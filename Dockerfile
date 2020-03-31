FROM python:3.7-alpine

ENV FLASK_APP app.py
ENV FLASK_CONFIG production

RUN adduser -D licms
USER licms

WORKDIR /home/licms

COPY requirements requirements
COPY pkg_upd3.py ./
RUN python -m venv venv
RUN python pkg_upd3.py
RUN venv/bin/pip install -r requirements/docker.txt

COPY app_core app_core
COPY migrations migrations
COPY app.py config.py gunicorn_ini.py boot.sh ./

# run-time configuration
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
