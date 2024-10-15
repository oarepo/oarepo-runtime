from celery import shared_task


@shared_task(name='ping')
def ping():
    return 'pong'