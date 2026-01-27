# Gunicorn configuration file for SAT-SHINE

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging - Use stdout/stderr for cloud deployments
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "sat_shine_gunicorn"

# Server mechanics
daemon = False
# Remove pidfile, user, group for cloud deployments
# pidfile = "/var/run/sat_shine/gunicorn.pid"
# user = "www-data"
# group = "www-data"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Environment - Remove specific settings module reference
# raw_env = [
#     'DJANGO_SETTINGS_MODULE=Sat_Shine.settings.production',
#     'DJANGO_ENVIRONMENT=production',
# ]