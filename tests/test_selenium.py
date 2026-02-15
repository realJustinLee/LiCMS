import threading
import time
import unittest

import onetimepass
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from app_core import create_app, db, fake
from app_core.models import Role, User, Gender


class SeleniumTestCase(unittest.TestCase):
    app = None
    app_context = None
    client = None
    server_thread = None

    @classmethod
    def setUpClass(cls):
        # start Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('headless')

        try:
            cls.client = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        except:
            pass

        # skip these tests if the browser could not be started
        if cls.client:
            # create the application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # suppress logging to keep unittest output clean
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # create the database and populate with some fake data
            db.create_all()
            Role.insert_roles()
            Gender.insert_genders()
            fake.users(10)
            fake.posts(10)

            # add an administrator user
            g = Gender.query.filter_by(name='Male').first()
            admin_role = Role.query.filter_by(name='Administrator').first()
            admin = User(email='john@example.com', name='john', password='cat', role=admin_role, confirmed=True,
                         gender=g)
            db.session.add(admin)
            db.session.commit()

            # start the Flask server in a thread, set port to 5001 to avoid macOS system services
            cls.server_thread = threading.Thread(target=cls.app.run, kwargs={'debug': False, 'port': 5001})
            cls.server_thread.start()

            # give the server a second to ensure it is up
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the flask server and the browser
            cls.client.get('http://localhost:5001/do/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            # destroy database
            db.drop_all()
            db.session.remove()

            # remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_admin_home_page(self):
        # navigate to home page
        self.client.get('http://localhost:5001/')
        self.assertTrue('Stranger!' in self.client.page_source)

        # navigate to login page
        self.client.find_element('link text', 'Log In').click()
        self.assertIn('Please login', self.client.page_source)

        # login
        self.client.find_element(by=By.NAME, value='email'). \
            send_keys('john@example.com')
        self.client.find_element(by=By.NAME, value='password').send_keys('cat')
        self.client.find_element(by=By.NAME, value='submit').click()
        # Wait for page to load
        time.sleep(1)
        self.assertTrue('Two Factor' in self.client.page_source)

        # 2FA
        user = User.query.filter_by(email='john@example.com').first()
        totp = onetimepass.get_totp(user.otp_secret)
        self.client.find_element(by=By.NAME, value='token').send_keys(totp)
        self.client.find_element(by=By.NAME, value='submit').click()
        # Wait for page to load
        time.sleep(1)
        self.assertTrue('john' in self.client.page_source)
