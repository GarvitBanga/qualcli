from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    org_id = Column(String, nullable=False)
    app_version_id = Column(String, nullable=False)
    test_path = Column(String, nullable=False)
    priority = Column(Integer, default=1)
    target = Column(String, nullable=False)  # emulator, device, browserstack
    status = Column(String, nullable=False)  # queued, running, completed, failed
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=True)  # Assigned device
    assigned_device_name = Column(String, nullable=True)  # For tracking device name
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to device
    device = relationship("Device", backref="jobs") 