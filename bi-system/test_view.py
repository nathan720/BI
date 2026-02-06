import os
import sys
import django
import json
from django.conf import settings
from django.http import HttpRequest

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings.dev')
django.setup()

from apps.dashboard.views import api_preview_chart

from django.test import RequestFactory

def test_preview():
    # Mock request
    factory = RequestFactory()
    data = {
        "type": "bar",
        "title": "Test Bar",
        "x_axis": ["A", "B", "C"],
        "y_axis": ["V1"],
        "data": [{"name": "A", "value": 10}, {"name": "B", "value": 20}],
        "category_col": "name",
        "value_col": "value",
    }
    request = factory.post('/api/preview_chart/', data=json.dumps(data), content_type='application/json')
    
    response = api_preview_chart(request)
    print("Status Code:", response.status_code)
    content = json.loads(response.content)
    print("Success:", content.get('success'))
    if not content.get('success'):
        print("Message:", content.get('message'))
    else:
        print("Options length:", len(content.get('options')))
        print("Options snippet:", content.get('options')[:100])

if __name__ == "__main__":
    test_preview()
