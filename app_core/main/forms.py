from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms.fields import StringField, TextAreaField, SubmitField, SelectField, BooleanField, DateTimeLocalField
from wtforms.validators import Length, DataRequired, Email, ValidationError, Optional

from app_core.models import Gender, Role, User


class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[Length(1, 128)])
    gender = SelectField('Gender', validators=[DataRequired()], coerce=int)
    location = StringField('Location', validators=[Length(0, 128)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.gender.choices = [(gender.id, gender.name) for gender in Gender.query.all()]


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 128), Email()])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Name', validators=[Length(1, 128)])
    gender = SelectField('Gender', validators=[DataRequired()], coerce=int)
    location = StringField('Location', validators=[Length(0, 128)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.gender.choices = [(gender.id, gender.name) for gender in Gender.query.all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class PostForm(FlaskForm):
    title = StringField('Title here', validators=[DataRequired()])
    body = PageDownField('Content here', validators=[DataRequired()])
    submit = SubmitField('Submit')


class CommentForm(FlaskForm):
    body = PageDownField('Enter your comment', validators=[DataRequired()])
    submit = SubmitField('Submit')


class PasteForm(FlaskForm):
    title = StringField('Title here')
    body = TextAreaField('Just paste', validators=[DataRequired()])
    expiry = DateTimeLocalField('Expiry date', validators=[Optional()])
    disabled = BooleanField('Disabled')
    submit = SubmitField('Submit')
