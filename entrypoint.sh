#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

: "${GUNICORN_CONF:=gunicorn_conf.py}"
: "${WORKER_CLASS:=uvicorn.workers.UvicornWorker}"
: "${APP_MODULE:=project.main:app}"
: "${MYSQL_HOST:=mysql}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_USER:=admin}"
: "${MYSQL_PASSWORD:=admin}"
: "${MYSQL_DATABASE:=populate}"

mysql_ready() {
python << END
import sys

import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(host="${MYSQL_HOST}",
                                        database="${MYSQL_DATABASE}",
                                        user="${MYSQL_USER}",
                                        password="${MYSQL_PASSWORD}")
    print("Conexão estabelecida")
except:
    sys.exit(-1)
sys.exit(0)

END
}
until mysql_ready; do
    >&2 echo 'Waiting for Mysql to become available...'
    sleep 1
done
>&2 echo 'Mysql is available'

if [ "${POD_TYPE}" = 'worker' ]; then
    echo 'Starting Worker'

    celery \
        -A project.main.celery worker \
            -l 'INFO' \
            -c "${WORKER_CONCURRENCY:-4}" \
            -E \
            --without-gossip \
            --without-mingle \
            --without-heartbeat
else
    echo 'Starting FastAPI Web Application...'
    alembic upgrade head
    echo "Database UP"
    exec gunicorn \
        -c "${GUNICORN_CONF}" \
        -w "${GUNICORN_CONCURRENCY:-2}" \
        -k "${WORKER_CLASS}" \
        "${APP_MODULE}"
fi