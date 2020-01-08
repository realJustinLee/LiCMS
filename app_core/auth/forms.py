from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, ValidationError

from app_core.models import User, Gender


class LoginForm(FlaskForm):
    email = StringField('Email address', validators=[DataRequired(), Length(1, 128), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email address', validators=[DataRequired(), Length(1, 128), Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 128),
        Regexp('^[A-Za-z][A-Za-z0-9_. ]*$', 0,
               'Names must have only letters, numbers, spaces, dots or underscores')])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password_cfm', message='Passwords must match.')])
    password_cfm = PasswordField('Confirm password', validators=[DataRequired()])
    gender = SelectField('Gender', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.gender.choices = [(gender.id, gender.name) for gender in Gender.query.all()]

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class ChangePasswordFrom(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[
        DataRequired(),
        EqualTo('password_cfm', message='Passwords must match.')
    ])
    password_cfm = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Your Email address', validators=[DataRequired(), Length(1, 128), Email()])
    submit = SubmitField('Request Password Reset')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        EqualTo('password_cfm', message='Passwords must match')
    ])
    password_cfm = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')


class ChangeEmailForm(FlaskForm):
    email = StringField("New Email address", validators=[DataRequired(), Length(1, 128), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Update Email Address')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')
