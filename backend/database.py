from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/qualcli')

try:
    # Create database engine
    engine = create_engine(DATABASE_URL)
    logger.info(f"Connecting to database at {DATABASE_URL}")
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def init_db():
        """Initialize database tables."""
        from .models.job import Job  # Import here to avoid circular imports
        from .models.device import Device  # Import Device model
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

    def get_db():
        """Get database session."""
        db = SessionLocal()
        try:
            return db
        finally:
            db.close()

except Exception as e:
    logger.error(f"Error connecting to database: {str(e)}")
    raise 