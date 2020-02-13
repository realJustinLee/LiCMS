import re
import unittest

import onetimepass

from app import create_app, db
from app_core.models import User, Role, Gender


class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        Gender.insert_genders()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Stranger' in response.get_data(as_text=True))

    def test_register_and_login(self):
        # register a new account
        g = Gender.query.filter_by(name='Male').first()
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'name': 'john',
            'password': 'cat',
            'password_cfm': 'cat',
            'gender': g.id
        })
        self.assertEqual(response.status_code, 302)

        # login with the new account
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat'
        })
        self.assertEqual(response.status_code, 302)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # redirect to 2FA
        response = self.client.get(url)
        self.assertTrue(re.search('Authentication Code', response.get_data(as_text=True)))

        # submit Authentication Code
        user = User.query.filter_by(email='john@example.com').first()
        totp = onetimepass.get_totp(user.otp_secret)
        response = self.client.post(url, data={'token': totp}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('<h1>Hello, john!</h1>' in response.get_data(as_text=True))
        self.assertTrue('<h3>You have <b>NOT</b> confirmed your account yet.</h3>' in response.get_data(as_text=True))

        # send a confirmation token
        token = user.generate_confirmation_token()
        response = self.client.get('/auth/confirm/{}'.format(token), follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have confirmed your account' in response.get_data(as_text=True))

        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have been logged out' in response.get_data(as_text=True))
