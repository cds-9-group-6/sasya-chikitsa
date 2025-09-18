#!/bin/bash

# Quick FSM Agent Chat Test Script
# Simple test for basic functionality

set -e

# Configuration
FSM_SERVER_URL="${FSM_SERVER_URL:-http://localhost:8080}"
CHAT_STREAM_ENDPOINT="$FSM_SERVER_URL/sasya-chikitsa/chat-stream"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Quick FSM Chat Test${NC}"
echo -e "Server: $FSM_SERVER_URL"
echo ""

# Check server health
echo -e "${YELLOW}Checking server...${NC}"
if ! curl -s --connect-timeout 5 "$FSM_SERVER_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Server not responding${NC}"
    echo "Please start: cd engine/fsm_agent && python3 run_fsm_server.py"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}"

# Simple text test
echo -e "${YELLOW}Testing simple chat query...${NC}"

SESSION_ID="quick-test-$(date +%s)"

# Create request
cat > /tmp/quick_test_request.json <<EOF
{
    "message": "Hello, I need help with my tomato plants. They have yellowing leaves.",
    "session_id": "$SESSION_ID",
    "context": {
        "plant_type": "Tomato",
        "location": "Maharashtra, India",
        "season": "Summer",
        "growth_stage": "Flowering",
        "farm_size": "2 acres"
    }
}
EOF

echo -e "${BLUE}📤 Sending request...${NC}"

# Send request and show streaming response
curl -X POST "$CHAT_STREAM_ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -d @/tmp/quick_test_request.json \
    --no-buffer \
    -s \
    --max-time 30 | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        event_data="${line#data: }"
        if [[ $event_data == "{"* ]]; then
            # Try to extract content from JSON
            content=$(echo "$event_data" | jq -r '.content // .message // .' 2>/dev/null || echo "$event_data")
            echo -e "${GREEN}Response: $content${NC}"
        else
            echo -e "${GREEN}$event_data${NC}"
        fi
    elif [[ $line == event:* ]]; then
        event_type="${line#event: }"
        echo -e "${YELLOW}[Event: $event_type]${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ Quick test completed!${NC}"

# Cleanup
rm -f /tmp/quick_test_request.json
