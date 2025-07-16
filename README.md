# QualGent Backend Coding Challenge

> **CLI tool and GitHub Actions integration to queue, group, and deploy AppWright tests across local devices, emulators, and BrowserStack.**

## 🎯 Challenge Overview

This project implements an internal test infrastructure for a QA automation platform powered by AppWright. Organizations can run end-to-end tests for various app versions across multiple device targets, with intelligent job batching to minimize install/setup overhead.

## 🏗️ Architecture

### System Components

```mermaid
graph TB
    %% User Interaction Layer
    User[👤 Developer] --> CLI[🖥️ qgjob CLI Tool]
    User --> GHA[🔄 GitHub Actions]
    
    %% CLI Commands
    CLI --> Submit[📝 qgjob submit]
    CLI --> Status[📊 qgjob status]
    CLI --> Devices[📱 qgjob devices]
    CLI --> Queue[⏳ qgjob queue]
    CLI --> Jobs[📋 qgjob jobs]
    
    %% API Gateway
    Submit --> API[🌐 FastAPI Backend<br/>Port 8002]
    Status --> API
    Devices --> API
    Queue --> API
    Jobs --> API
    GHA --> API
    
    %% Database Layer
    API --> PG[(🗄️ PostgreSQL<br/>Jobs & Devices)]
    
    %% Queue System
    API --> Redis[(🔴 Redis<br/>Job Queues)]
    Redis --> HPQ[🔥 High Priority Queue<br/>Priority 4-5]
    Redis --> NPQ[⚡ Normal Priority Queue<br/>Priority 2-3]
    Redis --> LPQ[🐌 Low Priority Queue<br/>Priority 1]
    
    %% Worker System
    HPQ --> Worker1[👷 Celery Worker 1]
    NPQ --> Worker2[👷 Celery Worker 2]
    LPQ --> Worker3[👷 Celery Worker 3]
    
    %% Device Management
    Worker1 --> DM[🎯 Device Manager]
    Worker2 --> DM
    Worker3 --> DM
    
    DM --> Pool[📱 Device Pool]
    Pool --> Emu1[📱 emulator-1]
    Pool --> Emu2[📱 emulator-2]
    Pool --> Emu3[📱 emulator-3]
    Pool --> Dev1[📱 device-1]
    Pool --> BS1[☁️ browserstack-1]
    
    %% Test Execution
    Worker1 --> TR[🧪 Test Runner]
    Worker2 --> TR
    Worker3 --> TR
    
    TR --> AW[📱 AppWright Tests]
    AW --> App[📦 App Installation<br/>& Test Execution]
```

### Key Features

- **🎯 Priority-Based Scheduling**: 3-tier priority queues (high/normal/low)
- **📦 Intelligent Job Batching**: Groups jobs by `app_version_id` to minimize app installations
- **🔄 Device Preemption**: High-priority jobs can preempt lower-priority ones
- **📊 Real-time Monitoring**: Comprehensive CLI commands for status tracking
- **🚀 Horizontal Scaling**: Multi-worker Celery setup with Redis
- **🛡️ Fault Tolerance**: Database persistence, retry logic, graceful error handling

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis 7+
- Docker (optional)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd qualcli
```

2. **Set up Python environment:**
```bash
python -m venv qualcli
source qualcli/bin/activate  # On Windows: qualcli\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

3. **Start services:**
```bash
# Terminal 1: Start PostgreSQL and Redis
docker-compose up postgres redis

# Terminal 2: Initialize database
python scripts/init_db.py
python scripts/init_devices.py

# Terminal 3: Start backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8002

# Terminal 4: Start Celery worker
cd backend && celery -A queue.celery_app worker --loglevel=info --concurrency=4
```

4. **Verify installation:**
```bash
qgjob devices list
qgjob queue status
```

## 📖 CLI Usage

### Core Commands

#### Submit Test Jobs
```bash
# Basic job submission
qgjob submit --org-id=qualgent --app-version-id=xyz123 --test=tests/onboarding.spec.js

# High priority job with specific target
qgjob submit --org-id=qualgent --app-version-id=abc456 --test=tests/critical.spec.js --priority=5 --target=device

# Low priority background job
qgjob submit --org-id=qualgent --app-version-id=def789 --test=tests/regression.spec.js --priority=1 --target=emulator
```

#### Check Job Status
```bash
# Basic status check
qgjob status job --job-id=123

# Detailed status with priority and device info
qgjob status job --job-id=123 --verbose

# List recent jobs
qgjob jobs recent --limit=10

# Filter jobs by criteria
qgjob jobs list --status-filter=running --priority=4 --target=emulator
```

#### Monitor System Health
```bash
# View queue status
qgjob queue status

# Monitor real-time activity
qgjob queue monitor --watch

# List available devices
qgjob devices list

# View active jobs
qgjob jobs active --watch
```

### Advanced Features

#### Job Management
```bash
# Cancel a job
qgjob jobs cancel 123

# List jobs with filters
qgjob jobs list --app-version-id=xyz123 --status-filter=completed --limit=20

# Monitor priority queue activity
qgjob queue monitor --watch
```

## 🔄 How Grouping & Scheduling Works

### Job Batching Strategy

The system implements intelligent job batching to maximize efficiency:

1. **App Version Grouping**: Jobs targeting the same `app_version_id` and device `target` are automatically batched
2. **Single App Installation**: Each batch installs the app once, then runs all tests sequentially
3. **Time Savings**: Avoids redundant app installations (saves 5-15 seconds per job)

### Priority Scheduling

**Priority Levels (1-5):**
- **Priority 5 (🔥 Critical)**: Immediate processing, can preempt lower-priority jobs
- **Priority 4 (🔥 High)**: Fast-track processing, queue jumping
- **Priority 3 (⚡ Normal)**: Standard processing order
- **Priority 2 (⚡ Normal)**: Standard processing order
- **Priority 1 (🐌 Low)**: Background processing when system is idle

**Queue Routing:**
- High Priority Queue: Priorities 4-5
- Normal Priority Queue: Priorities 2-3  
- Low Priority Queue: Priority 1

### Device Allocation

**Smart Device Selection:**
- **High Priority Jobs**: Get least-loaded devices for best performance
- **Normal Priority Jobs**: Load balancing across available devices
- **Low Priority Jobs**: Use most-loaded (but available) devices to preserve capacity

**Preemption Logic:**
- Priority 4+ jobs can preempt Priority 1-2 jobs
- Preempted jobs are automatically re-queued
- Device utilization is tracked and optimized

## 🔗 GitHub Actions Integration

### Workflow Example

The included workflow (`.github/workflows/appwright-test.yml`) demonstrates:

1. **Service Setup**: Automatically starts PostgreSQL, Redis, backend, and workers
2. **Job Submission**: Submits multiple test jobs with different priorities
3. **Progress Monitoring**: Polls job status until completion
4. **Build Failure**: Fails the CI build if any test fails
5. **Comprehensive Logging**: Shows system status and logs on failure

### Usage in Your CI/CD

```yaml
# .github/workflows/your-tests.yml
- name: Run AppWright Tests
  run: |
    # Submit your critical tests
    qgjob submit --org-id=your-org --app-version-id=${{ github.sha }} --test=tests/critical.spec.js --priority=5
    
    # Submit regression tests
    qgjob submit --org-id=your-org --app-version-id=${{ github.sha }} --test=tests/regression.spec.js --priority=2
```

## 📊 End-to-End Test Submission Example

### Complete Workflow Demo

```bash
# 1. Submit a batch of jobs with the same app version (will be batched)
qgjob submit --org-id=demo --app-version-id=v2.1.0 --test=tests/login.spec.js --priority=3 --target=emulator
qgjob submit --org-id=demo --app-version-id=v2.1.0 --test=tests/signup.spec.js --priority=3 --target=emulator
qgjob submit --org-id=demo --app-version-id=v2.1.0 --test=tests/checkout.spec.js --priority=4 --target=emulator

# 2. Monitor the batching in action
qgjob queue monitor --watch

# 3. Check individual job progress
qgjob status job --job-id=1 --verbose
qgjob status job --job-id=2 --verbose  
qgjob status job --job-id=3 --verbose

# 4. View final results
qgjob jobs list --app-version-id=v2.1.0
```

### Expected Output

```
📊 Queue Status Summary

✅ High Priority Queue: 1 active (0 queued, 1 running)
⏳ Normal Priority Queue: 2 active (2 queued, 0 running)  
✅ Low Priority Queue: 0 active (0 queued, 0 running)

🔄 Active Jobs

Running:
  🔥 Job 3 (P4) - checkout.spec.js (2m in queue)

Waiting in Queue:
  ⚡ Job 1 (P3) - login.spec.js (3m in queue)
  ⚡ Job 2 (P3) - signup.spec.js (3m in queue)
```

## 📈 Sample Output Logs

### Job Processing Logs

```
[2024-01-16 14:30:15] INFO: Starting to process job 1
[2024-01-16 14:30:15] INFO: Allocated device emulator-1 for emulator job (priority: 3, utilization: 0.0%)
[2024-01-16 14:30:15] INFO: Claimed batch of 3 jobs: [1, 2, 3]
[2024-01-16 14:30:15] INFO: Batch details: app_version_id=v2.1.0, target=emulator, device=emulator-1
[2024-01-16 14:30:15] INFO: Installing app v2.1.0 on emulator for batch
[2024-01-16 14:30:20] INFO: App installation completed in 5s
[2024-01-16 14:30:20] INFO: Processing job 1: tests/login.spec.js
[2024-01-16 14:30:23] INFO: Job 1 completed with status: completed
[2024-01-16 14:30:23] INFO: Processing job 2: tests/signup.spec.js  
[2024-01-16 14:30:26] INFO: Job 2 completed with status: completed
[2024-01-16 14:30:26] INFO: Processing job 3: tests/checkout.spec.js
[2024-01-16 14:30:29] INFO: Job 3 completed with status: completed
[2024-01-16 14:30:29] INFO: Batch processing completed:
[2024-01-16 14:30:29] INFO:   - Total jobs: 3
[2024-01-16 14:30:29] INFO:   - Successful: 3
[2024-01-16 14:30:29] INFO:   - Failed: 0
[2024-01-16 14:30:29] INFO:   - Device: emulator-1
[2024-01-16 14:30:29] INFO:   - Total time: 14s
[2024-01-16 14:30:29] INFO:   - Time saved: 10s (avoided 2 app installations)
```

### Priority Queue Processing

```
[2024-01-16 14:25:10] INFO: Routing job 5 (priority 5) to queue: high_priority
[2024-01-16 14:25:10] INFO: High priority job can preempt lower priority jobs
[2024-01-16 14:25:11] INFO: Preempting 1 lower priority jobs on device emulator-2
[2024-01-16 14:25:11] INFO: Successfully preempted device emulator-2 for high priority job
[2024-01-16 14:25:11] INFO: Allocated device emulator-2 for job 5
```

## 🧪 Running Tests

### Unit Tests
```bash
# Run CLI tests
pytest tests/cli/ -v

# Run backend tests  
pytest tests/backend/ -v

# Run with coverage
pytest --cov=backend --cov=cli tests/
```

### Integration Tests
```bash
# Full system test
python scripts/integration_test.py

# Priority scheduling test
python scripts/priority_verification.sh
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/qualcli

# API
API_URL=http://localhost:8002

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Docker Setup

```bash
# Start all services
docker-compose up

# Scale workers
docker-compose up --scale worker=4

# Production deployment
docker-compose -f docker-compose.prod.yml up
```

## 📝 API Documentation

Interactive API documentation available at: `http://localhost:8002/docs`

### Key Endpoints

- `POST /jobs/submit` - Submit new test job
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs` - List jobs with filtering
- `GET /devices` - List available devices
- `GET /queues/status` - Get queue status
- `DELETE /jobs/{job_id}` - Cancel job

## 🚀 Production Deployment

### Horizontal Scaling

```bash
# Scale workers by priority
celery -A backend.queue.celery_app worker --queues=high_priority --concurrency=8
celery -A backend.queue.celery_app worker --queues=normal_priority --concurrency=4  
celery -A backend.queue.celery_app worker --queues=low_priority --concurrency=2
```

### Monitoring

```bash
# Celery monitoring
celery -A backend.queue.celery_app flower

# Queue monitoring  
qgjob queue monitor --watch

# Job analytics
qgjob jobs list --limit=100 | jq '.[] | select(.status=="completed") | .priority' | sort | uniq -c
```

## 🎯 Design Goals Achieved

- ✅ **Modular**: Clear separation between CLI, API, queue system, device management
- ✅ **Reliable**: PostgreSQL persistence, retry logic, graceful error handling, device cleanup
- ✅ **Scalable**: Multi-worker Celery, priority queues, horizontal scaling, device pools
- ✅ **Efficient**: Job batching by app_version_id saves significant installation time

## 🏆 Assignment Completion Status

| Requirement | Status | Implementation |
|-------------|---------|---------------|
| CLI Tool (`qgjob`) | ✅ Complete | Submit, status, devices, queue, jobs commands |
| Backend Service | ✅ Complete | FastAPI with job orchestration, device management |
| Job Grouping | ✅ Complete | Batching by app_version_id with time savings |
| Priority Scheduling | ✅ Complete | 3-tier queues with preemption logic |
| Device Management | ✅ Complete | Smart allocation, load balancing, health tracking |
| GitHub Actions | ✅ Complete | Full CI/CD integration with failure handling |
| Architecture Docs | ✅ Complete | Detailed diagrams and explanations |
| Scalability | ✅ Complete | Horizontal worker scaling, queue distribution |
| Monitoring | ✅ Complete | Real-time CLI monitoring, comprehensive logging |

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details. 