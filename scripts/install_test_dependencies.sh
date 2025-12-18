#!/bin/bash
# Install all test dependencies for backend and frontend

set -e

echo "🔧 Installing test dependencies..."
echo ""

# Backend dependencies
echo "📦 Installing Python test dependencies..."
cd /Users/psama0214/Hackathon-AI/paramount-media-ops-mcp
source venv/bin/activate
pip install pytest pytest-cov pytest-asyncio httpx

echo ""
echo "✅ Python test dependencies installed"
echo ""

# Frontend dependencies
echo "📦 Installing Node.js test dependencies..."
cd dashboard
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom @vitest/ui

echo ""
echo "✅ Node.js test dependencies installed"
echo ""

echo "🎉 All test dependencies installed successfully!"
echo ""
echo "Run tests with:"
echo "  Backend:  pytest"
echo "  Frontend: npm test"


