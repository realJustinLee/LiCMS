FROM python:3.11-alpine

ENV FLASK_APP app.py
ENV FLASK_CONFIG production

USER root
RUN apk add build-base libffi-dev

RUN adduser -D licms
USER licms

WORKDIR /home/licms

COPY requirements requirements
RUN python -m venv venv
RUN venv/bin/pip install -U pip
RUN venv/bin/pip install wheel
RUN venv/bin/pip install -r requirements/docker.txt
# This may cause uncertainty
# RUN chmod 0755 dep_updater.sh
# RUN ./dep_updater.sh

COPY app_core app_core
COPY migrations migrations
COPY app.py config.py gunicorn_ini.py boot.sh ./

# run-time configuration
EXPOSE 5001
ENTRYPOINT ["./boot.sh"]
