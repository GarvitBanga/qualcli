from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from ..models.device import Device
from ..models.job import Job
import logging
import json

logger = logging.getLogger(__name__)

class DeviceManager:
    """
    Manages device allocation and status for test execution.
    Handles device pools, load balancing, and priority-based allocation strategies.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def allocate_device(self, target_type: str, priority: int = 1) -> Optional[Device]:
        """
        Allocate an available device for the given target type with priority consideration.
        
        Args:
            target_type: Type of device needed (emulator, device, browserstack)
            priority: Job priority (1-5, higher priority gets better allocation)
            
        Returns:
            Device object if allocation successful, None if no devices available
        """
        try:
            # Find available devices of the requested type
            available_devices = self.db.query(Device).filter(
                and_(
                    Device.device_type == target_type,
                    Device.status == "available",
                    Device.current_jobs < Device.max_concurrent_jobs
                )
            ).all()
            
            if not available_devices:
                # For high priority jobs, check if we can preempt lower priority jobs
                if priority >= 4:
                    logger.info(f"No available devices for priority {priority} job, checking for preemption opportunities")
                    preempted_device = self._try_preempt_device(target_type, priority)
                    if preempted_device:
                        return preempted_device
                
                logger.warning(f"No available devices of type {target_type} for priority {priority}")
                return None
            
            # Select best device based on priority and allocation strategy
            selected_device = self._select_optimal_device(available_devices, priority)
            
            # Allocate the device
            selected_device.allocate_job()
            self.db.commit()
            
            logger.info(f"Allocated device {selected_device.device_id} for {target_type} job "
                       f"(priority: {priority}, utilization: {selected_device.utilization_percent}%)")
            return selected_device
            
        except Exception as e:
            logger.error(f"Error allocating device: {str(e)}")
            self.db.rollback()
            return None
    
    def _select_optimal_device(self, available_devices: List[Device], priority: int) -> Device:
        """
        Select the optimal device based on priority and allocation strategy.
        
        Args:
            available_devices: List of available devices
            priority: Job priority level
            
        Returns:
            Best device for the job
        """
        if priority >= 4:  # High priority jobs
            # Give high priority jobs the least loaded device (best performance)
            return min(available_devices, key=lambda d: d.current_jobs)
        elif priority >= 2:  # Normal priority jobs
            # Balance load across devices for normal priority
            return min(available_devices, key=lambda d: d.current_jobs)
        else:  # Low priority jobs
            # Use most loaded device (but still available) to preserve capacity
            return max(available_devices, key=lambda d: d.current_jobs)
    
    def _try_preempt_device(self, target_type: str, priority: int) -> Optional[Device]:
        """
        Try to preempt a device running lower priority jobs for a high priority job.
        
        Args:
            target_type: Type of device needed
            priority: Priority of the requesting job (must be >= 4 for preemption)
            
        Returns:
            Device if preemption successful, None otherwise
        """
        if priority < 4:
            return None
            
        try:
            # Find busy devices with lower priority jobs
            busy_devices = self.db.query(Device).filter(
                and_(
                    Device.device_type == target_type,
                    Device.status == "busy"
                )
            ).all()
            
            for device in busy_devices:
                # Check if this device has lower priority jobs we can preempt
                low_priority_jobs = self.db.query(Job).filter(
                    and_(
                        Job.device_id == device.id,
                        Job.status == "running",
                        Job.priority < priority - 1  # Only preempt if significantly lower priority
                    )
                ).all()
                
                if low_priority_jobs:
                    logger.info(f"Preempting {len(low_priority_jobs)} lower priority jobs on device {device.device_id}")
                    
                    # Mark preempted jobs as queued again (they'll be rescheduled)
                    for job in low_priority_jobs:
                        job.status = "queued"
                        job.device_id = None
                        job.assigned_device_name = None
                    
                    # Make device available for the high priority job
                    device.current_jobs = device.current_jobs - len(low_priority_jobs)
                    if device.current_jobs == 0:
                        device.status = "available"
                    
                    self.db.commit()
                    logger.info(f"Successfully preempted device {device.device_id} for high priority job")
                    return device
            
            return None
            
        except Exception as e:
            logger.error(f"Error during device preemption: {str(e)}")
            self.db.rollback()
            return None
    
    def release_device(self, device_id: int):
        """
        Release a device after job completion.
        
        Args:
            device_id: ID of the device to release
        """
        try:
            device = self.db.query(Device).filter(Device.id == device_id).first()
            if device:
                device.release_job()
                self.db.commit()
                logger.info(f"Released device {device.device_id} (utilization: {device.utilization_percent}%)")
            else:
                logger.warning(f"Device {device_id} not found for release")
        except Exception as e:
            logger.error(f"Error releasing device {device_id}: {str(e)}")
            self.db.rollback()
    
    def get_device_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all devices and their allocation state.
        
        Returns:
            Dictionary with device status information
        """
        try:
            devices = self.db.query(Device).all()
            
            status_summary = {
                'total_devices': len(devices),
                'available_devices': 0,
                'busy_devices': 0,
                'offline_devices': 0,
                'by_type': {},
                'priority_allocation': self._get_priority_allocation_stats(),
                'devices': []
            }
            
            # Group by device type
            for device in devices:
                if device.device_type not in status_summary['by_type']:
                    status_summary['by_type'][device.device_type] = {
                        'total': 0,
                        'available': 0,
                        'busy': 0,
                        'offline': 0,
                        'avg_utilization': 0
                    }
                
                type_stats = status_summary['by_type'][device.device_type]
                type_stats['total'] += 1
                
                if device.status == 'available':
                    status_summary['available_devices'] += 1
                    type_stats['available'] += 1
                elif device.status == 'busy':
                    status_summary['busy_devices'] += 1
                    type_stats['busy'] += 1
                else:
                    status_summary['offline_devices'] += 1
                    type_stats['offline'] += 1
                
                # Add device details
                status_summary['devices'].append({
                    'device_id': device.device_id,
                    'type': device.device_type,
                    'status': device.status,
                    'current_jobs': device.current_jobs,
                    'max_jobs': device.max_concurrent_jobs,
                    'utilization_percent': device.utilization_percent,
                    'is_available': device.is_available
                })
            
            # Calculate average utilization by type
            for device_type, stats in status_summary['by_type'].items():
                if stats['total'] > 0:
                    total_utilization = sum(
                        d['utilization_percent'] for d in status_summary['devices'] 
                        if d['type'] == device_type
                    )
                    stats['avg_utilization'] = total_utilization / stats['total']
            
            return status_summary
            
        except Exception as e:
            logger.error(f"Error getting device status: {str(e)}")
            return {'error': str(e)}
    
    def _get_priority_allocation_stats(self) -> Dict[str, Any]:
        """Get statistics about priority-based device allocation."""
        try:
            priority_stats = {}
            
            for priority in range(1, 6):
                running_jobs = self.db.query(Job).filter(
                    and_(Job.priority == priority, Job.status == "running")
                ).count()
                
                queued_jobs = self.db.query(Job).filter(
                    and_(Job.priority == priority, Job.status == "queued")
                ).count()
                
                # Get device types being used by this priority
                devices_in_use = self.db.query(Device.device_type, func.count(Job.id)).join(
                    Job, Device.id == Job.device_id
                ).filter(
                    and_(Job.priority == priority, Job.status == "running")
                ).group_by(Device.device_type).all()
                
                priority_stats[f"priority_{priority}"] = {
                    'running_jobs': running_jobs,
                    'queued_jobs': queued_jobs,
                    'devices_by_type': dict(devices_in_use)
                }
            
            return priority_stats
            
        except Exception as e:
            logger.error(f"Error getting priority allocation stats: {str(e)}")
            return {}
    
    def get_device_recommendations(self, target_type: str, priority: int = 1) -> Dict[str, Any]:
        """
        Get recommendations for device allocation based on current load and priority.
        
        Args:
            target_type: Type of device needed
            priority: Job priority level
            
        Returns:
            Dictionary with recommendations and estimated wait times
        """
        try:
            devices = self.db.query(Device).filter(Device.device_type == target_type).all()
            
            if not devices:
                return {
                    'recommendation': 'no_devices_available',
                    'message': f'No {target_type} devices configured',
                    'estimated_wait_time': None
                }
            
            available_devices = [d for d in devices if d.is_available]
            
            if available_devices:
                best_device = self._select_optimal_device(available_devices, priority)
                return {
                    'recommendation': 'immediate_allocation',
                    'device_id': best_device.device_id,
                    'current_utilization': best_device.utilization_percent,
                    'estimated_wait_time': 0,
                    'priority_advantage': priority >= 4
                }
            
            # Check preemption possibilities for high priority jobs
            if priority >= 4:
                preemption_possible = any(
                    self.db.query(Job).filter(
                        and_(
                            Job.device_id == device.id,
                            Job.status == "running", 
                            Job.priority < priority - 1
                        )
                    ).count() > 0
                    for device in devices if device.status == "busy"
                )
                
                if preemption_possible:
                    return {
                        'recommendation': 'preemption_available',
                        'message': f'High priority job can preempt lower priority jobs',
                        'estimated_wait_time': 5,  # Time to preempt
                        'priority_advantage': True
                    }
            
            # Calculate estimated wait time based on running jobs
            busy_devices = [d for d in devices if d.status == "busy"]
            if busy_devices:
                # Estimate based on priority of waiting jobs
                avg_job_time = 30  # Assume 30 seconds average job time
                min_wait = min(d.current_jobs for d in busy_devices) * avg_job_time
                
                # Adjust based on priority
                if priority >= 4:
                    min_wait = min_wait * 0.5  # High priority gets priority in queue
                elif priority == 1:
                    min_wait = min_wait * 1.5  # Low priority waits longer
                
                return {
                    'recommendation': 'queue_and_wait',
                    'message': f'All {target_type} devices busy',
                    'estimated_wait_time': int(min_wait),
                    'priority_advantage': priority >= 4
                }
            
            return {
                'recommendation': 'devices_offline',
                'message': f'All {target_type} devices offline',
                'estimated_wait_time': None,
                'priority_advantage': False
            }
            
        except Exception as e:
            logger.error(f"Error getting device recommendations: {str(e)}")
            return {'error': str(e)}
    
    def health_check_devices(self) -> Dict[str, Any]:
        """
        Perform health check on all devices and update their status.
        
        Returns:
            Dictionary with health check results
        """
        try:
            devices = self.db.query(Device).all()
            results = {
                'total_checked': len(devices),
                'healthy': 0,
                'unhealthy': 0,
                'details': []
            }
            
            for device in devices:
                # Simulate health check (in real system, this would ping the device)
                is_healthy = True  # Simulated check
                
                if is_healthy and device.status == "offline":
                    device.status = "available"
                    logger.info(f"Device {device.device_id} is back online")
                elif not is_healthy and device.status in ["available", "busy"]:
                    device.status = "offline"
                    logger.warning(f"Device {device.device_id} went offline")
                
                device.last_health_check = func.now()
                
                results['details'].append({
                    'device_id': device.device_id,
                    'status': device.status,
                    'healthy': is_healthy
                })
                
                if is_healthy:
                    results['healthy'] += 1
                else:
                    results['unhealthy'] += 1
            
            self.db.commit()
            return results
            
        except Exception as e:
            logger.error(f"Error during health check: {str(e)}")
            self.db.rollback()
            return {'error': str(e)} 