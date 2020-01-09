from datetime import datetime

from flask import render_template, redirect, url_for

from app_core.main import main
from app_core.models import User


@main.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico', _external=True))


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', current_time=datetime.utcnow())


@main.route('/user/<user_id>')
def user(user_id):
    _user = User.query.filter_by(id=user_id).first_or_404()
    return render_template('user.html', user=_user)
