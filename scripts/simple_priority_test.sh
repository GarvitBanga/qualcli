#!/bin/bash

echo "🎯 Simple Priority Scheduling Test"
echo "=================================="
echo

echo "Step 1: Submit 3 LOW priority jobs quickly"
JOB1=$(python -m cli.main submit --org-id "test" --app-version-id "v1" --test "tests/priority_test.js" --priority 1 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "📤 Low Priority Job: $JOB1"

JOB2=$(python -m cli.main submit --org-id "test" --app-version-id "v1" --test "tests/priority_test.js" --priority 1 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "📤 Low Priority Job: $JOB2"

JOB3=$(python -m cli.main submit --org-id "test" --app-version-id "v1" --test "tests/priority_test.js" --priority 1 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "📤 Low Priority Job: $JOB3"

sleep 2

echo
echo "Step 2: Submit HIGH priority job"
HIGH_JOB=$(python -m cli.main submit --org-id "test" --app-version-id "v1" --test "tests/priority_test.js" --priority 5 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "🔥 High Priority Job: $HIGH_JOB"

echo
echo "Step 3: Check processing order by API"
echo "Low priority jobs: $JOB1, $JOB2, $JOB3"
echo "High priority job: $HIGH_JOB"
echo

for i in {1..5}; do
    echo "Check #$i:"
    
    # Get status of each job
    STATUS1=$(curl -s http://localhost:8002/jobs/$JOB1 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    STATUS2=$(curl -s http://localhost:8002/jobs/$JOB2 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    STATUS3=$(curl -s http://localhost:8002/jobs/$JOB3 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    STATUS_HIGH=$(curl -s http://localhost:8002/jobs/$HIGH_JOB 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null)
    
    echo "  Low Priority: Job $JOB1=$STATUS1, Job $JOB2=$STATUS2, Job $JOB3=$STATUS3"
    echo "  High Priority: Job $HIGH_JOB=$STATUS_HIGH"
    
    if [ "$STATUS_HIGH" = "completed" ]; then
        echo "🎉 HIGH PRIORITY JOB COMPLETED!"
        if [ "$STATUS1" != "completed" ] || [ "$STATUS2" != "completed" ] || [ "$STATUS3" != "completed" ]; then
            echo "✅ PRIORITY SCHEDULING VERIFIED!"
            echo "   High priority job ($HIGH_JOB) completed before some low priority jobs"
        fi
        break
    fi
    
    sleep 5
done

echo
echo "🔚 Test Complete" 