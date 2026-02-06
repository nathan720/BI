from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=50, unique=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'sys_department'

class Post(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    
    class Meta:
        db_table = 'sys_post'
