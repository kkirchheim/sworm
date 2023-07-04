# SWORM Demo Server

Running on Python 3.9 with django.

## Setup
Create the initial database with
```shell
python manage.py migrate
```

Create a superuser
```shell
python manage.py createsuperuser --username admin --email ""
```

[comment]: <> (### Static files)
[comment]: <> (Extract static files for the admin interface)
[comment]: <> (```)
[comment]: <> (python manage.py collectstatic --settings=config.settings)
[comment]: <> (```)

Spin up the debug server
```shell
python manage.py runserver --settings config.settings.debug
```

## Populate database
To populate the database, login as admin and visit
```
http://localhost:8000/import
```
This requires 4 files in `data/`.
