#!/bin/bash

# Phase 1 Test Script
echo "=== Phase 1 Workflow Test ==="
echo

# 1. Register/Login
echo "1. Testing Authentication..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser@demo.com&password=TestPass123!" | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get auth token"
  exit 1
fi
echo "✅ Authentication successful"
echo

# 2. Create test PDF
echo "2. Creating test document..."
cat > /tmp/test_doc.txt << 'EOF'
Q1 2024 Financial Report

Revenue: $1,250,000
Expenses: $850,000
Net Profit: $400,000

Key Highlights:
- 25% growth in recurring revenue
- Customer acquisition cost decreased by 15%
- Operating margin improved to 32%

Risk Assessment:
Our risk tolerance is moderate. We maintain a balanced portfolio.

Account Balances:
- Checking: $125,000
- Savings: $450,000
- Investments: $1,200,000
EOF
echo "✅ Test document created"
echo

# 3. Upload document (as text file, not PDF for simplicity)
echo "3. Uploading document..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_doc.txt;filename=financial_report.pdf;type=application/pdf")

echo "Upload response: $UPLOAD_RESPONSE"

DOC_ID=$(echo $UPLOAD_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)

if [ -z "$DOC_ID" ]; then
  echo "❌ Document upload failed"
  echo "Response: $UPLOAD_RESPONSE"
  exit 1
fi
echo "✅ Document uploaded. ID: $DOC_ID"
echo

# 4. Check document status
echo "4. Checking document processing status..."
for i in {1..10}; do
  STATUS=$(curl -s http://localhost:8000/api/v1/documents/$DOC_ID \
    -H "Authorization: Bearer $TOKEN" | \
    python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null)
  
  echo "   Status check $i: $STATUS"
  
  if [ "$STATUS" = "PROCESSED" ]; then
    echo "✅ Document processed successfully"
    break
  fi
  
  if [ "$STATUS" = "FAILED" ]; then
    echo "❌ Document processing failed"
    exit 1
  fi
  
  sleep 3
done
echo

# 5. Test RAG query
echo "5. Testing RAG query..."
QUERY_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/chat/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was the Q1 revenue and net profit?",
    "maxResults": 5,
    "stream": false
  }')

echo "Query response:"
echo $QUERY_RESPONSE | python3 -m json.tool 2>/dev/null || echo "$QUERY_RESPONSE"
echo

echo "=== Test Complete ==="
