from django.apps import apps
print("Models found:")
for m in apps.get_models():
    print(f"{m._meta.app_label}.{m.__name__}")

try:
    Report = apps.get_model('dashboard', 'Report')
    print(f"Report count: {Report.objects.count()}")
    for r in Report.objects.all():
        print(f"Report: {r.id} - {r.name}")
except LookupError:
    print("Report model not found")
