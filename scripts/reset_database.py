#!/usr/bin/env python3
"""
Reset database by dropping and recreating all tables.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine, Base
from backend.models.job import Job
from backend.models.device import Device
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Drop and recreate all database tables."""
    try:
        logger.info("Resetting database...")
        
        # Drop all tables
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")
        
        # Recreate all tables
        logger.info("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("QualCLI Database Reset")
    logger.info("=====================")
    
    if reset_database():
        logger.info("✅ Database reset successful!")
    else:
        logger.error("❌ Database reset failed!")
        sys.exit(1) 