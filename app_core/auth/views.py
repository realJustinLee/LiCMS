from datetime import datetime

from dateutil.tz import tz
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required, logout_user, login_user

from app_core import db
from app_core.auth import auth
from app_core.auth.forms import LoginForm, RegistrationForm
from app_core.email import send_email
from app_core.models import User, Gender


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


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(),
            username=form.username.data,
            password=form.password.data,
            gender=Gender.query.get(form.gender.data)
        )
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token,
                   current_time=datetime.now(tz.gettz('CST')).strftime("%B %d, %Y %H:%M CST"))
        flash('A confirmation email has been sent to you by email.', 'alert-primary')
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'alert-success')
    else:
        flash('The confirmation link is invalid or has expired.', 'alert-danger')
    return redirect(url_for('main.index'))
