from datetime import datetime

from flask import render_template, redirect, url_for

from app_core.main import main


@main.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico', _external=True))


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', current_time=datetime.utcnow())
