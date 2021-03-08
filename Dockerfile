FROM python:3.9-alpine

ENV FLASK_APP app.py
ENV FLASK_CONFIG production

RUN adduser -D licms
USER licms

WORKDIR /home/licms

COPY requirements requirements
RUN python -m venv venv
RUN venv/bin/pip install -U pip
RUN venv/bin/pip install -r requirements/docker.txt

COPY app_core app_core
COPY migrations migrations
COPY app.py config.py gunicorn_ini.py boot.sh ./

# run-time configuration
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
