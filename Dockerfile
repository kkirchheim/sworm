FROM python:3.9.4-buster
WORKDIR /usr/src/app
COPY requirements.txt ./



RUN useradd -ms /bin/bash django
#RUN chown django:django db.sqlite3
RUN chown django:django .
USER django
RUN pip install --user --no-cache-dir -r requirements.txt
#RUN chown -R django:django data/

COPY . .

EXPOSE 8000
CMD python manage.py runserver -v 3 0.0.0.0:8000

