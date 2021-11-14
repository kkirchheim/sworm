# SWORM Demo Server 

Running on django. 

Create the initial database with
```shell
python manage.py migrate
```

Create a superuser
```shell
python manage.py createsuperuser --username admin --email ""
```

## Static files 
Extract static files for the admin interface
```
python manage.py collectstatic --settings=config.settings
```

Spin up the server 
```shell
python manage.py runserver --insecure
```

## Populate database 
To populate the database, login as admin and visit
```
http://localhost:8000/import
```
This requires 4 files in `data/`. 
