import os

workers_per_core_str = os.getenv("WORKER_PER_CORE", "1")
use_max_workers = None

host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8000")
use_loglevel = os.getenv("LOG_LEVEL", "info")
use_bind = f"{host}:{port}"

# Gunicorn config variables
loglevel = use_loglevel
bind = use_bind

cores = int(os.getenv("GUNICORN_CONCURRENCY", "1"))
workers_per_core = int(workers_per_core_str)
default_web_concurrency = workers_per_core * cores
accesslog_var = os.getenv("ACCESS_LOG", "-")
use_accesslog = accesslog_var or None
errorlog_var = os.getenv("ERROR_LOG", "-")
use_errorlog = errorlog_var or None
graceful_timeout_str = os.getenv("GRACEFUL_TIMEOUT", "360")
timeout_str = os.getenv("TIMEOUT", "360")
keepalive_str = os.getenv("KEEP_ALIVE", "5")

# Gunicorn config variables
loglevel = use_loglevel
workers = default_web_concurrency
bind = use_bind
errorlog = use_errorlog
worker_tmp_dir = "/dev/shm"
accesslog = use_accesslog
graceful_timeout = int(graceful_timeout_str)
timeout = int(timeout_str)
keepalive = int(keepalive_str)
