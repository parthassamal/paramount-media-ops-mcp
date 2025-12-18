#!/bin/bash
# Quick Demo Startup Script

echo "🚀 Starting Paramount+ AI Operations Platform Demo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}"

# Start backend
echo -e "\n${YELLOW}Starting backend...${NC}"
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
python3 -m mcp.server > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    sleep 1
    echo -n "."
done

# Start frontend
echo -e "\n${YELLOW}Starting frontend...${NC}"
cd dashboard
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait a bit
sleep 3

# Show summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Demo is ready!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📊 Dashboard:${NC} http://localhost:5173"
echo -e "${YELLOW}📡 API Docs:${NC}  http://localhost:8000/docs"
echo -e "${YELLOW}💚 Health:${NC}    http://localhost:8000/health"
echo ""
echo -e "${YELLOW}Backend PID:${NC}  $BACKEND_PID"
echo -e "${YELLOW}Frontend PID:${NC} $FRONTEND_PID"
echo ""
echo -e "${RED}To stop:${NC} kill $BACKEND_PID $FRONTEND_PID"
echo -e "${RED}Or use:${NC}  pkill -f 'mcp.server' && pkill -f 'vite'"
echo ""
echo -e "${GREEN}Opening dashboard in browser...${NC}"
sleep 2
open http://localhost:5173

