from django.contrib import admin
from .models import User, Role, Permission, UserRole, RolePermission

# admin 페이지 연결
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("login_id", "name", "is_active", "is_staff")
    search_fields = ("login_id", "name")

# admin.site.register(User)
# admin.site.register(Role)
# admin.site.register(Permission)
# admin.site.register(UserRole)
# admin.site.register(RolePermission)