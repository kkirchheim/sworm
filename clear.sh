mv db.sqlite3 db.sqlite3.bak
python manage.py migrate
python manage.py createsuperuser --username admin --email ""
