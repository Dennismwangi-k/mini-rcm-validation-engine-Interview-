import os
import sys
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rcm_project.settings')

app = Celery('rcm_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Fix for macOS fork() issue - use solo pool on macOS
if sys.platform == 'darwin':
    app.conf.worker_pool = 'solo'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

