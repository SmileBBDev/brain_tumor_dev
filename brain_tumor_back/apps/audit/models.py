from django.db import models
from apps.accounts.models import User

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ("LOGIN_SUCCESS", "Login Success"),
        ("LOGIN_FAIL", "Login Fail"),
        ("LOGOUT", "Logout"),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null = True,
        blank= True,
    )
    
    action = models.CharField(max_length=30, choices= ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add = True)
    
    def __str__(self):
        return f"{self.action} - {self.user}"
