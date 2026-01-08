python manage.py makemigrations


python .\manage.py migrate accounts
python .\manage.py migrate menus   
python manage.py migrate



migrate 순서가 중요하다. 
1. accounts_permission
2. accounts_role
3. menus_menu
4. accounts_role_permissions
5. menus_menupermission



 daphne -b 127.0.0.1 -p 8000 config.asgi:application






