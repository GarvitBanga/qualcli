#!/bin/bash

echo "🚀 QualCLI Job Batching Demonstration"
echo "===================================="
echo

# Create some test files if they don't exist
mkdir -p tests/demo
echo 'console.log("Demo test 1");' > tests/demo/test1.spec.js
echo 'console.log("Demo test 2");' > tests/demo/test2.spec.js
echo 'console.log("Demo test 3");' > tests/demo/test3.spec.js

echo "📋 Submitting 3 jobs with the same app_version_id simultaneously..."
echo "   This should trigger batch processing to avoid multiple app installations."
echo

# Submit multiple jobs quickly for the same app version
qgjob submit --org-id=demo-org --app-version-id=demo-app-v1.0 --test=tests/demo/test1.spec.js --priority=1 --target=emulator &
qgjob submit --org-id=demo-org --app-version-id=demo-app-v1.0 --test=tests/demo/test2.spec.js --priority=2 --target=emulator &
qgjob submit --org-id=demo-org --app-version-id=demo-app-v1.0 --test=tests/demo/test3.spec.js --priority=1 --target=emulator &

# Wait for all submissions to complete
wait

echo
echo "⏳ Waiting for batch processing to complete..."
sleep 8

echo
echo "📊 Batch Summary:"
curl -s http://localhost:8002/batches/summary | python -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Total Jobs: {data['summary']['total_jobs']}\")
print(f\"Total Batches: {data['summary']['total_batches']}\")
print(f\"Average Batch Size: {data['summary']['average_batch_size']}\")
print(f\"Time Saved: {data['summary']['potential_time_saved_seconds']} seconds\")
print()
print('Recent Batch (demo-app-v1.0):')
for batch in data['batches']:
    if batch['app_version_id'] == 'demo-app-v1.0':
        print(f\"  • App Version: {batch['app_version_id']}\")
        print(f\"  • Target: {batch['target']}\")
        print(f\"  • Total Jobs: {batch['total_jobs']}\")
        print(f\"  • Status: {batch['status_breakdown']}\")
        break
"

echo
echo "✅ Batching demonstration complete!"
echo
echo "💡 Key Benefits:"
echo "   • Jobs with same app_version_id are grouped together"
echo "   • App installation happens only once per batch"
echo "   • Significant time savings on multiple jobs"
echo "   • Individual job results are tracked separately" 