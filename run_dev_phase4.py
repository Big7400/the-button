# run_dev_phase4.py
import os
import psutil
import subprocess
import signal
import sys
import time

PORT = 8001

def kill_process_on_port(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"Killing process {proc.pid} on port {port}")
                    os.kill(proc.pid, signal.SIGKILL)
        except Exception:
            continue

def start_uvicorn():
    print(f"Starting Phase 4 dev server on port {PORT}...")
    subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                      "--reload", "--port", str(PORT)],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
    print("Server started!")

if __name__ == "__main__":
    kill_process_on_port(PORT)
    time.sleep(1)
    start_uvicorn()
