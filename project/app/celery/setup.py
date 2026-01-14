from celery import current_app as current_celery_app
from celery.signals import worker_process_init

from project.config import get_settings


def create_celery():
    settings = get_settings()
    celery_app = current_celery_app
    celery_app.config_from_object(settings, namespace="default")

    return celery_app


@worker_process_init.connect
def init_worker_tracing(**kwargs):
    """Initialize Phoenix tracing when Celery worker starts."""
    from project.app.observability import setup_phoenix_tracing

    setup_phoenix_tracing()
