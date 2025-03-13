import multiprocessing
import os

# Server socket
port = os.environ.get('PORT', '10000')
bind = f"0.0.0.0:{port}"
backlog = 2048

# Worker processes
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 300
keepalive = 2

# Logging
loglevel = "debug"  # Changed to debug for more info
accesslog = "-"
errorlog = "-"

# Process naming
proc_name = "wot-battle-analyzer"

# SSL
keyfile = None
certfile = None 