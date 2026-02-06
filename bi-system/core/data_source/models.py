from django.db import models

class DataSource(models.Model):
    """
    Data Connection Definition
    """
    DB_TYPES = (
        ('mssql', 'Microsoft SQL Server'),
        ('mysql', 'MySQL'),
        ('postgresql', 'PostgreSQL'),
        ('oracle', 'Oracle'),
    )

    name = models.CharField(max_length=100, unique=True, verbose_name="Connection Name")
    db_type = models.CharField(max_length=20, choices=DB_TYPES, default='mssql')
    host = models.CharField(max_length=200)
    port = models.IntegerField(default=1433)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=200, help_text="Encrypted storage recommended")
    db_name = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_connection_string(self):
        # Logic to build connection string based on type
        pass

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'bi_datasource'
        verbose_name = "Data Source"
