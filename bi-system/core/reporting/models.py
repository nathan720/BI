from django.db import models
from core.dataset.models import DataSet

class ReportDirectory(models.Model):
    """
    Report Directory for hierarchical organization
    """
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bi_report_directory'
        verbose_name = "Report Directory"
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name

class Report(models.Model):
    """
    Report Definition
    """
    PLATFORM_TYPES = (
        ('pc', 'PC Browser'),
        ('mobile', 'Mobile App/H5'),
    )

    name = models.CharField(max_length=100)
    # Deprecated: use directories instead. Kept for migration.
    directory = models.ForeignKey(ReportDirectory, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_legacy')
    directories = models.ManyToManyField(ReportDirectory, blank=True, related_name='reports', verbose_name="所属目录")
    code = models.CharField(max_length=50, unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_TYPES, default='pc')
    is_visible = models.BooleanField(default=True, verbose_name="Display in List")
    
    # External URL Support
    external_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="External URL")
    
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '已发布'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="状态")

    # Link to a dataset (can be multiple in advanced systems, simplifying to one or M2M)
    datasets = models.ManyToManyField(DataSet, blank=True)
    
    # Template Configuration (JSON for layout, chart types, etc.)
    # Changed to TextField for MSSQL compatibility
    template_config = models.TextField(default='{}', verbose_name="Visual Template Config")
    
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bi_report'
        verbose_name = "Report"
        ordering = ['sort_order', 'id']

class ReportFunctionMapping(models.Model):
    """
    Report Mapping
    Maps report page to backend execution function
    """
    report = models.OneToOneField(Report, on_delete=models.CASCADE, related_name='backend_mapping')
    
    # Path to the python function/module that handles specific logic if standard engine isn't enough
    # e.g., "apps.custom_logic.finance.monthly_report_processor"
    function_path = models.CharField(max_length=255, verbose_name="Backend Function Path")
    
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'bi_report_mapping'
        verbose_name = "Report Function Mapping"

class ScheduledTask(models.Model):
    """
    Scheduler for reports/data updates
    """
    name = models.CharField(max_length=100)
    cron_expression = models.CharField(max_length=100, help_text="Standard Cron format")
    task_type = models.CharField(max_length=50, choices=[('email', 'Send Email'), ('cache', 'Refresh Cache')])
    target_config = models.TextField(default='{}', help_text="Config for the task (e.g., report_id, email_list)")
    
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'bi_scheduled_task'
