from django.db import models
from django.contrib.auth.models import(
    BaseUserManager,   
    AbstractBaseUser,
    PermissionsMixin,
)

# 최상위 관리자 모델 
class UserManager(BaseUserManager):
    def create_user(self, login_id, password=None, **extra_fields):
        if not login_id:
            raise ValueError("ID는 필수 항목")
        
        user = self.model(login_id = login_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login_id, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        
        return self.create_user(login_id, password, **extra_fields)


ROLE_CHOICES = (
    ("ADMIN", "관리자"),
    ("DOCTOR", "의사"),
    ("NURSE", "간호사"),
    ("RIS", "영상의학과"),
    ("LIS", "검사실"),
    ("PATIENT", "환자"),
)

# User 모델
class User(AbstractBaseUser, PermissionsMixin):
    login_id = models.CharField(max_length=50, unique = True)
    name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null= True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="PATIENT")
        
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 충돌 방지 : related_name 지정
    groups = models.ManyToManyField(
        "auth.Group",
        related_name= "custom_user_groups",
        blank= True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions",
        blank=True,
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = "login_id"
    REQUIRED_FIELDS = ["name"]
    
    def __str__(self):
        return self.login_id