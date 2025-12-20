#!/bin/bash
#
# Soccer-AI Startup Script
#
# Starts both backend (FastAPI) and frontend (Vite) servers.
# Usage: ./start.sh [--backend-only] [--frontend-only]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default ports
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Parse arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
    case $arg in
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Soccer-AI Startup Script"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend-only   Start only the backend server"
            echo "  --frontend-only  Start only the frontend server"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Servers:"
            echo "  Backend:  http://localhost:$BACKEND_PORT"
            echo "  Frontend: http://localhost:$FRONTEND_PORT"
            echo "  KG Viewer: http://localhost:$BACKEND_PORT/kg-viewer"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}     Soccer-AI Startup Script          ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -i :$port > /dev/null 2>&1
        return $?
    elif command -v netstat &> /dev/null; then
        netstat -tuln | grep -q ":$port "
        return $?
    else
        # Can't check, assume available
        return 1
    fi
}

# Function to start backend
start_backend() {
    echo -e "${YELLOW}Starting Backend Server...${NC}"

    if check_port $BACKEND_PORT; then
        echo -e "${RED}Port $BACKEND_PORT is already in use!${NC}"
        echo "Stop the existing process or use a different port."
        return 1
    fi

    cd "$BACKEND_DIR"

    # Check for .env file
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Warning: No .env file found in backend/${NC}"
        echo "Create one with: ANTHROPIC_API_KEY=your-key-here"
    fi

    # Start uvicorn
    echo -e "${GREEN}Backend starting on http://localhost:$BACKEND_PORT${NC}"
    echo -e "${GREEN}KG Viewer: http://localhost:$BACKEND_PORT/kg-viewer${NC}"
    python3 -m uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
}

# Function to start frontend
start_frontend() {
    echo -e "${YELLOW}Starting Frontend Server...${NC}"

    if check_port $FRONTEND_PORT; then
        echo -e "${RED}Port $FRONTEND_PORT is already in use!${NC}"
        echo "Stop the existing process or use a different port."
        return 1
    fi

    cd "$FRONTEND_DIR"

    # Check for node_modules
    if [ ! -d node_modules ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install
    fi

    # Start Vite dev server
    echo -e "${GREEN}Frontend starting on http://localhost:$FRONTEND_PORT${NC}"
    npm run dev &
    FRONTEND_PID=$!
    echo "Frontend PID: $FRONTEND_PID"
}

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"

    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "Backend stopped"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "Frontend stopped"
    fi

    echo -e "${GREEN}Goodbye!${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start servers based on flags
if [ "$FRONTEND_ONLY" = true ]; then
    start_frontend
elif [ "$BACKEND_ONLY" = true ]; then
    start_backend
else
    start_backend
    sleep 2  # Give backend time to start
    start_frontend
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}     Servers Running                   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for processes
wait
