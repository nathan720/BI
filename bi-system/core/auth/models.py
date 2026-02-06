from django.db import models
from django.contrib.auth.models import User, Group

class SysMenu(models.Model):
    """
    System Menu / Report Directory
    Used for: Report directory permissions
    """
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Parent Menu")
    name = models.CharField(max_length=100, verbose_name="Menu Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Permission Code")
    path = models.CharField(max_length=200, blank=True, verbose_name="Frontend Path")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Icon")
    sort_order = models.IntegerField(default=0, verbose_name="Sort Order")
    is_report_dir = models.BooleanField(default=False, verbose_name="Is Report Directory")

    class Meta:
        db_table = 'sys_menu'
        verbose_name = "System Menu"

    def __str__(self):
        return self.name

class SysRole(models.Model):
    """
    Extended Role Management
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    menus = models.ManyToManyField(SysMenu, blank=True, verbose_name="Menu Permissions")
    
    class Meta:
        db_table = 'sys_role'

    def __str__(self):
        return self.name

class SysDataPermission(models.Model):
    """
    Data Permissions
    Defines row-level security or specific data access rules
    """
    role = models.ForeignKey(SysRole, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=100, verbose_name="Target Table")
    filter_rule = models.TextField(verbose_name="SQL Filter Condition", help_text="e.g., dept_id = {user.dept_id}")
    
    class Meta:
        db_table = 'sys_data_permission'

    def __str__(self):
        return f"{self.role.name} - {self.table_name}"
