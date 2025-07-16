#!/bin/bash

echo "🚀 Enhanced QualCLI Features Demonstration"
echo "=========================================="
echo
echo "This demo showcases the new priority scheduling and enhanced CLI commands."
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 1. Priority Queue Configuration${NC}"
echo "   Let's see how priority queues are configured:"
echo
qgjob queue info
echo

echo -e "${BLUE}📊 2. Current Queue Status${NC}"
echo "   Checking current queue activity:"
echo
qgjob queue status
echo

echo -e "${BLUE}🔥 3. Submitting High Priority Job (Priority 5)${NC}"
echo "   This will go to the high priority queue and be processed first:"
echo
qgjob submit --org-id=cli-demo --app-version-id=demo-app-v2.0 --test=tests/demo/test_high.spec.js --priority=5 --target=emulator --show-queue-info
echo

echo -e "${BLUE}⚡ 4. Submitting Normal Priority Job (Priority 3)${NC}"
echo "   This will go to the normal priority queue:"
echo
qgjob submit --org-id=cli-demo --app-version-id=demo-app-v2.0 --test=tests/demo/test_normal.spec.js --priority=3 --target=emulator
echo

echo -e "${BLUE}🐌 5. Submitting Low Priority Job (Priority 1)${NC}"
echo "   This will go to the low priority queue:"
echo
qgjob submit --org-id=cli-demo --app-version-id=demo-app-v2.0 --test=tests/demo/test_low.spec.js --priority=1 --target=emulator
echo

echo -e "${BLUE}📈 6. Updated Queue Status${NC}"
echo "   See how jobs are distributed across priority queues:"
echo
qgjob queue status
echo

echo -e "${BLUE}🔍 7. System Status Summary${NC}"
echo "   Overall system health and activity:"
echo
qgjob status summary
echo

echo -e "${BLUE}📱 8. Device Status${NC}"
echo "   Check device allocation and priority usage:"
echo
qgjob devices status
echo

echo -e "${BLUE}⏱️  9. Real-time Queue Monitor (5 seconds)${NC}"
echo "   Watch live queue activity:"
echo
timeout 5s qgjob queue monitor --watch || echo "   Monitor stopped after 5 seconds"
echo

echo -e "${GREEN}✅ CLI Enhancement Demo Complete!${NC}"
echo
echo -e "${PURPLE}💡 Key Features Demonstrated:${NC}"
echo "  🔥 Priority-based job routing (1-5 priority levels)"
echo "  📊 Real-time queue monitoring and status"
echo "  📋 Enhanced job submission with visual indicators"
echo "  🎯 Intelligent device allocation based on priority"
echo "  📈 Comprehensive system status summaries"
echo "  🔍 Rich CLI formatting with icons and colors"
echo
echo -e "${PURPLE}🛠️  Available CLI Commands:${NC}"
echo "  qgjob submit     - Submit jobs with priority scheduling"
echo "  qgjob status     - Enhanced job status with priority info"
echo "  qgjob queue      - Priority queue management and monitoring"
echo "  qgjob jobs       - Job listing, filtering, and management"
echo "  qgjob devices    - Device pool management and allocation"
echo
echo -e "${CYAN}📖 Command Examples:${NC}"
echo "  qgjob submit --priority=5 --target=emulator test.js"
echo "  qgjob queue info"
echo "  qgjob queue monitor --watch"
echo "  qgjob status job --job-id=123 --verbose"
echo "  qgjob status summary"
echo "  qgjob devices list"
echo
echo -e "${GREEN}🎉 Priority scheduling is now fully operational!${NC}" 