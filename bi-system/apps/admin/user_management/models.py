from django.db import models
from django.contrib.auth.models import User
from apps.admin.organization.models import Department, Post

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    posts = models.ManyToManyField(Post, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    security_level = models.IntegerField(default=1, help_text="User security clearance level")

    class Meta:
        db_table = 'sys_user_profile'
