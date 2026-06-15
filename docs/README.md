# CCMed - Adaptive K-12 Mastery Engine

This repository contains the backend and frontend code for the CCMed project, an adaptive K-12 math mastery engine that uses algorithmic Math DNA to procedurally generate countless practice problems.

## 🚀 Quick Setup & Installation

Since `node_modules` and `venv` are intentionally excluded from the Git repository to keep the codebase clean, you will need to install the dependencies locally when you first clone the project.

### 1. Backend Setup (Python)

The backend is built with FastAPI and runs on Python 3.10+.

```bash
# Navigate to the root directory of the project
cd ccmed

# Create a new virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install the required Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup (React)

The frontend is built with React and Vite.

```bash
# Navigate to the frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

---

## 🏃‍♂️ Running the Servers

Once your dependencies are installed, you can use the provided `manage.sh` script from the root directory to easily boot up both servers simultaneously.

```bash
# Ensure the script is executable
chmod +x manage.sh

# Start both backend and frontend servers
./scripts/manage.sh start
```

The script will automatically launch:
*   **Backend:** [http://localhost:8000](http://localhost:8000)
*   **Frontend:** [http://localhost:5173](http://localhost:5173)

### Management Commands
*   `./scripts/manage.sh stop` - Stops all servers cleanly.
*   `./scripts/manage.sh restart` - Restarts both servers.
*   `./scripts/manage.sh status` - Checks if ports 8000 and 5173 are actively running.

## Project Structure Highlights
*   `/backend/app/practice_gen/` - The core v2 pipeline for generating algorithmic math problems.
*   `/frontend/src/` - The React UI handling student interactions and the practice workspace.
*   `/american_dump/` - Contains archived legacy code for the American curriculum.
