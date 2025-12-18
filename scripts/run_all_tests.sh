#!/bin/bash
# Run all tests (backend + frontend) with coverage

set -e

echo "🧪 Running All Tests..."
echo ""

# Backend tests
echo "═══════════════════════════════════════"
echo "📊 Backend Tests (Python/FastAPI)"
echo "═══════════════════════════════════════"
cd /Users/psama0214/Hackathon-AI/paramount-media-ops-mcp
source venv/bin/activate
pytest --cov=mcp --cov-report=html --cov-report=term

echo ""
echo "✅ Backend tests completed"
echo "   Coverage report: htmlcov/index.html"
echo ""

# Frontend tests
echo "═══════════════════════════════════════"
echo "📊 Frontend Tests (React/TypeScript)"
echo "═══════════════════════════════════════"
cd dashboard
npm test -- --coverage

echo ""
echo "✅ Frontend tests completed"
echo "   Coverage report: coverage/index.html"
echo ""

echo "🎉 All tests passed!"
echo ""
echo "📈 Coverage Reports:"
echo "  Backend:  htmlcov/index.html"
echo "  Frontend: dashboard/coverage/index.html"


