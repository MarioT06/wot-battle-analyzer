import multiprocessing
import os

# Server socket
port = os.environ.get('PORT', '8000')  # Changed default to 8000 to match Render's preference
bind = f"0.0.0.0:{port}"
backlog = 2048

# Worker processes
workers = 1
worker_class = "eventlet"
worker_connections = 1000
timeout = 300
keepalive = 2

# Specify the Python path
pythonpath = '.'

# Logging
capture_output = True
loglevel = "debug"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "wot-battle-analyzer"

# SSL
keyfile = None
certfile = None 