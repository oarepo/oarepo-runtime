from celery import shared_task

# TODO priority if something big is in queue already
@shared_task(name='ping')
def ping():
    return 'pong'