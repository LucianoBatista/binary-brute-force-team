from celery import current_app as current_celery_app
from project.config import get_settings


def create_celery():
    settings = get_settings()
    celery_app = current_celery_app
    celery_app.config_from_object(settings, namespace="default")

    return celery_app
