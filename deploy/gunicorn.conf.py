# SQLite demo: one process with a bounded thread pool; do not scale replicas.
bind = '0.0.0.0:8000'
workers = 1
worker_class = 'gthread'
threads = 4
timeout = 60
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 100
# No management socket is needed in a read-only demonstration container.
control_socket_disable = True
accesslog = '-'
errorlog = '-'
# Query strings can contain email/reset tokens. Never log them.
access_log_format = '%(h)s %(m)s %(U)s %(s)s %(L)s'
