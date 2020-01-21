from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from app_core import db
from app_core.models import Gender, User, Post


def users(count=100):
    fake = Faker()
    gender_count = Gender.query.count()
    for _ in range(count):
        g = Gender.query.offset(randint(0, gender_count - 1)).first()
        u = User(email=fake.email(),
                 name=fake.name(),
                 password='password',
                 confirmed=True,
                 location=fake.city(),
                 about_me=fake.text(),
                 member_since=fake.past_date(),
                 gender=g)
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def posts(count=100):
    fake = Faker()
    user_count = User.query.count()
    for _ in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(body=fake.text(),
                 timestamp=fake.past_date(),
                 author=u)
        db.session.add(p)
    db.session.commit()


def follow(count=100):
    user_count = User.query.count()
    for _ in range(count):
        u1 = User.query.offset(randint(0, user_count - 1)).first()
        u2 = User.query.offset(randint(0, user_count - 1)).first()
        while u2 == u1:
            u2 = User.query.offset(randint(0, user_count - 1)).first()
        u1.follow(u2)
        db.session.commit()
