from django.db import models
from .role import Role
from .permission import Permission

# Role Permission 모델
class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete= models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ("role", "permission")