import base64
import hashlib
import os
from datetime import datetime, timezone, timedelta

import bleach
import jwt
import onetimepass
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash

from app_core import db, login_manager
from app_core.exceptions import ValidationError


class Gender(db.Model):
    __tablename__ = 'genders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True)
    users = db.relationship('User', backref='gender', lazy='dynamic')

    @staticmethod
    def insert_genders():
        genders = {
            "Male",
            "Female",
            "Transgender(MTF)",
            "Transgender(FTM)",
            "Rather not say"
        }
        for g in genders:
            gender = Gender.query.filter_by(name=g).first()
            if gender is None:
                gender = Gender(name=g)
                db.session.add(gender)
        db.session.commit()

    def __repr__(self):
        return '<Gender %r>' % self.name


class Permission:
    FOLLOW = pow(2, 0)
    COMMENT = pow(2, 1)
    WRITE = pow(2, 2)
    MODERATE = pow(2, 3)
    ADMIN = pow(2, 4)
    FILE_READ = pow(2, 5)
    FILE_WRITE = pow(2, 6)
    FILE_ADMIN = pow(2, 7)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT,
                     Permission.WRITE, Permission.FILE_READ],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE,
                          Permission.FILE_READ, Permission.FILE_WRITE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN, Permission.FILE_READ,
                              Permission.FILE_WRITE, Permission.FILE_ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for permission in roles[r]:
                role.add_permission(permission)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, permission):
        if not self.has_permission(permission):
            self.permissions += permission

    def remove_permission(self, permission):
        if self.has_permission(permission):
            self.permissions -= permission

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, permission):
        return self.permissions & permission == permission

    def __repr__(self):
        return '<Role %r>' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True, index=True)
    avatar_hash = db.Column(db.String(32))
    password_hash = db.Column(db.String(256))
    otp_secret = db.Column(db.String(16))
    confirmed = db.Column(db.Boolean, default=False)
    location = db.Column(db.String(128))
    about_me = db.Column(db.Text)
    member_since = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    last_seen = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    gender_id = db.Column(db.Integer, db.ForeignKey('genders.id'))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.otp_secret is None:
            # generate a random secret
            self.generate_otp_secret()
        if self.role is None:
            if self.email == current_app.config['LICMS_ADMIN'].lower():
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
        self.follow(self)

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    def generate_otp_secret(self):
        self.otp_secret = base64.b32encode(os.urandom(10)).decode('utf-8')

    def get_totp_uri(self):
        return 'otpauth://totp/LiCMS:{0}?secret={1}&issuer=LiCMS'.format(self.email, self.otp_secret)

    def verify_totp(self, token):
        return onetimepass.valid_totp(token, self.otp_secret)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=600):
        payload = {'confirm': self.id, 'exp': datetime.now(timezone.utc) + timedelta(seconds=expiration)}
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")

    def confirm(self, token, leeway=10):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], leeway=leeway, algorithms=["HS256"])
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=600):
        payload = {'reset': self.id, 'exp': datetime.now(timezone.utc) + timedelta(seconds=expiration)}
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")

    @staticmethod
    def reset_password(token, new_password, leeway=10):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], leeway=leeway, algorithms=["HS256"])
        except:
            return False
        user = db.session.get(User, data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_email_change_token(self, new_email, expiration=600):
        payload = {'change_email': self.id, 'new_email': new_email,
                   'exp': datetime.now(timezone.utc) + timedelta(seconds=expiration)}
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")

    def change_email(self, token, leeway=10):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], leeway=leeway, algorithms=["HS256"])
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True

    def generate_two_factor_reset_token(self, expiration=600):
        payload = {'reset_2FA': self.id, 'exp': datetime.now(timezone.utc) + timedelta(seconds=expiration)}
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")

    def reset_two_factor(self, token, leeway=10):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], leeway=leeway, algorithms=["HS256"])
        except:
            return False
        if data.get('reset_2FA') != self.id:
            return False
        self.generate_otp_secret()
        db.session.add(self)
        return True

    def can(self, permission):
        return self.role is not None and self.role.has_permission(permission)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def ping(self):
        self.last_seen = datetime.now(timezone.utc)
        db.session.add(self)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        _hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=_hash, size=size, default=default, rating=rating)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', user_id=self.id),
            'name': self.name,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'gender': self.gender.name,
            'posts_url': url_for('api.get_user_posts', user_id=self.id),
            'followed_posts_url': url_for('api.get_user_followed_posts', user_id=self.id),
            'post_count': self.posts.count()
        }
        return json_user

    def generate_auth_token(self, expiration=600):
        payload = {'user_id': self.id, 'exp': datetime.now(timezone.utc) + timedelta(seconds=expiration)}
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")

    @staticmethod
    def verify_auth_token(token, leeway=10):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], leeway=leeway, algorithms=["HS256"])
        except:
            return None
        return db.session.get(User, data['user_id'])

    def __repr__(self):
        return '<User %r>' % self.name


class AnonymousUser(AnonymousUserMixin):
    def can(self, permission):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @staticmethod
    def on_changed_body(target, value, old_value, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, extensions=current_app.config['LICMS_MARKDOWN_EXTENSIONS'], output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', post_id=self.id),
            'title': self.title,
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', user_id=self.author_id),
            'comments_url': url_for('api.get_post_comments', post_id=self.id),
            'comment_count': self.comments.count()
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        title = json_post.get('title')
        body = json_post.get('body')
        if title is None or title == '':
            raise ValidationError('post does not have a title')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(title=title, body=body)


db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc))
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, old_value, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, extensions=current_app.config['LICMS_MARKDOWN_EXTENSIONS'], output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', comment_id=self.id),
            'post_url': url_for('api.get_post', post_id=self.post_id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', user_id=self.author_id),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Paste(db.Model):
    __tablename__ = "pastes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_json(self):
        json_paste = {
            # 'url': url_for('api.get_paste', paste_id=self.id),
            'title': self.name,
            'body': self.body,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', user_id=self.author_id),
        }
        return json_paste

    @staticmethod
    def from_json(json_paste):
        title = json_paste.get('title')
        body = json_paste.get('body')
        if title is None or title == '':
            raise ValidationError('paste does not have a title')
        if body is None or body == '':
            raise ValidationError('paste does not have a body')
        return Paste(title=title, body=body)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    file_hash = db.Column(db.String(32))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_json(self):
        json_file = {
            # 'url': url_for('api.get_file', file_id=self.id),
            'name': self.name,
            'file_hash': self.file_hash,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', user_id=self.author_id),
        }
        return json_file

    @staticmethod
    def from_json(json_file):
        name = json_file.get('name')
        file_hash = json_file.get('file_hash')
        if name is None or name == '':
            raise ValidationError('paste does not have a title')
        if file_hash is None or file_hash == '' or len(file_hash) > 32:
            raise ValidationError('paste does not have a body')
        return Paste(name=name, file_hash=file_hash)
