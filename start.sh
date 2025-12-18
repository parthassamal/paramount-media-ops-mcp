#!/bin/bash
# Paramount+ AI Operations Platform - Startup Script
# This script starts both backend and frontend for the hackathon demo

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Paramount+ AI Operations Platform - Starting...        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get the project root directory
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo -e "${GREEN}✓ Virtual environment found${NC}"
fi

# Function to check if port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# Check if backend is already running
if check_port 8000; then
    echo -e "${YELLOW}⚠ Backend already running on port 8000${NC}"
    read -p "Kill existing process and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing process on port 8000...${NC}"
        lsof -ti :8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo -e "${YELLOW}Skipping backend startup${NC}"
        SKIP_BACKEND=true
    fi
fi

# Check if frontend is already running
if check_port 5173; then
    echo -e "${YELLOW}⚠ Frontend already running on port 5173${NC}"
    read -p "Kill existing process and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing process on port 5173...${NC}"
        lsof -ti :5173 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo -e "${YELLOW}Skipping frontend startup${NC}"
        SKIP_FRONTEND=true
    fi
fi

# Start Backend
if [ "$SKIP_BACKEND" != "true" ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Starting Backend (FastAPI MCP Server)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Activate virtual environment and start backend in background
    source venv/bin/activate
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Start backend
    echo -e "${YELLOW}Starting FastAPI server on http://localhost:8000${NC}"
    nohup python -m mcp.server > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > logs/backend.pid
    
    # Wait for backend to start
    echo -e "${YELLOW}Waiting for backend to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend started successfully!${NC}"
            echo -e "${GREEN}  API Docs: http://localhost:8000/docs${NC}"
            echo -e "${GREEN}  PID: $BACKEND_PID${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Backend failed to start${NC}"
            echo -e "${RED}Check logs/backend.log for details${NC}"
            exit 1
        fi
        echo -n "."
        sleep 1
    done
else
    echo -e "${GREEN}✓ Backend already running${NC}"
fi

# Start Frontend
if [ "$SKIP_FRONTEND" != "true" ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  Starting Frontend (React Dashboard)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    cd dashboard
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Start frontend in background
    echo -e "${YELLOW}Starting Vite dev server on http://localhost:5173${NC}"
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    
    cd ..
    
    # Wait for frontend to start
    echo -e "${YELLOW}Waiting for frontend to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Frontend started successfully!${NC}"
            echo -e "${GREEN}  Dashboard: http://localhost:5173${NC}"
            echo -e "${GREEN}  PID: $FRONTEND_PID${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Frontend failed to start${NC}"
            echo -e "${RED}Check logs/frontend.log for details${NC}"
            exit 1
        fi
        echo -n "."
        sleep 1
    done
else
    echo -e "${GREEN}✓ Frontend already running${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              🚀 Platform Running Successfully! 🚀         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Dashboard:${NC}     http://localhost:5173"
echo -e "${BLUE}📚 API Docs:${NC}      http://localhost:8000/docs"
echo -e "${BLUE}🔍 Health Check:${NC}  http://localhost:8000/health"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo -e "   Backend:  tail -f logs/backend.log"
echo -e "   Frontend: tail -f logs/frontend.log"
echo ""
echo -e "${YELLOW}⏹  To Stop:${NC}"
echo -e "   Run: ./stop.sh"
echo -e "   Or:  kill \$(cat logs/backend.pid logs/frontend.pid)"
echo ""
echo -e "${GREEN}✨ Ready for hackathon demo!${NC}"
echo ""

# Open browser (optional)
if command -v open &> /dev/null; then
    read -p "Open dashboard in browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:5173
    fi
fi

