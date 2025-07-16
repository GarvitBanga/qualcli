from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from ..database import Base

class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    device_id = Column(String, unique=True, nullable=False)  # e.g., "emulator-1", "device-2"
    device_type = Column(String, nullable=False)  # emulator, device, browserstack
    status = Column(String, nullable=False)  # available, busy, offline, maintenance
    max_concurrent_jobs = Column(Integer, default=1)  # How many jobs can run simultaneously
    current_jobs = Column(Integer, default=0)  # Currently running jobs
    location = Column(String, nullable=True)  # Optional: datacenter, region, etc.
    capabilities = Column(String, nullable=True)  # JSON string of device capabilities
    last_health_check = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_available(self):
        """Check if device can accept more jobs"""
        return (self.status == "available" and 
                self.current_jobs < self.max_concurrent_jobs)
    
    @property
    def utilization_percent(self):
        """Calculate current utilization percentage"""
        if self.max_concurrent_jobs == 0:
            return 0
        return (self.current_jobs / self.max_concurrent_jobs) * 100
    
    def can_handle_job(self, target_type: str) -> bool:
        """Check if this device can handle a specific target type"""
        return self.device_type == target_type and self.is_available
    
    def allocate_job(self):
        """Allocate a job to this device"""
        if not self.is_available:
            raise ValueError(f"Device {self.device_id} is not available for job allocation")
        self.current_jobs += 1
        if self.current_jobs >= self.max_concurrent_jobs:
            self.status = "busy"
        self.updated_at = datetime.utcnow()
    
    def release_job(self):
        """Release a job from this device"""
        if self.current_jobs > 0:
            self.current_jobs -= 1
        if self.current_jobs < self.max_concurrent_jobs and self.status == "busy":
            self.status = "available"
        self.updated_at = datetime.utcnow() 