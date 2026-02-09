#!/bin/bash

echo "=========================================="
echo "PHASE 3 INTEGRATION TEST"
echo "=========================================="
echo ""

echo "TEST 1: Call /chat/integrated endpoint"
echo "---"
curl -X POST http://localhost:8000/chat/integrated \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "source": "chat_ui",
    "external_user_id": null,
    "text": "Tell me about web scraping"
  }' \
  -s | python -m json.tool

echo ""
echo "TEST 2: List goals from whiteboard"
echo "---"
curl -X GET http://localhost:8000/api/whiteboard/goals \
  -s | python -m json.tool

echo ""
echo "=========================================="
echo "TESTS COMPLETED"
echo "=========================================="
