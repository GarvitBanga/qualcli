#!/bin/bash

# QualCLI Service Startup Script
echo "Starting QualCLI services..."

# Create logs directory
mkdir -p logs

# Kill any existing services
echo "Stopping existing services..."
pkill -f "uvicorn backend.main:app" || true
pkill -f "celery.*backend.queue.celery_app" || true
sleep 2

# Start backend server with logs
echo "Starting backend server..."
uvicorn backend.main:app --host 0.0.0.0 --port 8002 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID"

# Wait for backend to start
sleep 5

# Start Celery worker with logs
echo "Starting Celery worker..."
celery -A backend.queue.celery_app worker --loglevel=INFO > logs/celery.log 2>&1 &
CELERY_PID=$!
echo "Celery worker started with PID: $CELERY_PID"

# Wait for services to be ready
sleep 3

echo "Services started successfully!"
echo "Backend server: http://localhost:8002"
echo "Logs:"
echo "  Backend: logs/backend.log"
echo "  Celery:  logs/celery.log"
echo ""
echo "To stop services:"
echo "  kill $BACKEND_PID $CELERY_PID"
echo "  or run: pkill -f 'uvicorn|celery'" 