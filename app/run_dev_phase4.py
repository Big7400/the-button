#!/usr/bin/env python3
import os, signal, subprocess, sys
import psutil

PORT = 8001
APP_MODULE = "app.main:app"

# Kill existing process on port
for conn in psutil.net_connections():
    if conn.laddr.port == PORT and conn.pid:
        print(f"Killing process {conn.pid} on port {PORT}")
        os.kill(conn.pid, signal.SIGKILL)

# Start server
subprocess.run([sys.executable, "-m", "uvicorn", APP_MODULE, "--reload", "--host", "0.0.0.0", "--port", str(PORT)])
