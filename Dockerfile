FROM python:3.9.5-alpine

ENV FLASK_APP app.py
ENV FLASK_CONFIG production

USER root
RUN apk add build-base

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
