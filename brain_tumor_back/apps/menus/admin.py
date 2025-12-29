from django.contrib import admin
from .models import Menu, MenuPermission, MenuLabel, MenuRole


# Admin 등록
admin.site.register(Menu)
admin.site.register(MenuPermission)
admin.site.register(MenuLabel)
admin.site.register(MenuRole)
