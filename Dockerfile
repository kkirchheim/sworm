FROM python:3.9.4-buster
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY . .

RUN useradd -ms /bin/bash django
RUN chown django:django db.sqlite3
RUN chown django:django .
RUN chown -R django:django data/svm/

USER django

RUN pip install --user --no-cache-dir -r requirements.txt

EXPOSE 5006
CMD python manage.py runserver -v 3 0.0.0.0:5006

