from django.db import models

# Menu 모델 설계

# 메뉴 기본 정보 (path, icon, parent-child 구조)
class Menu(models.Model):
    id = models.CharField(max_length=50, primary_key=True) # ex: 'DASHBOARD'
    path = models.CharField(max_length=200, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    group_label = models.CharField(max_length=100, blank=True, null=True)
    breadcrumb_only = models.BooleanField(default=False) # 사이드바에서 보이게 하려면 false
    
    parent = models.ForeignKey(
        "self",
        related_name="children",
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.id
    

# 역할별 라벨 텍스트
class MenuLabel(models.Model):
    menu = models.ForeignKey(Menu, related_name="labels", on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # ex: 'DOCTOR', 'NURSE', 'DEFAULT'
    text = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.menu.id} - {self.role}: {self.text}"


# 접근 가능한 역할(Role)
class MenuRole(models.Model):
    menu = models.ForeignKey(Menu, related_name="roles", on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # ex: 'DOCTOR', 'NURSE', 'ADMIN'

    def __str__(self):
        return f"{self.menu.id} - {self.role}"
