from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from app_core import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    # !VITAL! DO NOT remove _get_current_object()
    app = current_app._get_current_object()
    msg = Message(
        app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
        sender=app.config['MAIL_SENDER'],
        recipients=[to]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    _thread = Thread(target=send_async_email, args=[app, msg])
    _thread.start()
    return _thread
