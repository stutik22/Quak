#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=8501

# Print banner
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🍳 QWAK Recipe Recommender                ║"
echo "║                     Shell Launcher                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${CYAN}Starting QWAK Recipe Recommender...${NC}"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python is not installed or not in PATH${NC}"
    echo "Please install Python and try again"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo -e "${GREEN}✅ Python found: $PYTHON_CMD${NC}"
echo

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo -e "${CYAN}🧹 Backend stopped${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo -e "${CYAN}🧹 Frontend stopped${NC}"
    fi
    
    echo -e "${GREEN}✅ Shutdown complete!${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Check if directories exist
if [ ! -d "backend" ]; then
    echo -e "${RED}❌ Backend directory not found${NC}"
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Frontend directory not found${NC}"
    exit 1
fi

# Start backend
echo -e "${BLUE}🚀 Starting backend server...${NC}"
cd backend
$PYTHON_CMD -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start backend${NC}"
    cat backend.log
    exit 1
fi

echo -e "${GREEN}✅ Backend server starting on http://localhost:$BACKEND_PORT${NC}"

# Wait for backend to initialize
echo -e "${CYAN}⏳ Waiting for backend to initialize...${NC}"
sleep 3

# Start frontend
echo -e "${BLUE}🎨 Starting frontend app...${NC}"
cd frontend
$PYTHON_CMD -m streamlit run app.py --server.port $FRONTEND_PORT --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start frontend${NC}"
    cat frontend.log
    exit 1
fi

echo -e "${GREEN}✅ Frontend app starting on http://localhost:$FRONTEND_PORT${NC}"

# Wait for services to be ready
echo -e "${CYAN}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check if services are responding
echo -e "${CYAN}🔍 Checking service health...${NC}"

# Check backend health
if command -v curl &> /dev/null; then
    if curl -s http://localhost:$BACKEND_PORT/health > /dev/null; then
        echo -e "${GREEN}✅ Backend is healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend may not be ready yet${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  curl not found, skipping health check${NC}"
fi

# Print success message
echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 QWAK Recipe Recommender is now running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}🔗 Frontend: http://localhost:$FRONTEND_PORT${NC}"
echo -e "${PURPLE}🔗 Backend API: http://localhost:$BACKEND_PORT${NC}"
echo -e "${PURPLE}📚 API Docs: http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo
echo -e "${YELLOW}💡 Press Ctrl+C to stop both services${NC}"
echo -e "${CYAN}📋 Logs are saved to backend.log and frontend.log${NC}"
echo

# Try to open frontend in browser (if on macOS or Linux with xdg-open)
if command -v open &> /dev/null; then
    echo -e "${CYAN}🌐 Opening frontend in browser...${NC}"
    open http://localhost:$FRONTEND_PORT
elif command -v xdg-open &> /dev/null; then
    echo -e "${CYAN}🌐 Opening frontend in browser...${NC}"
    xdg-open http://localhost:$FRONTEND_PORT
fi

# Keep script running and monitor processes
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend process stopped unexpectedly${NC}"
        echo "Backend log:"
        tail -10 backend.log
        break
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend process stopped unexpectedly${NC}"
        echo "Frontend log:"
        tail -10 frontend.log
        break
    fi
    
    sleep 2
done