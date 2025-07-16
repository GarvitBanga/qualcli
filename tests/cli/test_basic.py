import pytest
from cli.client import QualClient

def test_job_submission_and_status():
    # Initialize client
    client = QualClient(base_url="http://localhost:8002")
    
    # Submit a test job
    job_id = client.submit_job(
        org_id="test-org",
        app_version_id="test-version",
        test_path="tests/dummy_test.js",  # This file doesn't need to exist for this test
        priority=1,
        target="local"
    )
    
    # Verify job_id is returned and is a positive integer
    assert isinstance(job_id, int)
    assert job_id > 0
    
    # Get job status
    status = client.get_job_status(job_id)
    
    # Verify status is a valid status string
    assert status in ["queued", "running", "completed", "failed"]
    
    # Get all jobs for the app version
    jobs = client.get_jobs_by_app_version("test-version")
    
    # Verify jobs is a list
    assert isinstance(jobs, list)
    
    # Verify our job is in the list
    assert any(job["job_id"] == job_id for job in jobs) 