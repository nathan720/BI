import os

from django.core.wsgi import get_wsgi_application

# Compatibility fix: if env var points to old config.settings, redirect to conf.settings.dev
if os.environ.get('DJANGO_SETTINGS_MODULE', '').startswith('config.settings'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'conf.settings.dev'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings.dev')

application = get_wsgi_application()
