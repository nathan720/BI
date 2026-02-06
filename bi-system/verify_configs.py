
import os
import sys
import django
import json

# Setup Django environment
sys.path.append('d:\\work\\python\\BI\\bi-system')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings.dev')
django.setup()

from apps.dashboard.utils.chart_config_loader import load_chart_configs

configs = load_chart_configs()
print("Keys in charts:", list(configs['charts'].keys()))
if 'table' in configs['charts']:
    print("Table config found.")
    print("Label:", configs['charts']['table']['label'])
    print("Icon:", configs['charts']['table']['icon'])
else:
    print("Table config NOT found.")
