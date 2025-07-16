#!/bin/bash

echo "🎯 Priority Scheduling Test (Unbatched Jobs)"
echo "============================================"
echo "Using different app versions to prevent batching"
echo

echo "📤 Step 1: Submit LOW priority jobs (different app versions)"
JOB1=$(python -m cli.main submit --org-id "test" --app-version-id "low-v1" --test "tests/priority_test.js" --priority 1 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "  📤 Low Priority Job: $JOB1 (app: low-v1)"

JOB2=$(python -m cli.main submit --org-id "test" --app-version-id "low-v2" --test "tests/priority_test.js" --priority 1 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "  📤 Low Priority Job: $JOB2 (app: low-v2)"

JOB3=$(python -m cli.main submit --org-id "test" --app-version-id "low-v3" --test "tests/priority_test.js" --priority 1 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "  📤 Low Priority Job: $JOB3 (app: low-v3)"

echo
echo "⏰ Waiting 3 seconds for jobs to start processing..."
sleep 3

echo "🔥 Step 2: Submit HIGH priority job (should jump queue)"
HIGH_JOB=$(python -m cli.main submit --org-id "test" --app-version-id "high-v1" --test "tests/priority_test.js" --priority 5 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "  🔥 High Priority Job: $HIGH_JOB (app: high-v1)"

echo
echo "📊 Monitoring job processing order..."
echo "Expected: High priority job should complete before remaining low priority jobs"
echo

for i in {1..8}; do
    echo "Check #$i ($(date '+%H:%M:%S')):"
    
    STATUS1=$(curl -s http://localhost:8002/jobs/$JOB1 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    STATUS2=$(curl -s http://localhost:8002/jobs/$JOB2 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    STATUS3=$(curl -s http://localhost:8002/jobs/$JOB3 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    STATUS_HIGH=$(curl -s http://localhost:8002/jobs/$HIGH_JOB 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    
    echo "  Low Priority: $JOB1=$STATUS1, $JOB2=$STATUS2, $JOB3=$STATUS3"
    echo "  High Priority: $HIGH_JOB=$STATUS_HIGH"
    
    # Check if high priority job completed while some low priority jobs are still running/queued
    if [ "$STATUS_HIGH" = "completed" ]; then
        echo "  🎉 HIGH PRIORITY JOB COMPLETED!"
        if [ "$STATUS1" = "running" ] || [ "$STATUS1" = "queued" ] || [ "$STATUS2" = "running" ] || [ "$STATUS2" = "queued" ] || [ "$STATUS3" = "running" ] || [ "$STATUS3" = "queued" ]; then
            echo "  ✅ PRIORITY SCHEDULING VERIFIED!"
            echo "     High priority job completed while low priority jobs were still processing"
            break
        elif [ "$STATUS1" != "completed" ] || [ "$STATUS2" != "completed" ] || [ "$STATUS3" != "completed" ]; then
            echo "  ✅ PRIORITY SCHEDULING LIKELY WORKING!"
            echo "     High priority job completed before all low priority jobs"
            break
        fi
    fi
    
    sleep 5
done

echo
echo "📈 Final Status:"
echo "  Jobs $JOB1, $JOB2, $JOB3 (Priority 1): $STATUS1, $STATUS2, $STATUS3"
echo "  Job $HIGH_JOB (Priority 5): $STATUS_HIGH"

echo
echo "🔚 Test Complete" 