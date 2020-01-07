from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user, login_user

from app_core.auth import auth
from app_core.auth.forms import LoginForm
from app_core.models import User


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_anonymous:
        flash("You've already logged in.", 'alert-info')
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            _next = request.args.get('next')
            if _next is None or not _next.startswith('/'):
                _next = url_for('main.index')
            flash('You have been logged in.', 'alert-success')
            return redirect(_next)
        form.password.errors = ['Invalid email or password.']
    return render_template('auth/login.html', form=form)


@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))
