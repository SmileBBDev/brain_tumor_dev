from django.db import models

# Role 모델
class Role(models.Model):
    code = models.CharField(max_length=50, unique = True) # Doctor, Nurse, Patient, LIS, RIS, Admin
    name = models.CharField(max_length=50)
    description = models.TextField(blank= True)
    created_at = models.DateTimeField(auto_now_add = True)
    
    def __str__(self) :
        return self.name

