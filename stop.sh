#!/bin/bash
# Paramount+ AI Operations Platform - Stop Script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping Paramount+ AI Operations Platform...${NC}"
echo ""

# Get project root
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

# Stop backend
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null
        sleep 2
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo -e "${RED}Force killing backend...${NC}"
            kill -9 $BACKEND_PID 2>/dev/null
        fi
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo -e "${YELLOW}Backend not running${NC}"
    fi
    rm logs/backend.pid
else
    echo -e "${YELLOW}No backend PID file found${NC}"
    # Try to kill by port
    BACKEND_PORT_PID=$(lsof -ti :8000 2>/dev/null)
    if [ ! -z "$BACKEND_PORT_PID" ]; then
        echo -e "${YELLOW}Found process on port 8000, killing...${NC}"
        kill -9 $BACKEND_PORT_PID 2>/dev/null
        echo -e "${GREEN}✓ Backend stopped${NC}"
    fi
fi

# Stop frontend
if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null
        sleep 2
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo -e "${RED}Force killing frontend...${NC}"
            kill -9 $FRONTEND_PID 2>/dev/null
        fi
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    else
        echo -e "${YELLOW}Frontend not running${NC}"
    fi
    rm logs/frontend.pid
else
    echo -e "${YELLOW}No frontend PID file found${NC}"
    # Try to kill by port
    FRONTEND_PORT_PID=$(lsof -ti :5173 2>/dev/null)
    if [ ! -z "$FRONTEND_PORT_PID" ]; then
        echo -e "${YELLOW}Found process on port 5173, killing...${NC}"
        kill -9 $FRONTEND_PORT_PID 2>/dev/null
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✓ Platform stopped${NC}"

