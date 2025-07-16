#!/bin/bash

echo "🔧 QualCLI Device Management System Demonstration"
echo "================================================="
echo

# Create test files
mkdir -p tests/device-mgmt-demo
echo 'console.log("Test on emulator");' > tests/device-mgmt-demo/emulator-test.spec.js
echo 'console.log("Test on device");' > tests/device-mgmt-demo/device-test.spec.js  
echo 'console.log("Test on browserstack");' > tests/device-mgmt-demo/browserstack-test.spec.js

echo "📋 Step 1: Current Device Pool Status"
echo "====================================="
qgjob devices status
echo

echo "📋 Step 2: Get Device Recommendations"
echo "====================================="
echo "Emulator recommendation:"
qgjob devices recommend emulator
echo

echo "Device recommendation:"
qgjob devices recommend device
echo

echo "BrowserStack recommendation:"
qgjob devices recommend browserstack
echo

echo "📋 Step 3: Submit Jobs to Different Device Types"
echo "==============================================="
echo "Submitting job to emulator..."
qgjob submit --org-id=device-demo --app-version-id=multi-device-v1.0 --test=tests/device-mgmt-demo/emulator-test.spec.js --priority=1 --target=emulator

echo
echo "Submitting job to physical device..."
qgjob submit --org-id=device-demo --app-version-id=multi-device-v1.0 --test=tests/device-mgmt-demo/device-test.spec.js --priority=2 --target=device

echo
echo "Submitting job to BrowserStack..."
qgjob submit --org-id=device-demo --app-version-id=multi-device-v1.0 --test=tests/device-mgmt-demo/browserstack-test.spec.js --priority=1 --target=browserstack

echo
echo "📋 Step 4: Monitor Device Utilization During Processing"
echo "======================================================="
echo "Waiting 2 seconds for jobs to start processing..."
sleep 2

echo "Current device pool status:"
qgjob devices list

echo
echo "📋 Step 5: Wait for Completion and Check Final Status"
echo "===================================================="
echo "Waiting for jobs to complete..."
sleep 6

echo "Final device pool status:"
qgjob devices list

echo
echo "📋 Step 6: Health Check"
echo "======================"
qgjob devices health

echo
echo "✅ Device Management Demonstration Complete!"
echo
echo "🎯 Key Features Demonstrated:"
echo "  • Device pool visualization and status tracking"
echo "  • Smart device allocation based on availability"
echo "  • Different device types (emulator/device/browserstack)"
echo "  • Real-time utilization monitoring"
echo "  • Automatic device cleanup after job completion"
echo "  • Health checking capabilities"
echo "  • Device recommendations for optimal allocation" 