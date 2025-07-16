from .celery_app import celery_app
from ..models.job import Job
from ..models.device import Device
from ..database import SessionLocal
from ..services.test_runner import TestRunner
from ..services.device_manager import DeviceManager
from typing import Dict, Any, List
import logging
import sys
import json
import asyncio
from sqlalchemy import and_

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('celery_tasks.log')
    ]
)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='backend.queue.tasks.process_test_job')
def process_test_job(self, job_id: int) -> Dict[str, Any]:
    """
    Process a test job with batching logic.
    
    This task:
    1. Loads job details from database
    2. Groups jobs by app_version_id and target
    3. Claims all related queued jobs to process as a batch
    4. Simulates app installation once per batch
    5. Executes all tests in the batch
    6. Updates individual job statuses
    """
    db = None
    job = None
    batch_jobs = []
    
    try:
        logger.info(f"Starting to process job {job_id}")
        logger.info(f"Task ID: {self.request.id}")
        
        # Get database session
        db = SessionLocal()
        logger.info(f"Connected to database for job {job_id}")
        
        # Get job details
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            error_msg = f"Job {job_id} not found"
            logger.error(error_msg)
            return {
                "job_id": job_id,
                "status": "failed",
                "error": error_msg
            }

        logger.info(f"Found job {job_id} in database with status {job.status}")
        
        # Check if job is already being processed
        if job.status != "queued":
            logger.info(f"Job {job_id} already processed with status {job.status}")
            return {
                "job_id": job_id,
                "status": job.status,
                "message": "Job already processed"
            }

        # DEVICE ALLOCATION: First try to allocate a device for this target type
        device_manager = DeviceManager(db)
        allocated_device = device_manager.allocate_device(job.target, job.priority)
        
        if not allocated_device:
            error_msg = f"No available devices for target type {job.target}"
            logger.error(error_msg)
            job.status = "failed"
            db.commit()
            return {
                "job_id": job_id,
                "status": "failed",
                "error": error_msg
            }
        
        logger.info(f"Allocated device {allocated_device.device_id} for job {job_id}")

        # BATCH COORDINATION: Claim all related queued jobs atomically for the same device type
        related_jobs = db.query(Job).filter(
            and_(
                Job.app_version_id == job.app_version_id,
                Job.target == job.target,  # Same target for device efficiency
                Job.status == "queued"
            )
        ).all()
        
        # Update all related jobs to "running" and assign to the same device
        batch_job_ids = []
        for related_job in related_jobs:
            related_job.status = "running"
            related_job.device_id = allocated_device.id
            related_job.assigned_device_name = allocated_device.device_id
            batch_job_ids.append(related_job.id)
            batch_jobs.append(related_job)
        
        db.commit()
        logger.info(f"Claimed batch of {len(batch_jobs)} jobs: {batch_job_ids}")
        logger.info(f"Batch details: app_version_id={job.app_version_id}, target={job.target}, device={allocated_device.device_id}")

        # BATCH PROCESSING: Initialize test runner for the batch
        runner = TestRunner(target=job.target)
        
        # Simulate app installation (once per batch)
        logger.info(f"Installing app {job.app_version_id} on {job.target} for batch")
        installation_time = await_app_installation(job.target)
        logger.info(f"App installation completed in {installation_time}s")
        
        # Process all jobs in the batch
        batch_results = []
        successful_jobs = 0
        failed_jobs = 0
        
        for batch_job in batch_jobs:
            try:
                logger.info(f"Processing job {batch_job.id}: {batch_job.test_path}")
                
                # Run the test using asyncio
                loop = asyncio.get_event_loop()
                test_result = loop.run_until_complete(
                    runner.run_tests(batch_job.test_path, batch_job.app_version_id)
                )
                
                if test_result["success"]:
                    batch_job.status = "completed"
                    successful_jobs += 1
                    result = {
                        "job_id": batch_job.id,
                        "status": "completed",
                        "result": test_result["results"]
                    }
                else:
                    batch_job.status = "failed"
                    failed_jobs += 1
                    result = {
                        "job_id": batch_job.id,
                        "status": "failed",
                        "error": test_result["error"]
                    }
                
                batch_results.append(result)
                logger.info(f"Job {batch_job.id} completed with status: {batch_job.status}")
                
            except Exception as e:
                error_msg = f"Error processing job {batch_job.id}: {str(e)}"
                logger.error(error_msg)
                batch_job.status = "failed"
                failed_jobs += 1
                batch_results.append({
                    "job_id": batch_job.id,
                    "status": "failed",
                    "error": error_msg
                })
        
        # Commit all job status updates
        db.commit()
        
        # DEVICE CLEANUP: Release the allocated device
        device_manager.release_device(allocated_device.id)
        logger.info(f"Released device {allocated_device.device_id} after batch completion")
        
        # Log batch summary
        total_time = installation_time + sum([r.get("result", {}).get("execution_time", 0) for r in batch_results if r["status"] == "completed"])
        logger.info(f"Batch processing completed:")
        logger.info(f"  - Total jobs: {len(batch_jobs)}")
        logger.info(f"  - Successful: {successful_jobs}")
        logger.info(f"  - Failed: {failed_jobs}")
        logger.info(f"  - Device: {allocated_device.device_id}")
        logger.info(f"  - Total time: {total_time}s")
        logger.info(f"  - Time saved: {(len(batch_jobs) - 1) * installation_time}s (avoided {len(batch_jobs) - 1} app installations)")
        
        # Return summary for the initiating job
        return {
            "job_id": job_id,
            "status": "completed" if job.status == "completed" else "failed",
            "device_id": allocated_device.device_id,
            "batch_summary": {
                "total_jobs": len(batch_jobs),
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "device_used": allocated_device.device_id,
                "time_saved_seconds": (len(batch_jobs) - 1) * installation_time,
                "batch_results": batch_results
            }
        }
        
    except Exception as e:
        error_msg = f"Error processing batch for job {job_id}: {str(e)}"
        logger.error(error_msg)
        
        # DEVICE CLEANUP: Release allocated device if it exists
        if 'allocated_device' in locals() and allocated_device and db:
            device_manager = DeviceManager(db)
            device_manager.release_device(allocated_device.id)
            logger.info(f"Released device {allocated_device.device_id} due to batch error")
        
        # Mark all claimed jobs as failed
        if batch_jobs and db:
            for batch_job in batch_jobs:
                if batch_job.status == "running":
                    batch_job.status = "failed"
            db.commit()
            logger.info(f"Marked {len(batch_jobs)} jobs as failed due to batch error")
            
        return {
            "job_id": job_id,
            "status": "failed",
            "error": error_msg
        }
    finally:
        if db:
            db.close()
            logger.info(f"Closed database connection for job {job_id}")

def await_app_installation(target: str) -> int:
    """
    Simulate app installation time based on target.
    This represents the time saved by batching jobs.
    """
    installation_times = {
        'emulator': 5,      # 5 seconds for emulator
        'device': 10,       # 10 seconds for physical device  
        'browserstack': 15  # 15 seconds for BrowserStack
    }
    return installation_times.get(target, 5) 