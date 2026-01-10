#!/usr/bin/env python3
import subprocess
import sys
import psutil
import time
from pathlib import Path

# -------------------------------
# Config
# -------------------------------
HOST = "0.0.0.0"
PORT = 8001
APP_MODULE = "app.main:app"
PROJECT_ROOT = Path(__file__).parent

# -------------------------------
# Function: Kill process using the port
# -------------------------------
def kill_port(port):
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        for conn in proc.connections(kind="inet"):
            if conn.laddr.port == port:
                print(f"Killing process {proc.info['name']} (PID: {proc.info['pid']}) using port {port}")
                proc.kill()

# -------------------------------
# Function: Start Uvicorn
# -------------------------------
def start_server():
    print(f"Starting server: uvicorn {APP_MODULE} --reload --host {HOST} --port {PORT}\n")
    subprocess.run([sys.executable, "-m", "uvicorn", APP_MODULE, "--reload", "--host", HOST, "--port", str(PORT)])

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("psutil not installed. Installing now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil

    print(f"Phase 4 Dev Runner - TheButtonApp\nProject root: {PROJECT_ROOT}\n")
    
    # Kill any existing process on the port
    kill_port(PORT)
    time.sleep(1)  # wait a moment to ensure port is free

    # Start Uvicorn server
    start_server()
