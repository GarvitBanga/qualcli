from backend.database import init_db, engine
from backend.models.job import Base  # Get Base from one of the models
from backend.models import Job, Device  # Import all models for foreign key resolution

def main():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    main() 