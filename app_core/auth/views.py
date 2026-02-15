from datetime import datetime
from io import BytesIO

import pyqrcode
from dateutil.tz import tz
from flask import render_template, flash, redirect, url_for, request, session, abort
from flask_login import current_user, login_required, logout_user, login_user

from app_core import db
from app_core.auth import auth
from app_core.auth.forms import LoginForm, RegistrationForm, ChangePasswordFrom, PasswordResetRequestForm, \
    PasswordResetForm, ChangeEmailForm, TwoFactorForm, TwoFactorResetForm
from app_core.email import send_email
from app_core.models import User, Gender


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))
    return None


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous:
        flash('Your should have an account before you could confirm it.', 'alert-danger')
        return redirect(url_for('main.index'))
    if current_user.confirmed:
        flash('Your account has already been confirmed.', 'alert-info')
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_anonymous:
        flash("You've already logged in.", 'alert-info')
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            # Do NOT put user_id into the session, in case you want to log the user in.
            session['email'] = user.email
            _next = request.args.get('next')
            return redirect(url_for('auth.two_factor', next=_next, remember=form.remember_me.data))
        form.password.errors = ['Invalid email or password.']
    return render_template('auth/login.html', form=form)


@auth.route('/two-factor', methods=['GET', 'POST'])
def two_factor():
    if 'email' not in session:
        abort(404)
    user = User.query.filter_by(email=session['email'].lower()).first()
    if user is None:
        abort(404)
    form = TwoFactorForm()
    if form.validate_on_submit():
        if user.verify_totp(form.token.data):
            del session['email']
            remember = request.args.get('remember')
            if remember is None:
                remember = False
            login_user(user, remember=remember)
            _next = request.args.get('next')
            if _next is None or not _next.startswith('/'):
                _next = url_for('main.index')
            flash('You have been logged in.', 'alert-success')
            return redirect(_next)
        form.token.errors = ['Invalid authentication token.']
    return render_template('auth/two_factor.html', form=form)


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
            name=form.name.data,
            password=form.password.data,
            gender=db.session.get(Gender, form.gender.data)
        )
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token,
                   current_time=datetime.now(tz.gettz('CST')).strftime("%B %d, %Y %H:%M CST"))
        flash('A confirmation email has been sent to you by email.', 'alert-primary')
        db.session.add(user)
        db.session.commit()
        # Redirect to the two-factor auth page, passing username in session
        # Do NOT put user_id into the session, unless you wanna log the user in.
        session['email'] = user.email
        return redirect(url_for('auth.two_factor_setup'))
    return render_template('auth/register.html', form=form)


@auth.route('/two-factor-setup', methods=['GET', 'POST'])
def two_factor_setup():
    if 'email' not in session:
        abort(404)
    user = User.query.filter_by(email=session['email'].lower()).first()
    if user is None:
        abort(404)
    form = TwoFactorForm()
    if form.validate_on_submit():
        if user.verify_totp(form.token.data):
            # For enhanced security, remove email from session
            del session['email']
            db.session.commit()
            flash("Congratulations! You've finished setting up two factor authentication.", 'alert-success')
            return redirect(url_for('auth.login'))
        flash('Invalid authentication code.', 'alert-danger')
    # Since this page contains the sensitive QR Code, make sure the browser does NOT cache it
    return render_template('auth/two_factor_setup.html', form=form), 200, {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}


@auth.route('/2FA-QR-Code')
def two_factor_qr_code():
    if 'email' not in session:
        abort(404)
    user = User.query.filter_by(email=session['email'].lower()).first()
    if user is None:
        abort(404)
    # Render QR Code for Authenticator app
    url = pyqrcode.create(user.get_totp_uri())
    stream = BytesIO()
    url.svg(stream, scale=5)
    return stream.getvalue(), 200, {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'}


@auth.route('/change-two-factor')
@login_required
def change_two_factor():
    current_user.generate_otp_secret()
    db.session.add(current_user)
    db.session.commit()
    session['email'] = current_user.email
    return redirect(url_for('auth.two_factor_setup'))


@auth.route('/reset-2FA', methods=['GET', 'POST'])
def tow_factor_reset_request():
    if not current_user.is_anonymous:
        flash("Since you have access to your 2FA, you don't need to reset it. You can change it directly.",
              'alert-info')
        return redirect(url_for('auth.change_two_factor'))
    form = TwoFactorResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            token = user.generate_two_factor_reset_token()
            send_email(user.email, 'Reset Your 2FA', 'auth/email/reset_two_factor', user=user, token=token,
                       current_time=datetime.now(tz.gettz('CST')).strftime("%B %d, %Y %H:%M CST"))
            flash('An email with instructions to reset your 2FA has been sent to you.', 'alert-primary')
        flash('Invalid email or password.', 'alert-danger')
    return render_template('auth/reset_tow_factor.html', form=form)


@auth.route('/reset-2FA/<token>', methods=['GET', 'POST'])
def tow_factor_reset(token):
    if not current_user.is_anonymous:
        flash('Invalid Request.')
        return redirect(url_for('main.index'))
    form = TwoFactorResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            if user.reset_two_factor(token):
                session['email'] = user.email
                return redirect(url_for('auth.two_factor_setup'))
            else:
                flash('The 2FA reset link is invalid or has expired.', 'alert-danger')
                return redirect(url_for('main.index'))
        flash('Invalid email or password.', 'alert-danger')
    return render_template('auth/reset_tow_factor.html', form=form)


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


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token,
               current_time=datetime.now(tz.gettz('CST')).strftime("%B %d, %Y %H:%M CST"))
    flash('A new confirmation email has been sent to you by email.', 'alert-primary')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordFrom()
    if form.validate_on_submit():
        if current_user.verify_password(form.current_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.', 'alert-success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid Password.', 'alert-danger')
    return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        flash("Since you know your current password, you don't need to reset it. You can change it directly.",
              'alert-info')
        return redirect(url_for('auth.change_password'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password', 'auth/email/reset_password', user=user, token=token,
                       current_time=datetime.now(tz.gettz('CST')).strftime("%B %d, %Y %H:%M CST"))
        flash('An email with instructions to reset your password has been sent to you.', 'alert-primary')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        flash('Invalid Request.')
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('The password reset link is invalid or has expired.', 'alert-danger')
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address', 'auth/email/change_email', user=current_user,
                       token=token, current_time=datetime.now(tz.gettz('CST')).strftime("%B %d, %Y %H:%M CST"))
            flash('An email with instructions to confirm your new email address has been sent to ' + new_email + '.',
                  'alert-info')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.', 'alert_danger')
    return render_template('auth/change_email.html', form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('Your email address has been updated.')
    else:
        flash('Invalid Request.')
    return redirect(url_for('main.index'))
