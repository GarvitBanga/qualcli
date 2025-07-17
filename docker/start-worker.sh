#!/bin/bash

echo "🚀 Starting AppWright Worker Container"
echo "====================================="

# Start virtual display for headless operation
echo "📺 Starting virtual display..."
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99

# Wait for display to be ready
sleep 2

# Start Android emulator in background if not running
echo "📱 Starting Android emulator..."
if ! pgrep -f emulator; then
    echo "Starting emulator in headless mode..."
    cd $ANDROID_HOME/emulator
    ./emulator -avd test_emulator -no-window -no-audio -no-boot-anim -gpu off &
    
    echo "⏳ Waiting for emulator to boot (this may take a few minutes)..."
    timeout 300s bash -c 'until adb shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; do sleep 5; done'
    
    if adb shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; then
        echo "✅ Emulator booted successfully"
    else
        echo "❌ Emulator failed to boot within timeout"
        exit 1
    fi
else
    echo "✅ Emulator already running"
fi

# Wait for ADB to detect the device
echo "🔍 Waiting for ADB to detect emulator..."
timeout 60s bash -c 'until adb devices | grep -q "emulator.*device"; do sleep 2; done'

if adb devices | grep -q "emulator.*device"; then
    echo "✅ ADB connected to emulator"
    adb devices
else
    echo "❌ Failed to connect to emulator via ADB"
    exit 1
fi

# Set worker configuration based on environment
WORKER_NAME=${WORKER_NAME:-"appwright-worker-$(hostname)"}
WORKER_QUEUES=${WORKER_QUEUES:-"high_priority,normal_priority,low_priority"}
WORKER_CONCURRENCY=${WORKER_CONCURRENCY:-"2"}

echo "🔧 Worker Configuration:"
echo "   Name: $WORKER_NAME"
echo "   Queues: $WORKER_QUEUES"
echo "   Concurrency: $WORKER_CONCURRENCY"
echo "   Real Execution: $USE_REAL_APPWRIGHT_EXECUTION"

# Start Celery worker
echo "🏃 Starting Celery worker..."
exec celery -A backend.queue.celery_app worker \
    --hostname="$WORKER_NAME" \
    --queues="$WORKER_QUEUES" \
    --concurrency="$WORKER_CONCURRENCY" \
    --loglevel=info \
    --logfile=/app/logs/worker.log 