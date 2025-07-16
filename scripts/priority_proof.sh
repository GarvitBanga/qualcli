#!/bin/bash

echo "🎯 DEFINITIVE Priority Scheduling Proof"
echo "======================================="
echo "Strategy: Submit MORE jobs than workers to force queueing"
echo

# Submit 8 LOW priority jobs rapidly (more than the 4 workers)
echo "📤 Submitting 8 LOW priority jobs rapidly..."
for i in {1..8}; do
    python -m cli.main submit --org-id "proof-test" --app-version-id "low-v$i" --test "tests/priority_test.js" --priority 1 --target emulator 2>/dev/null &
done
wait

echo "⏰ Waiting 2 seconds for jobs to start queuing..."
sleep 2

# Now submit HIGH priority job - this should jump the queue
echo "🔥 Submitting HIGH priority job (should jump queue)..."
HIGH_JOB=$(python -m cli.main submit --org-id "proof-test" --app-version-id "high-urgent" --test "tests/priority_test.js" --priority 5 --target emulator 2>/dev/null | grep "Job ID:" | grep -o "[0-9]*")
echo "  🔥 High Priority Job: $HIGH_JOB"

echo
echo "📊 Check the Celery logs now - you should see:"
echo "   1. Multiple low priority jobs running on workers 1-4"
echo "   2. High priority job $HIGH_JOB jumping queue and getting next available worker"
echo "   3. High priority job completing before some low priority jobs"

echo
echo "🔍 Monitor with: tail -f celery_tasks.log | grep -E '(Starting to process job|succeeded)'" 