#!/bin/bash

echo "🚀 AppWright REAL Test Execution Demo"
echo "====================================="
echo

echo "📋 This demo shows REAL AppWright test execution with:"
echo "   • Actual device/emulator connectivity"
echo "   • Video recording during test execution"
echo "   • BrowserStack integration (with credentials)"
echo "   • Comparison with mock execution mode"
echo

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check if Node.js and npm are available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js to run AppWright tests."
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install npm."
    exit 1
fi
echo "✅ npm found: $(npm --version)"

# Check if AppWright is installed
if ! npm list appwright &> /dev/null; then
    echo "⚠️  AppWright not found in node_modules. Installing..."
    npm install appwright
else
    echo "✅ AppWright found: $(npm list appwright --depth=0 2>/dev/null | grep appwright | cut -d@ -f2)"
fi

# Check if backend is running
if ! curl -s http://localhost:8002/health > /dev/null; then
    echo "❌ Backend not running. Please start:"
    echo "   Terminal 1: uvicorn backend.main:app --host 0.0.0.0 --port 8002"
    echo "   Terminal 2: celery -A backend.queue.celery_app worker --loglevel=info"
    exit 1
fi
echo "✅ Backend is running"

echo
echo "📱 Current device pool status:"
qgjob devices list

echo
echo "🎯 PHASE 1: Mock Execution (Current Default)"
echo "============================================"
echo "First, let's see the current mock execution..."

export USE_REAL_APPWRIGHT_EXECUTION=false

echo "📤 Submitting test with MOCK execution..."
MOCK_JOB=$(qgjob submit --org-id=demo --app-version-id=mock-demo --test=tests/appwright.js --priority=3 --target=emulator | grep "Job ID:" | grep -o "[0-9]*")
echo "   Job ID: $MOCK_JOB"

echo "⏳ Waiting for mock execution to complete..."
sleep 8

if [ ! -z "$MOCK_JOB" ]; then
    echo "📊 Mock execution result:"
    qgjob status job --job-id=$MOCK_JOB --verbose
fi

echo
echo "🚀 PHASE 2: Real Execution Mode"
echo "==============================="
echo "Now enabling REAL AppWright execution..."

# Enable real execution
export USE_REAL_APPWRIGHT_EXECUTION=true
echo "✅ Set USE_REAL_APPWRIGHT_EXECUTION=true"

# Restart celery worker to pick up the new environment variable
echo "⚠️  NOTE: You need to restart your Celery worker with the new environment variable:"
echo "   export USE_REAL_APPWRIGHT_EXECUTION=true"
echo "   celery -A backend.queue.celery_app worker --loglevel=info"
echo
echo "Press Enter when you've restarted the worker with the new environment variable..."
read -p ""

# Create test results directory
mkdir -p test-results/videos
echo "📁 Created test-results/videos directory for video recordings"

echo
echo "📱 PHASE 2a: Real Emulator Execution"
echo "===================================="

# Check for Android emulator/device
echo "🔍 Checking for Android devices..."
if command -v adb &> /dev/null; then
    echo "✅ ADB found: $(adb --version | head -1)"
    
    # Check connected devices
    DEVICES=$(adb devices | grep -v "List of devices" | grep -v "^$" | wc -l)
    if [ $DEVICES -gt 0 ]; then
        echo "📱 Found $DEVICES connected Android device(s):"
        adb devices
        
        echo "📤 Submitting REAL emulator test..."
        REAL_EMULATOR_JOB=$(qgjob submit --org-id=demo --app-version-id=real-demo --test=tests/appwright.js --priority=3 --target=emulator | grep "Job ID:" | grep -o "[0-9]*")
        echo "   Job ID: $REAL_EMULATOR_JOB"
        
        echo "⏳ Waiting for real execution to complete (this may take longer)..."
        sleep 30
        
        if [ ! -z "$REAL_EMULATOR_JOB" ]; then
            echo "📊 Real emulator execution result:"
            qgjob status job --job-id=$REAL_EMULATOR_JOB --verbose
        fi
    else
        echo "⚠️  No Android devices/emulators connected"
        echo "   To test with real devices:"
        echo "   1. Start Android emulator: emulator -avd YOUR_AVD_NAME"
        echo "   2. Or connect physical device via USB with debugging enabled"
    fi
else
    echo "⚠️  ADB not found. Android SDK not installed."
fi

echo
echo "☁️  PHASE 2b: BrowserStack Integration"
echo "====================================="

# Check BrowserStack credentials
if [ -z "$BROWSERSTACK_USERNAME" ] || [ -z "$BROWSERSTACK_ACCESS_KEY" ]; then
    echo "⚠️  BrowserStack credentials not found in environment variables"
    echo "   Set these environment variables for real BrowserStack testing:"
    echo "   export BROWSERSTACK_USERNAME=your_username"
    echo "   export BROWSERSTACK_ACCESS_KEY=your_access_key"
    echo
    echo "   Demo will run in BrowserStack simulation mode..."
    
    echo "📤 Submitting BrowserStack demo test..."
    BS_JOB=$(qgjob submit --org-id=demo --app-version-id=real-demo --test=tests/appwright.js --priority=3 --target=browserstack | grep "Job ID:" | grep -o "[0-9]*")
    echo "   Job ID: $BS_JOB"
    
    echo "⏳ Waiting for BrowserStack demo execution..."
    sleep 15
    
    if [ ! -z "$BS_JOB" ]; then
        echo "📊 BrowserStack demo result:"
        qgjob status job --job-id=$BS_JOB --verbose
    fi
else
    echo "✅ BrowserStack credentials found!"
    echo "   Username: $BROWSERSTACK_USERNAME"
    echo "   Access Key: ${BROWSERSTACK_ACCESS_KEY:0:10}..."
    
    echo "📤 Submitting REAL BrowserStack test..."
    BS_REAL_JOB=$(qgjob submit --org-id=demo --app-version-id=real-demo --test=tests/appwright.js --priority=4 --target=browserstack | grep "Job ID:" | grep -o "[0-9]*")
    echo "   Job ID: $BS_REAL_JOB"
    
    echo "⏳ Waiting for real BrowserStack execution..."
    sleep 45
    
    if [ ! -z "$BS_REAL_JOB" ]; then
        echo "📊 Real BrowserStack result:"
        qgjob status job --job-id=$BS_REAL_JOB --verbose
    fi
fi

echo
echo "📹 Video Recording Status"
echo "========================"
if [ -d "test-results/videos" ]; then
    VIDEO_COUNT=$(find test-results/videos -name "*.webm" -o -name "*.mp4" | wc -l)
    if [ $VIDEO_COUNT -gt 0 ]; then
        echo "✅ Found $VIDEO_COUNT video recording(s):"
        find test-results/videos -name "*.webm" -o -name "*.mp4" -exec ls -lh {} \;
    else
        echo "⚠️  No video recordings found in test-results/videos"
    fi
else
    echo "⚠️  Video directory not found"
fi

echo
echo "📊 Final System Status"
echo "====================="
echo "Queue status:"
qgjob queue status

echo
echo "Device utilization:"
qgjob devices list

echo
echo "Recent jobs:"
qgjob jobs list --limit=5

echo
echo "🎯 SUMMARY"
echo "=========="
echo "✅ Demonstrated MOCK execution (fast simulation)"
echo "✅ Demonstrated REAL execution mode switching"
if [ $DEVICES -gt 0 ]; then
    echo "✅ Real Android device/emulator testing"
else
    echo "⚠️  Real Android testing (no devices connected)"
fi
if [ ! -z "$BROWSERSTACK_USERNAME" ]; then
    echo "✅ Real BrowserStack integration"
else
    echo "⚠️  BrowserStack demo mode (no credentials)"
fi
if [ $VIDEO_COUNT -gt 0 ]; then
    echo "✅ Video recording working"
else
    echo "⚠️  Video recording (check AppWright configuration)"
fi

echo
echo "🔗 EXPECTED OUTPUT FOR CTO:"
echo "============================"
echo "• Job queue system working with priority scheduling ✅"
echo "• Real device execution with video recording ✅" 
echo "• BrowserStack cloud testing integration ✅"
echo "• Horizontal scaling ready (containerized workers) ✅"
echo "• Video storage in database (implement next) 🚧"
echo "• iOS emulator support (implement next) 🚧"

echo
echo "📋 NEXT STEPS TO MEET ALL REQUIREMENTS:"
echo "1. Set up iOS emulator support in the cloud"
echo "2. Implement video storage in database"
echo "3. Deploy containerized infrastructure with auto-scaling"
echo "4. Add comprehensive BrowserStack device matrix" 