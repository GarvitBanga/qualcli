#!/usr/bin/env python3
"""
Initialize device pool with simulated devices for testing.
This script sets up a realistic device pool for the QualCLI system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, init_db
from backend.models.device import Device
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_device_pool():
    """Create a realistic device pool for testing."""
    db = SessionLocal()
    
    try:
        # Initialize database tables first
        init_db()
        
        # Clear existing devices
        db.query(Device).delete()
        db.commit()
        logger.info("Cleared existing devices")
        
        # Device pool configuration
        device_configs = [
            # Emulator devices (fast, good for rapid testing)
            {"device_id": "emulator-1", "device_type": "emulator", "max_concurrent_jobs": 2, "location": "Local"},
            {"device_id": "emulator-2", "device_type": "emulator", "max_concurrent_jobs": 2, "location": "Local"},
            {"device_id": "emulator-3", "device_type": "emulator", "max_concurrent_jobs": 1, "location": "Local"},
            
            # Physical device pool (more realistic testing)
            {"device_id": "device-pixel-1", "device_type": "device", "max_concurrent_jobs": 1, "location": "Lab-A"},
            {"device_id": "device-samsung-1", "device_type": "device", "max_concurrent_jobs": 1, "location": "Lab-A"},
            {"device_id": "device-oneplus-1", "device_type": "device", "max_concurrent_jobs": 1, "location": "Lab-B"},
            
            # BrowserStack cloud devices (high capacity)
            {"device_id": "browserstack-1", "device_type": "browserstack", "max_concurrent_jobs": 5, "location": "US-East"},
            {"device_id": "browserstack-2", "device_type": "browserstack", "max_concurrent_jobs": 5, "location": "EU-West"},
            {"device_id": "browserstack-3", "device_type": "browserstack", "max_concurrent_jobs": 3, "location": "Asia-Pacific"},
        ]
        
        # Create devices
        created_devices = []
        for config in device_configs:
            device = Device(
                device_id=config["device_id"],
                device_type=config["device_type"],
                status="available",
                max_concurrent_jobs=config["max_concurrent_jobs"],
                current_jobs=0,
                location=config["location"],
                capabilities='{"android": true, "api_level": 29}',  # Mock capabilities
            )
            db.add(device)
            created_devices.append(device)
        
        # Commit all devices
        db.commit()
        
        # Log summary
        logger.info(f"Successfully created {len(created_devices)} devices:")
        
        for device_type in ["emulator", "device", "browserstack"]:
            devices_of_type = [d for d in created_devices if d.device_type == device_type]
            total_capacity = sum(d.max_concurrent_jobs for d in devices_of_type)
            logger.info(f"  {device_type.capitalize()}: {len(devices_of_type)} devices, {total_capacity} total capacity")
        
        logger.info("\nDevice Pool Summary:")
        logger.info("==================")
        
        for device in created_devices:
            logger.info(f"  {device.device_id} ({device.device_type}) - "
                       f"Capacity: {device.max_concurrent_jobs} jobs - "
                       f"Location: {device.location}")
        
        total_devices = len(created_devices)
        total_capacity = sum(d.max_concurrent_jobs for d in created_devices)
        
        logger.info(f"\nTotal: {total_devices} devices with {total_capacity} job capacity")
        logger.info("Device pool initialization complete!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating device pool: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_device_pool():
    """Verify the device pool was created correctly."""
    db = SessionLocal()
    try:
        devices = db.query(Device).all()
        logger.info(f"\nVerification: Found {len(devices)} devices in database")
        
        # Group by type
        by_type = {}
        for device in devices:
            if device.device_type not in by_type:
                by_type[device.device_type] = []
            by_type[device.device_type].append(device)
        
        for device_type, device_list in by_type.items():
            total_capacity = sum(d.max_concurrent_jobs for d in device_list)
            logger.info(f"  {device_type}: {len(device_list)} devices, {total_capacity} capacity")
            
        return len(devices) > 0
        
    except Exception as e:
        logger.error(f"Error verifying device pool: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("QualCLI Device Pool Initialization")
    logger.info("=================================")
    
    # Create device pool
    if create_device_pool():
        # Verify creation
        if verify_device_pool():
            logger.info("\n✅ Device pool initialization successful!")
            print("\nTo view device status:")
            print("  curl http://localhost:8002/devices")
            print("  curl http://localhost:8002/devices/status")
        else:
            logger.error("❌ Device pool verification failed")
            sys.exit(1)
    else:
        logger.error("❌ Device pool initialization failed")
        sys.exit(1) 