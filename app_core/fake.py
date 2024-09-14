from random import randint

from faker import Faker
from flask import current_app
from sqlalchemy.exc import IntegrityError

from app_core import db
from app_core.models import Gender, User, Post, Comment


def users(count=100):
    fake = Faker(current_app.config['LICMS_FAKER_LANG_LIST'])
    gender_count = Gender.query.count()
    for _ in range(count):
        g = Gender.query.offset(randint(0, gender_count - 1)).first()
        u = User(email=fake.email(),
                 name=fake.name(),
                 password='password',
                 confirmed=True,
                 location=fake.city(),
                 about_me=fake.text(),
                 member_since=fake.past_datetime(),
                 gender=g)
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def posts(count=100):
    fake = Faker(current_app.config['LICMS_FAKER_LANG_LIST'])
    user_count = User.query.count()
    for _ in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(title=fake.text(100),
                 body=fake.text(1000),
                 timestamp=fake.past_datetime(),
                 author=u)
        db.session.add(p)
    db.session.commit()


def follows(count=100):
    user_count = User.query.count()
    for _ in range(count):
        u1 = User.query.offset(randint(0, user_count - 1)).first()
        u2 = User.query.offset(randint(0, user_count - 1)).first()
        while u2 == u1:
            u2 = User.query.offset(randint(0, user_count - 1)).first()
        u1.follow(u2)
        db.session.commit()


def comments(count=100):
    fake = Faker(current_app.config['LICMS_FAKER_LANG_LIST'])
    user_count = User.query.count()
    post_count = Post.query.count()
    for _ in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post.query.offset(randint(0, post_count - 1)).first()
        c = Comment(body=fake.text(200),
                    timestamp=fake.past_datetime(),
                    author=u,
                    post=p)
        db.session.add(c)
    db.session.commit()
