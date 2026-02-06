from django.db import models

class AuditLog(models.Model):
    ACTION_TYPES = (
        ('LOGIN', 'Login'),
        ('QUERY', 'Query Data'),
        ('EXPORT', 'Export Report'),
        ('MODIFY', 'Modify System'),
    )
    
    user_id = models.IntegerField(null=True)
    username = models.CharField(max_length=150)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target = models.CharField(max_length=255, help_text="Target object/report")
    detail = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sys_audit_log'
