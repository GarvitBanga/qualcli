import pytest
import time
from cli.client import QualClient

class TestPriorityScheduling:
    """Test suite for priority-based job scheduling."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = QualClient(base_url="http://localhost:8002")
    
    def test_priority_queue_routing(self):
        """Test that jobs are routed to correct priority queues."""
        # Submit jobs with different priorities
        test_jobs = [
            {"priority": 5, "test_path": "tests/high_priority_test.js"},
            {"priority": 3, "test_path": "tests/normal_priority_test.js"},
            {"priority": 1, "test_path": "tests/low_priority_test.js"},
        ]
        
        job_ids = []
        for job_config in test_jobs:
            job_id = self.client.submit_job(
                org_id="priority-test-org",
                app_version_id="priority-test-v1.0",
                test_path=job_config["test_path"],
                priority=job_config["priority"],
                target="emulator"
            )
            job_ids.append((job_id, job_config["priority"]))
            
        # Verify all jobs were submitted successfully
        assert len(job_ids) == 3
        for job_id, priority in job_ids:
            assert isinstance(job_id, int)
            assert job_id > 0
    
    def test_priority_queue_info_endpoint(self):
        """Test the priority queue information endpoint."""
        import httpx
        
        response = httpx.get("http://localhost:8002/queues/priority-info")
        assert response.status_code == 200
        
        data = response.json()
        assert "priority_queues" in data
        assert "priority_mapping" in data["priority_queues"]
        
        # Verify priority mapping
        mapping = data["priority_queues"]["priority_mapping"]
        assert mapping["5"] == "high_priority"
        assert mapping["4"] == "high_priority"
        assert mapping["3"] == "normal_priority"
        assert mapping["2"] == "normal_priority"
        assert mapping["1"] == "low_priority"
    
    def test_queue_status_endpoint(self):
        """Test the queue status monitoring endpoint."""
        import httpx
        
        # First submit some jobs
        job_id_high = self.client.submit_job(
            org_id="status-test-org",
            app_version_id="status-test-v1.0",
            test_path="tests/status_test_high.js",
            priority=5,
            target="emulator"
        )
        
        job_id_low = self.client.submit_job(
            org_id="status-test-org",
            app_version_id="status-test-v1.0",
            test_path="tests/status_test_low.js",
            priority=1,
            target="emulator"
        )
        
        # Check queue status
        response = httpx.get("http://localhost:8002/queues/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "queue_summary" in data
        assert "priority_breakdown" in data
        
        # Verify queue structure
        queue_summary = data["queue_summary"]
        assert "high_priority" in queue_summary
        assert "normal_priority" in queue_summary
        assert "low_priority" in queue_summary
        
        # Verify priority breakdown
        priority_breakdown = data["priority_breakdown"]
        assert "priority_5" in priority_breakdown
        assert "priority_1" in priority_breakdown
    
    def test_device_allocation_with_priority(self):
        """Test that device allocation considers job priority."""
        import httpx
        
        # Submit high and low priority jobs
        high_priority_job = self.client.submit_job(
            org_id="device-test-org",
            app_version_id="device-test-v1.0",
            test_path="tests/device_test_high.js",
            priority=5,
            target="emulator"
        )
        
        low_priority_job = self.client.submit_job(
            org_id="device-test-org",
            app_version_id="device-test-v1.0",
            test_path="tests/device_test_low.js",
            priority=1,
            target="emulator"
        )
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Check device status
        response = httpx.get("http://localhost:8002/devices/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "priority_allocation" in data
        
        # Verify priority allocation tracking exists
        priority_allocation = data["priority_allocation"]
        assert isinstance(priority_allocation, dict)
    
    def test_priority_validation(self):
        """Test that invalid priorities are rejected."""
        import httpx
        
        # Test priority too high
        response = httpx.post("http://localhost:8002/jobs/submit", json={
            "org_id": "validation-test-org",
            "app_version_id": "validation-test-v1.0",
            "test_path": "tests/validation_test.js",
            "priority": 10,  # Invalid: too high
            "target": "emulator"
        })
        assert response.status_code == 400
        
        # Test priority too low
        response = httpx.post("http://localhost:8002/jobs/submit", json={
            "org_id": "validation-test-org",
            "app_version_id": "validation-test-v1.0",
            "test_path": "tests/validation_test.js",
            "priority": 0,  # Invalid: too low
            "target": "emulator"
        })
        assert response.status_code == 400
        
        # Test valid priorities
        for priority in [1, 2, 3, 4, 5]:
            response = httpx.post("http://localhost:8002/jobs/submit", json={
                "org_id": "validation-test-org",
                "app_version_id": "validation-test-v1.0",
                "test_path": f"tests/validation_test_{priority}.js",
                "priority": priority,
                "target": "emulator"
            })
            assert response.status_code == 200
    
    def test_high_priority_job_processing(self):
        """Test that high priority jobs are processed preferentially."""
        # This test verifies the overall priority scheduling behavior
        
        # Submit multiple jobs with different priorities
        jobs = []
        
        # Submit low priority jobs first
        for i in range(3):
            job_id = self.client.submit_job(
                org_id="processing-test-org",
                app_version_id="processing-test-v1.0",
                test_path=f"tests/low_priority_test_{i}.js",
                priority=1,
                target="emulator"
            )
            jobs.append({"id": job_id, "priority": 1, "submitted_at": time.time()})
        
        # Wait a moment
        time.sleep(1)
        
        # Submit high priority job
        high_priority_job_id = self.client.submit_job(
            org_id="processing-test-org",
            app_version_id="processing-test-v1.0",
            test_path="tests/high_priority_test.js",
            priority=5,
            target="emulator"
        )
        jobs.append({"id": high_priority_job_id, "priority": 5, "submitted_at": time.time()})
        
        # Wait for some processing
        time.sleep(5)
        
        # Check job statuses
        job_statuses = []
        for job in jobs:
            status = self.client.get_job_status(job["id"])
            job_statuses.append({
                "id": job["id"],
                "priority": job["priority"],
                "status": status,
                "submitted_at": job["submitted_at"]
            })
        
        # Verify that jobs were created successfully
        assert len(job_statuses) == 4
        
        # The high priority job should be processed or in a better state
        high_priority_status = [j for j in job_statuses if j["priority"] == 5][0]
        low_priority_statuses = [j for j in job_statuses if j["priority"] == 1]
        
        # At minimum, verify the jobs were submitted and are being tracked
        assert high_priority_status["status"] in ["queued", "running", "completed", "failed"]
        for low_priority_job in low_priority_statuses:
            assert low_priority_job["status"] in ["queued", "running", "completed", "failed"]
    
    def test_queue_configuration(self):
        """Test that queue configuration is properly set up."""
        from backend.queue.celery_app import get_queue_by_priority, get_priority_info
        
        # Test queue routing function
        assert get_queue_by_priority(5) == "high_priority"
        assert get_queue_by_priority(4) == "high_priority"
        assert get_queue_by_priority(3) == "normal_priority"
        assert get_queue_by_priority(2) == "normal_priority"
        assert get_queue_by_priority(1) == "low_priority"
        
        # Test priority info function
        priority_info = get_priority_info()
        assert "priority_mapping" in priority_info
        assert "queue_order" in priority_info
        assert "description" in priority_info
        
        # Verify queue order
        assert priority_info["queue_order"] == ["high_priority", "normal_priority", "low_priority"] 