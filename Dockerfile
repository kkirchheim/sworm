FROM python:3.9.4-buster
WORKDIR /usr/src/app
COPY requirements.txt ./

RUN useradd -ms /bin/bash django
RUN chown django:django .
USER django
RUN pip install --user --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD gunicorn config.wsgi

