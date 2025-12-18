#!/bin/bash
# Paramount+ AI Operations Platform - Status Check

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Paramount+ AI Operations Platform - System Status       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python
echo -e "${BLUE}🐍 Python Environment:${NC}"
if [ -d "venv" ]; then
    PYTHON_VERSION=$(venv/bin/python --version 2>&1)
    echo -e "   ${GREEN}✓${NC} Virtual environment exists"
    echo -e "   ${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "   ${RED}✗${NC} Virtual environment not found"
fi
echo ""

# Check Node.js
echo -e "${BLUE}📦 Node.js Environment:${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    echo -e "   ${GREEN}✓${NC} Node.js $NODE_VERSION"
    echo -e "   ${GREEN}✓${NC} npm $NPM_VERSION"
else
    echo -e "   ${RED}✗${NC} Node.js not found"
fi
echo ""

# Check Backend
echo -e "${BLUE}🔧 Backend Status:${NC}"
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Running on port 8000"
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} API responding"
        echo -e "   ${GREEN}→${NC} http://localhost:8000/docs"
    else
        echo -e "   ${YELLOW}⚠${NC} Port 8000 in use but not responding"
    fi
else
    echo -e "   ${RED}✗${NC} Not running"
    echo -e "   ${YELLOW}→${NC} Run: ./start.sh"
fi
echo ""

# Check Frontend
echo -e "${BLUE}🎨 Frontend Status:${NC}"
if lsof -i :5173 > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Running on port 5173"
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓${NC} Dashboard responding"
        echo -e "   ${GREEN}→${NC} http://localhost:5173"
    else
        echo -e "   ${YELLOW}⚠${NC} Port 5173 in use but not responding"
    fi
else
    echo -e "   ${RED}✗${NC} Not running"
    echo -e "   ${YELLOW}→${NC} Run: ./start.sh"
fi
echo ""

# Check Dependencies
echo -e "${BLUE}📚 Dependencies:${NC}"
if [ -f "dashboard/node_modules/.package-lock.json" ]; then
    echo -e "   ${GREEN}✓${NC} Frontend dependencies installed"
else
    echo -e "   ${YELLOW}⚠${NC} Frontend dependencies not installed"
    echo -e "   ${YELLOW}→${NC} Run: cd dashboard && npm install"
fi
echo ""

# Check Configuration
echo -e "${BLUE}⚙️  Configuration:${NC}"
if [ -f ".env" ]; then
    echo -e "   ${GREEN}✓${NC} .env file exists"
    
    # Check key variables
    if grep -q "MOCK_MODE=true" .env 2>/dev/null; then
        echo -e "   ${YELLOW}ℹ${NC} Running in MOCK_MODE (safe for demo)"
    fi
    
    if grep -q "NEWRELIC_API_KEY=.\+" .env 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} NewRelic configured"
    else
        echo -e "   ${YELLOW}⚠${NC} NewRelic not configured (using mocks)"
    fi
    
    if grep -q "DYNATRACE_API_TOKEN=.\+" .env 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Dynatrace configured"
    else
        echo -e "   ${YELLOW}⚠${NC} Dynatrace not configured (using mocks)"
    fi
else
    echo -e "   ${YELLOW}⚠${NC} .env file not found (using defaults)"
    echo -e "   ${YELLOW}→${NC} Copy .env.example to .env"
fi
echo ""

# Project Stats
echo -e "${BLUE}📊 Project Stats:${NC}"
if command -v find &> /dev/null && command -v wc &> /dev/null; then
    PY_FILES=$(find . -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*" -not -path "*/node_modules/*" | wc -l | tr -d ' ')
    TS_FILES=$(find dashboard/src -name "*.tsx" -o -name "*.ts" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "   ${BLUE}→${NC} Python files: $PY_FILES"
    echo -e "   ${BLUE}→${NC} TypeScript files: $TS_FILES"
fi

if [ -f "pytest.ini" ]; then
    echo -e "   ${GREEN}✓${NC} Tests configured"
fi
echo ""

# Quick Commands
echo -e "${YELLOW}⚡ Quick Commands:${NC}"
echo -e "   Start:  ${GREEN}./start.sh${NC}"
echo -e "   Stop:   ${GREEN}./stop.sh${NC}"
echo -e "   Test:   ${GREEN}pytest tests/${NC}"
echo -e "   Logs:   ${GREEN}tail -f logs/*.log${NC}"
echo ""

# Overall Status
if lsof -i :8000 > /dev/null 2>&1 && lsof -i :5173 > /dev/null 2>&1; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              ✨ Platform is READY! ✨                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║         Platform not fully running - Run ./start.sh        ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
fi

