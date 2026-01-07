python manage.py makemigrations
python manage.py migrate

 daphne -b 127.0.0.1 -p 8000 config.asgi:application