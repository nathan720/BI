from django.db import models
from core.data_source.models import DataSource

class DataSet(models.Model):
    """
    Dataset Definition
    Executes SQL through selected connection
    """
    name = models.CharField(max_length=100, unique=True)
    datasource = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    sql_script = models.TextField(verbose_name="SQL Query")
    
    # Stores JSON config for parameters (e.g., [{'name': 'start_date', 'type': 'date'}])
    # Changed to TextField for MSSQL compatibility
    params_config = models.TextField(default='{}', blank=True, verbose_name="Parameters Configuration")
    
    # Caches the result structure (columns, types)
    metadata = models.TextField(default='{}', blank=True, verbose_name="Result Metadata")
    
    # Flag to distinguish datasets created inside a specific report design session
    is_report_specific = models.BooleanField(default=False, verbose_name="Created in Report")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'bi_dataset'
        verbose_name = "Data Set"
