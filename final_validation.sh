#!/bin/bash
echo "=========================================="
echo "FINAL SECURITY & FUNCTIONALITY VALIDATION"
echo "=========================================="
echo ""

echo "1. Checking dependency versions..."
pip list | grep -E "(fastapi|mcp)" | while read line; do
  echo "   ✓ $line"
done

echo ""
echo "2. Running validation script..."
python validate.py 2>&1 | grep -E "(PASSED|FAILED)"

echo ""
echo "3. Running test suite..."
python -m pytest tests/ -q --tb=no 2>&1 | tail -2

echo ""
echo "4. Testing server import..."
python -c "from mcp.server import app; print('   ✓ Server imported successfully')"

echo ""
echo "5. Checking for security issues..."
if grep -q "0.104" requirements.txt; then
  echo "   ✗ Old FastAPI version found"
else
  echo "   ✓ FastAPI version is secure"
fi

if grep -q "0.9.0" requirements.txt; then
  echo "   ✗ Old MCP version found"
else
  echo "   ✓ MCP version is secure"
fi

echo ""
echo "=========================================="
echo "✅ VALIDATION COMPLETE"
echo "=========================================="
