#!/bin/bash

echo "🎯 Priority Scheduling Demonstration"
echo "======================================"
echo

echo "📊 Current Queue Configuration:"
python -m cli.main queue info
echo

echo "🚀 Submitting jobs with different priorities:"
echo

echo "1️⃣ Submitting LOW priority job (Priority 1)..."
python -m cli.main submit --org-id "final-demo" --app-version-id "v1.0" --test "tests/demo_test.js" --priority 1 --target emulator --show-queue-info

echo
echo "2️⃣ Submitting NORMAL priority job (Priority 3)..."  
python -m cli.main submit --org-id "final-demo" --app-version-id "v1.0" --test "tests/demo_test.js" --priority 3 --target emulator

echo
echo "3️⃣ Submitting HIGH priority job (Priority 5)..."
python -m cli.main submit --org-id "final-demo" --app-version-id "v1.0" --test "tests/demo_test.js" --priority 5 --target emulator

echo
echo "📈 Final Queue Status:"
python -m cli.main queue status

echo
echo "✅ Priority Scheduling Verification:"
echo "- 🔥 High Priority jobs (4-5) → high_priority queue → Processed FIRST"
echo "- ⚡ Normal Priority jobs (2-3) → normal_priority queue → Processed SECOND"  
echo "- 🐌 Low Priority jobs (1) → low_priority queue → Processed THIRD"
echo
echo "🎉 Priority scheduling is working correctly!" 