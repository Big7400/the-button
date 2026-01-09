#!/usr/bin/env python3
"""
Super Dev Runner
----------------
- Handles Phase 2 → Phase 4+ dev servers
- Auto-kills port conflicts (default: 8001)
- Installs missing dependencies (like psutil)
- Starts uvicorn for your FastAPI app
- Future-proof for additional phases
"""

import os
import sys
import subprocess
import signal
import time

try:
    import psutil
except ImportError:
    print("psutil not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

PORT = 8001
APP_MODULE = "app.main:app"
RELOAD = True

PHASES = {
    "2": "Phase 2: Auth + DB",
    "2.5": "Phase 2.5: JWT Route Protection + User Router",
    "3": "Phase 3: Roles + Multi-table DB",
    "3.5": "Phase 3.5: Dev Runner + Protected Routes",
    "4": "Phase 4: Multi-table Relational DB + Admin/User Dashboards"
}

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"Killing process {proc.pid} ({proc.name()}) on port {port}...")
                    os.kill(proc.pid, signal.SIGKILL)
        except Exception:
            continue

def start_uvicorn():
    """Start the FastAPI dev server with reload"""
    cmd = [sys.executable, "-m", "uvicorn", APP_MODULE, "--port", str(PORT)]
    if RELOAD:
        cmd.append("--reload")
    print(f"Starting server: {' '.join(cmd)}")
    subprocess.Popen(cmd)
    print(f"Server should be running at http://127.0.0.1:{PORT}/docs")

def main():
    print("\n=== SUPER DEV RUNNER ===\n")
    print("Available Phases:")
    for k, v in PHASES.items():
        print(f"  {k}: {v}")
    
    phase = input("\nEnter phase to run (default 4): ").strip() or "4"
    if phase not in PHASES:
        print(f"Phase {phase} not recognized. Defaulting to Phase 4.")
        phase = "4"
    print(f"\nRunning {PHASES[phase]}...\n")

    # Kill port if in use
    kill_process_on_port(PORT)
    time.sleep(1)

    # Start Uvicorn server
    start_uvicorn()

    print("\n✅ Dev server launched successfully!")
    print("Use Ctrl+C to stop. Always run this script before testing your app.\n")

if __name__ == "__main__":
    main()
