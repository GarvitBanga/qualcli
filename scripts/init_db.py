from backend.database import init_db
from backend.models.job import Base, Job
from backend.database import engine

def main():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    main() 