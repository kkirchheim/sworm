FROM python:3.9.4-buster
WORKDIR /usr/src/app
COPY requirements.txt ./

RUN useradd -ms /bin/bash django
RUN chown django:django .
USER django
RUN pip install --user --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD python -m gunicorn  -w 4 --bind 0.0.0.0:8000 config.wsgi
