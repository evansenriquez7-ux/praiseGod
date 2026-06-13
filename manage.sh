#!/bin/bash

# Management script for CCMed backend & frontend servers (Tailscale optimized)

# Colors for pretty terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function stop_backend() {
    # Only kill the process LISTENING on port 8000 — not SSH forwards or other connections
    PID_8000=$(lsof -t -i:8000 -sTCP:LISTEN)
    if [ -n "$PID_8000" ]; then
        echo -e "${RED}[-] Stopping backend on port 8000 (PID: $PID_8000)...${NC}"
        kill -9 $PID_8000 2>/dev/null
    else
        echo -e "${GREEN}[*] Port 8000 is already clear.${NC}"
    fi
    pkill -f "uvicorn backend.app.main:app" 2>/dev/null
    sleep 0.3
}

function stop_frontend() {
    # Only kill the process LISTENING on port 5173 — not SSH forwards or other connections
    PID_5173=$(lsof -t -i:5173 -sTCP:LISTEN)
    if [ -n "$PID_5173" ]; then
        echo -e "${RED}[-] Stopping frontend on port 5173 (PID: $PID_5173)...${NC}"
        kill -9 $PID_5173 2>/dev/null
    else
        echo -e "${GREEN}[*] Port 5173 is already clear.${NC}"
    fi
    pkill -f "vite" 2>/dev/null
    sleep 0.3
}

function stop_servers() {
    echo -e "${BLUE}[+] Ensuring everything is cleanly exited...${NC}"
    stop_backend
    stop_frontend
    echo -e "${GREEN}[✓] All ports and processes are fully cleared!${NC}"
}

function start_backend() {
    echo -e "${BLUE}[+] Starting FastAPI backend on http://0.0.0.0:8000...${NC}"
    PYTHONPATH=. venv/bin/uvicorn backend.app.main:app --port 8000 --host 0.0.0.0 >> scratch/backend.log 2>&1 &

    # Wait up to 15 seconds for backend to bind and respond
    BACKEND_READY=false
    for i in {1..15}; do
        if curl -s http://localhost:8000/api/students/profiles >/dev/null; then
            echo -e "\n${GREEN}[✓] Backend is fully responsive!${NC}"
            BACKEND_READY=true
            break
        fi
        echo -n "."
        sleep 1
    done

    if [ "$BACKEND_READY" = false ]; then
        echo -e "\n${RED}[!] Warning: Backend is taking unusually long. Checking logs...${NC}"
        tail -n 10 scratch/backend.log
    fi
}

function start_frontend() {
    echo -e "${BLUE}[+] Starting Vite frontend on http://0.0.0.0:5173...${NC}"
    cd frontend
    npm exec vite -- --port 5173 --host 0.0.0.0 >> ../scratch/frontend.log 2>&1 &
    cd ..

    # Wait up to 10 seconds for Vite to bind
    FRONTEND_READY=false
    for i in {1..10}; do
        if lsof -i:5173 -sTCP:LISTEN >/dev/null 2>&1; then
            echo -e "\n${GREEN}[✓] Frontend is active on port 5173!${NC}"
            FRONTEND_READY=true
            break
        fi
        echo -n "."
        sleep 1
    done

    if [ "$FRONTEND_READY" = false ]; then
        echo -e "\n${RED}[!] Warning: Frontend port 5173 is not active yet. Checking logs...${NC}"
        tail -n 10 scratch/frontend.log
    fi
}

function start_servers() {
    echo -e "${BLUE}[+] Starting CCMed services cleanly...${NC}"
    start_backend
    start_frontend
    echo -e "${GREEN}[✓] CCMed started cleanly!${NC}"
    echo -e "${GREEN}[*] Backend log:  scratch/backend.log${NC}"
    echo -e "${GREEN}[*] Frontend log: scratch/frontend.log${NC}"
    echo -e "${GREEN}[*] App: http://localhost:5173/${NC}"
}

case "$1" in
    start)
        stop_servers
        start_servers
        ;;
    stop)
        stop_servers
        ;;
    restart)
        stop_servers
        start_servers
        ;;
    restart-backend)
        echo -e "${BLUE}[+] Restarting backend only (Vite and SSH sessions untouched)...${NC}"
        stop_backend
        start_backend
        echo -e "${GREEN}[✓] Backend restarted.${NC}"
        echo -e "${GREEN}[*] Backend log: scratch/backend.log${NC}"
        ;;
    restart-frontend)
        echo -e "${BLUE}[+] Restarting frontend only...${NC}"
        stop_frontend
        start_frontend
        echo -e "${GREEN}[✓] Frontend restarted.${NC}"
        ;;
    status)
        echo -e "${BLUE}[*] Checking CCMed status...${NC}"
        PID_8000=$(lsof -t -i:8000 -sTCP:LISTEN)
        PID_5173=$(lsof -t -i:5173 -sTCP:LISTEN)
        if [ -n "$PID_8000" ]; then
            echo -e "${GREEN}[✓] Backend is RUNNING on port 8000 (PID: $PID_8000)${NC}"
        else
            echo -e "${RED}[-] Backend is STOPPED${NC}"
        fi
        if [ -n "$PID_5173" ]; then
            echo -e "${GREEN}[✓] Frontend is RUNNING on port 5173 (PID: $PID_5173)${NC}"
        else
            echo -e "${RED}[-] Frontend is STOPPED${NC}"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|restart-backend|restart-frontend|status}"
        exit 1
esac
