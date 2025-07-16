# QualCli - Test Job Queue System

A CLI tool and backend service for queuing and deploying AppWright tests across devices, emulators, and BrowserStack with intelligent job batching and priority scheduling.

## Features

- **Priority-based job scheduling** (high/normal/low priority queues)
- **Intelligent job batching** by app version to minimize installations  
- **Multi-device support** (emulators, physical devices, BrowserStack)
- **CLI interface** for job management
- **GitHub Actions integration** for CI/CD

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis

### Installation

1. **Clone and setup:**
```bash
git clone https://github.com/GarvitBanga/qualcli.git
cd qualcli
python -m venv qualcli
source qualcli/bin/activate  # Windows: qualcli\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

2. **Start services:**
```bash
# Start PostgreSQL and Redis (using Docker)
docker-compose up postgres redis

# Initialize database
python scripts/init_db.py
python scripts/init_devices.py

# Start backend server (new terminal)
uvicorn backend.main:app --host 0.0.0.0 --port 8002

# Start worker (new terminal)
celery -A backend.queue.celery_app worker --loglevel=info
```

3. **Verify setup:**
```bash
qgjob devices list
qgjob queue status
```

## CLI Commands

### Submit Jobs

```bash
# Basic job submission
qgjob submit --org-id=qualgent --app-version-id=xyz123 --test=tests/onboarding.spec.js

# High priority job
qgjob submit --org-id=qualgent --app-version-id=abc456 --test=tests/critical.spec.js --priority=5 --target=device

# Low priority background job
qgjob submit --org-id=qualgent --app-version-id=def789 --test=tests/regression.spec.js --priority=1 --target=emulator
```

### Check Status

```bash
# Check specific job
qgjob status job --job-id=123

# List recent jobs
qgjob jobs recent --limit=10

# List jobs with filters
qgjob jobs list --status-filter=running --priority=4 --target=emulator
```

### Monitor System

```bash
# View queue status
qgjob queue status

# List available devices
qgjob devices list

# Monitor real-time activity
qgjob queue monitor --watch

# View active jobs
qgjob jobs active --watch
```

## Demo Workflow

Here's a complete example showing the system in action:

```bash
# 1. Submit multiple jobs with same app version (will be batched together)
qgjob submit --org-id=demo --app-version-id=v2.1.0 --test=tests/login.spec.js --priority=3 --target=emulator
qgjob submit --org-id=demo --app-version-id=v2.1.0 --test=tests/signup.spec.js --priority=3 --target=emulator
qgjob submit --org-id=demo --app-version-id=v2.1.0 --test=tests/checkout.spec.js --priority=4 --target=emulator

# 2. Monitor progress
qgjob queue monitor --watch

# 3. Check results
qgjob jobs list --app-version-id=v2.1.0
```

## How It Works

### Job Batching
- Jobs with the same `app_version_id` and `target` are automatically batched
- App is installed once per batch, then all tests run sequentially
- Saves time by avoiding redundant app installations

### Priority Scheduling
- **Priority 5 (Critical)**: Immediate processing, can preempt lower-priority jobs
- **Priority 4 (High)**: Fast-track processing
- **Priority 3 (Normal)**: Standard processing
- **Priority 2 (Normal)**: Standard processing  
- **Priority 1 (Low)**: Background processing when system is idle

### Device Management
- Smart device allocation based on priority and load
- Device utilization tracking and optimization
- Support for emulators, physical devices, and BrowserStack

## GitHub Actions Integration

Example workflow (`.github/workflows/appwright-test.yml`):

```yaml
name: AppWright Tests
on: [push]
jobs:
  run-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Tests
        run: |
          pip install qgjob
          qgjob submit --org-id=qualgent --app-version-id=${{ github.sha }} --test=tests/onboarding.spec.js --priority=4
```

## Configuration

Set these environment variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/qualcli

# API
API_URL=http://localhost:8002

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## API Documentation

Interactive API docs available at: `http://localhost:8002/docs`

Key endpoints:
- `POST /jobs/submit` - Submit new test job
- `GET /jobs/{job_id}` - Get job status  
- `GET /jobs` - List jobs with filtering
- `GET /devices` - List available devices
- `GET /queues/status` - Get queue status

## Testing

```bash
# Run CLI tests
pytest tests/cli/ -v

# Run with coverage
pytest --cov=backend --cov=cli tests/
```

## Architecture

The system consists of:

- **CLI Tool** (`qgjob`) - Command-line interface for job management
- **FastAPI Backend** - REST API for job orchestration  
- **Celery Workers** - Distributed job processing
- **PostgreSQL** - Job and device data persistence
- **Redis** - Job queue management
- **Device Manager** - Smart device allocation and load balancing

## License

MIT License - see [LICENSE](LICENSE) file for details. 