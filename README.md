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

Spin up the server 
```shell
python manage.py runserver --insecure
```

## Populating database 
To populate the database, login as admin and visit
```
http://localhost:8000/import
```
This requires 4 files in `data/`. 