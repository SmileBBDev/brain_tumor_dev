from django.db import models
from .role import Role
from .permission import Permission

# Role Permission 모델
class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete= models.CASCADE)
    permission = models.ForeignKey(
        Permission, 
        on_delete=models.CASCADE
    )   
    
    # Permission은 특정 Menu와 연결됨
    menu = models.ForeignKey(
        "menus.Menu",
        on_delete=models.CASCADE,
        null=True,   # 기존 데이터 허용
        blank=True

    )

    class Meta:
        unique_together = ("role", "permission", "menu")