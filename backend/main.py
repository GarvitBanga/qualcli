from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import logging
import sys
import json

from .database import get_db, init_db
from .models.job import Job
from .models.device import Device
from .services.device_manager import DeviceManager
from .queue.tasks import process_test_job
from .queue.celery_app import get_queue_by_priority, get_priority_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="QualGent Job Server")

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and monitoring."""
    return {"status": "healthy", "service": "qualcli-backend"}

class TestJob(BaseModel):
    org_id: str
    app_version_id: str
    test_path: str
    priority: int = 1
    target: str = "emulator"  # One of: emulator, device, browserstack

class JobResponse(BaseModel):
    job_id: int
    status: str
    created_at: datetime

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()

@app.post("/jobs/submit", response_model=JobResponse)
async def submit_job(job: TestJob, db: Session = Depends(get_db)):
    """Submit a new job with priority-based routing."""
    try:
        logger.info(f"Received job submission request: {json.dumps(job.dict())}")
        
        # Validate priority
        if not 1 <= job.priority <= 5:
            raise HTTPException(status_code=400, detail="Priority must be between 1 and 5")
        
        db_job = Job(
            org_id=job.org_id,
            app_version_id=job.app_version_id,
            test_path=job.test_path,
            priority=job.priority,
            target=job.target,
            status="queued"
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        logger.info(f"Created job {db_job.id} in database with priority {db_job.priority}, status {db_job.status}")
        
        # Route job to appropriate priority queue
        queue_name = get_queue_by_priority(job.priority)
        logger.info(f"Routing job {db_job.id} (priority {job.priority}) to queue: {queue_name}")
        
        # Queue the job for processing with priority routing
        try:
            task = process_test_job.apply_async(
                args=[db_job.id],
                queue=queue_name,
                priority=job.priority,  # Set task priority within the queue
                retry=True,
                retry_policy={
                    'max_retries': 3,
                    'interval_start': 0,
                    'interval_step': 0.2,
                    'interval_max': 0.2,
                }
            )
            logger.info(f"Queued job {db_job.id} with task ID {task.id} in {queue_name} queue")
            logger.info(f"Task details: queue={queue_name}, priority={job.priority}")
        except Exception as e:
            logger.error(f"Error queueing task: {str(e)}")
            db_job.status = "failed"
            db.commit()
            raise
        
        return JobResponse(
            job_id=db_job.id,
            status=db_job.status,
            created_at=db_job.created_at
        )
    except Exception as e:
        logger.error(f"Error submitting job: {str(e)}")
        raise

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Get the status of a job."""
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        job_id=db_job.id,
        status=db_job.status,
        created_at=db_job.created_at
    )

@app.get("/jobs/group/{app_version_id}")
async def get_grouped_jobs(app_version_id: str, db: Session = Depends(get_db)):
    """Get all jobs for a specific app version."""
    jobs = db.query(Job).filter(Job.app_version_id == app_version_id).all()
    return [
        {
            "job_id": job.id,
            "status": job.status,
            "created_at": job.created_at
        }
        for job in jobs
    ]

@app.get("/batches/summary")
async def get_batch_summary(db: Session = Depends(get_db)):
    """Get batch processing summary showing grouping efficiency."""
    # Group jobs by app_version_id and target
    from sqlalchemy import func
    
    batch_data = db.query(
        Job.app_version_id,
        Job.target,
        Job.status,
        func.count(Job.id).label('job_count'),
        func.min(Job.created_at).label('first_job'),
        func.max(Job.created_at).label('last_job')
    ).group_by(
        Job.app_version_id, 
        Job.target, 
        Job.status
    ).all()
    
    batches = {}
    for row in batch_data:
        batch_key = f"{row.app_version_id}_{row.target}"
        if batch_key not in batches:
            batches[batch_key] = {
                "app_version_id": row.app_version_id,
                "target": row.target,
                "total_jobs": 0,
                "status_breakdown": {},
                "first_job": row.first_job,
                "last_job": row.last_job
            }
        
        batches[batch_key]["total_jobs"] += row.job_count
        batches[batch_key]["status_breakdown"][row.status] = row.job_count
        
        # Update time range
        if row.first_job < batches[batch_key]["first_job"]:
            batches[batch_key]["first_job"] = row.first_job
        if row.last_job > batches[batch_key]["last_job"]:
            batches[batch_key]["last_job"] = row.last_job
    
    # Calculate efficiency metrics
    total_batches = len(batches)
    total_jobs = sum(batch["total_jobs"] for batch in batches.values())
    potential_time_saved = sum(
        max(0, batch["total_jobs"] - 1) * {
            'emulator': 5, 'device': 10, 'browserstack': 15
        }.get(batch["target"], 5)
        for batch in batches.values()
    )
    
    return {
        "summary": {
            "total_batches": total_batches,
            "total_jobs": total_jobs,
            "average_batch_size": round(total_jobs / total_batches, 2) if total_batches > 0 else 0,
            "potential_time_saved_seconds": potential_time_saved
        },
        "batches": list(batches.values())
    }

# Device Management Endpoints

@app.get("/devices")
async def list_devices(db: Session = Depends(get_db)):
    """Get all devices and their current status."""
    devices = db.query(Device).all()
    return {
        "devices": [
            {
                "id": device.id,
                "device_id": device.device_id,
                "device_type": device.device_type,
                "status": device.status,
                "current_jobs": device.current_jobs,
                "max_concurrent_jobs": device.max_concurrent_jobs,
                "utilization_percent": device.utilization_percent,
                "location": device.location,
                "last_health_check": device.last_health_check
            }
            for device in devices
        ]
    }

@app.get("/devices/status")
async def get_device_pool_status(db: Session = Depends(get_db)):
    """Get device pool status and utilization metrics."""
    device_manager = DeviceManager(db)
    return device_manager.get_device_status()

@app.get("/devices/recommendations/{target_type}")
async def get_device_recommendations(target_type: str, db: Session = Depends(get_db)):
    """Get device allocation recommendations for a specific target type."""
    device_manager = DeviceManager(db)
    return device_manager.get_device_recommendations(target_type)

@app.post("/devices/health-check")
async def perform_health_check(db: Session = Depends(get_db)):
    """Perform health check on all devices."""
    device_manager = DeviceManager(db)
    return device_manager.health_check_devices()

class DeviceCreate(BaseModel):
    device_id: str
    device_type: str
    max_concurrent_jobs: int = 1
    location: str = None

@app.post("/devices")
async def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    """Create a new device in the pool."""
    # Check if device_id already exists
    existing_device = db.query(Device).filter(Device.device_id == device.device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Device ID already exists")
    
    db_device = Device(
        device_id=device.device_id,
        device_type=device.device_type,
        status="available",
        max_concurrent_jobs=device.max_concurrent_jobs,
        location=device.location
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    return {
        "device_id": db_device.device_id,
        "status": db_device.status,
        "created_at": db_device.created_at
    }

@app.delete("/devices/{device_id}")
async def remove_device(device_id: str, db: Session = Depends(get_db)):
    """Remove a device from the pool."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.current_jobs > 0:
        raise HTTPException(status_code=400, detail="Cannot remove device with running jobs")
    
    db.delete(device)
    db.commit()
    return {"message": f"Device {device_id} removed successfully"} 

@app.get("/queues/priority-info")
async def get_priority_queue_info():
    """Get information about priority queue configuration."""
    try:
        priority_info = get_priority_info()
        return {
            "priority_queues": priority_info,
            "status": "active",
            "description": "Priority-based job routing configuration"
        }
    except Exception as e:
        logger.error(f"Error getting priority info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/queues/status")
async def get_queue_status(db: Session = Depends(get_db)):
    """Get current queue status by priority level."""
    try:
        # Count jobs by priority and status
        priority_stats = {}
        
        for priority in range(1, 6):
            queue_name = get_queue_by_priority(priority)
            queued_count = db.query(Job).filter(
                Job.priority == priority, 
                Job.status == "queued"
            ).count()
            running_count = db.query(Job).filter(
                Job.priority == priority, 
                Job.status == "running"
            ).count()
            
            priority_stats[f"priority_{priority}"] = {
                "queue_name": queue_name,
                "queued_jobs": queued_count,
                "running_jobs": running_count,
                "total_active": queued_count + running_count
            }
        
        # Group by queue
        queue_summary = {}
        for queue in ['high_priority', 'normal_priority', 'low_priority']:
            total_queued = sum(
                stats["queued_jobs"] for stats in priority_stats.values() 
                if stats["queue_name"] == queue
            )
            total_running = sum(
                stats["running_jobs"] for stats in priority_stats.values() 
                if stats["queue_name"] == queue
            )
            queue_summary[queue] = {
                "queued_jobs": total_queued,
                "running_jobs": total_running,
                "total_active": total_queued + total_running
            }
        
        return {
            "queue_summary": queue_summary,
            "priority_breakdown": priority_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: int, db: Session = Depends(get_db)):
    """Cancel a queued or running job."""
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel job with status: {job.status}")
        
        # Mark job as failed (cancelled)
        original_status = job.status
        job.status = "failed"
        db.commit()
        
        logger.info(f"Job {job_id} cancelled (was {original_status})")
        
        return {
            "job_id": job_id,
            "message": f"Job cancelled successfully (was {original_status})",
            "previous_status": original_status,
            "new_status": "failed"
        }
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {str(e)}")
        raise

@app.get("/jobs")
async def list_jobs(
    app_version_id: str = None,
    status: str = None,
    priority: int = None,
    target: str = None,
    org_id: str = None,
    limit: int = 50,
    sort: str = "created",
    order: str = "desc",
    db: Session = Depends(get_db)
):
    """List jobs with optional filtering and sorting."""
    try:
        query = db.query(Job)
        
        # Apply filters
        if app_version_id:
            query = query.filter(Job.app_version_id == app_version_id)
        if status:
            # Support comma-separated status values
            if ',' in status:
                status_list = [s.strip() for s in status.split(',')]
                query = query.filter(Job.status.in_(status_list))
            else:
                query = query.filter(Job.status == status)
        if priority:
            query = query.filter(Job.priority == priority)
        if target:
            query = query.filter(Job.target == target)
        if org_id:
            query = query.filter(Job.org_id == org_id)
        
        # Apply sorting
        if sort == "priority":
            if order == "desc":
                query = query.order_by(Job.priority.desc())
            else:
                query = query.order_by(Job.priority.asc())
        elif sort == "status":
            if order == "desc":
                query = query.order_by(Job.status.desc())
            else:
                query = query.order_by(Job.status.asc())
        else:  # default to created
            if order == "desc":
                query = query.order_by(Job.created_at.desc())
            else:
                query = query.order_by(Job.created_at.asc())
        
        # Apply limit
        query = query.limit(limit)
        
        jobs = query.all()
        
        return [
            {
                "id": job.id,
                "org_id": job.org_id,
                "app_version_id": job.app_version_id,
                "test_path": job.test_path,
                "priority": job.priority,
                "target": job.target,
                "status": job.status,
                "device_id": job.device_id,
                "assigned_device_name": job.assigned_device_name,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None
            }
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 