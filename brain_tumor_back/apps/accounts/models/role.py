from django.db import models

# Role 모델
class Role(models.Model):
    code = models.CharField(max_length=50, unique = True) # Doctor, Nurse, Patient, LIS, RIS, Admin
    name = models.CharField(max_length=50)
    description = models.TextField(blank= True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now=True)
    
    permissions = models.ManyToManyField(
        "accounts.Permission",  # Permission 모델 위치에 맞게 수정
        related_name="roles",
        blank=True
    )


    def __str__(self) :
        return self.name

