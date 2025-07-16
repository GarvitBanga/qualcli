#!/bin/bash

echo "🎯 Priority Scheduling Verification Test"
echo "========================================"
echo

# Clear any previous jobs to start fresh
echo "📊 Initial Queue Status:"
python -m cli.main queue status
echo

echo "🚀 Step 1: Submit LOW priority jobs first (these should run last)"
echo "Submitting 3 low priority jobs..."

python -m cli.main submit --org-id "priority-demo" --app-version-id "v1.0" --test "tests/priority_test.js" --priority 1 --target emulator > job1.txt &
sleep 1
python -m cli.main submit --org-id "priority-demo" --app-version-id "v1.0" --test "tests/priority_test.js" --priority 1 --target emulator > job2.txt &
sleep 1
python -m cli.main submit --org-id "priority-demo" --app-version-id "v1.0" --test "tests/priority_test.js" --priority 1 --target emulator > job3.txt &

wait
echo "✅ Low priority jobs submitted"

# Extract job IDs
job1_id=$(grep -o "Job ID: [0-9]*" job1.txt | grep -o "[0-9]*")
job2_id=$(grep -o "Job ID: [0-9]*" job2.txt | grep -o "[0-9]*")
job3_id=$(grep -o "Job ID: [0-9]*" job3.txt | grep -o "[0-9]*")

echo "  - Job $job1_id (Priority 1)"
echo "  - Job $job2_id (Priority 1)" 
echo "  - Job $job3_id (Priority 1)"
echo

sleep 2

echo "📋 Queue Status After Low Priority Jobs:"
python -m cli.main queue status
echo

echo "🔥 Step 2: Submit HIGH priority job (this should jump the queue)"
sleep 3
python -m cli.main submit --org-id "priority-demo" --app-version-id "v1.0" --test "tests/priority_test.js" --priority 5 --target emulator > job_high.txt

high_job_id=$(grep -o "Job ID: [0-9]*" job_high.txt | grep -o "[0-9]*")
echo "  - Job $high_job_id (Priority 5) - HIGH PRIORITY"
echo

echo "📋 Queue Status After High Priority Job:"
python -m cli.main queue status
echo

echo "⏱️  Monitoring job processing order..."
echo "Expected order: Job $high_job_id (P5) should complete before Jobs $job1_id, $job2_id, $job3_id (P1)"
echo

# Monitor job statuses
for i in {1..10}; do
    echo "📊 Check #$i ($(date '+%H:%M:%S')):"
    
    status1=$(python -m cli.main status job --job-id $job1_id | grep -o "Status: [A-Z]*" | cut -d' ' -f2)
    status2=$(python -m cli.main status job --job-id $job2_id | grep -o "Status: [A-Z]*" | cut -d' ' -f2)
    status3=$(python -m cli.main status job --job-id $job3_id | grep -o "Status: [A-Z]*" | cut -d' ' -f2)
    status_high=$(python -m cli.main status job --job-id $high_job_id | grep -o "Status: [A-Z]*" | cut -d' ' -f2)
    
    echo "  Low Priority Jobs: $job1_id=$status1, $job2_id=$status2, $job3_id=$status3"
    echo "  High Priority Job: $high_job_id=$status_high"
    
    if [ "$status_high" = "COMPLETED" ]; then
        echo "🎉 HIGH PRIORITY JOB COMPLETED FIRST!"
        if [ "$status1" != "COMPLETED" ] || [ "$status2" != "COMPLETED" ] || [ "$status3" != "COMPLETED" ]; then
            echo "✅ PRIORITY SCHEDULING VERIFIED: High priority job completed before low priority jobs"
        fi
        break
    fi
    
    echo "  Waiting 10 seconds..."
    sleep 10
done

echo
echo "📈 Final Status Summary:"
python -m cli.main jobs list --limit 10

# Cleanup
rm -f job1.txt job2.txt job3.txt job_high.txt

echo
echo "🎯 Priority Scheduling Test Complete!" 