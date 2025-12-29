from django.db import models
from .menu import Menu
from apps.accounts.models.permission import Permission

# 메뉴와 Permission 매핑 (권한 기반 접근 제어)
class MenuPermission(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ("menu", "permission")