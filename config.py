import os

from sqlalchemy.engine.url import URL


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'Hard_To_Guess_String')
    LICMS_ADMIN = os.environ.get('LICMS_ADMIN', '')
    LICMS_POSTS_PER_PAGE = int(os.environ.get('LICMS_POSTS_PER_PAGE', 20))
    LICMS_USERS_PER_PAGE = int(os.environ.get('LICMS_USERS_PER_PAGE', 50))
    LICMS_COMMENTS_PER_PAGE = int(os.environ.get('LICMS_COMMENTS_PER_PAGE', 30))
    LICMS_SLOW_DB_QUERY_TIME = float(os.environ.get('LICMS_SLOW_DB_QUERY_TIME', 0.5))
    LICMS_MARKDOWN_EXTENSIONS = ['abbr', 'admonition', 'attr_list', 'codehilite', 'def_list', 'extra', 'fenced_code',
                                 'footnotes', 'legacy_attrs', 'legacy_em', 'md_in_html', 'meta', 'nl2br', 'sane_lists',
                                 'smarty', 'tables', 'toc', 'wikilinks']
    LICMS_FAKER_LANG_LIST = ['en_US', 'fr_FR', 'zh_CN']
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = '[LiCMS]'
    MAIL_SENDER = 'LiCMS Admin <' + LICMS_ADMIN + '>'
    SSL_REDIRECT = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_recycle': 499}
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    credentials = {
        'username': os.environ.get('DEV_DB_USERNAME'),
        'password': os.environ.get('DEV_DB_PASSWORD'),
        'host': os.environ.get('DEV_DB_HOST'),
        'port': os.environ.get('DEV_DB_PORT'),
        'database': os.environ.get('DEV_DB_DATABASE', 'licms')}
    SQLALCHEMY_DATABASE_URI = URL.create(
        'mysql+pymysql',
        username=credentials['username'],
        password=credentials['password'],
        host=credentials['host'],
        port=credentials['port'],
        database=credentials['database'])


class TestingConfig(Config):
    TESTING = True
    # Using sqlite for testing
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DB_URL'
    ) or 'sqlite://'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_POOL_TIMEOUT = 20
    credentials = {
        'username': os.environ.get('DB_USERNAME'),
        'password': os.environ.get('DB_PASSWORD'),
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
        'database': os.environ.get('DB_DATABASE', 'licms')}
    SQLALCHEMY_DATABASE_URI = URL.create(
        'mysql+pymysql',
        username=credentials['username'],
        password=credentials['password'],
        host=credentials['host'],
        port=credentials['port'],
        database=credentials['database'])

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # handle reverse proxy server headers
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=[cls.LICMS_ADMIN],
            subject=cls.MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    SSL_REDIRECT = True if os.environ.get('DYNO') else False

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class DockerConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.INFO)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'docker': DockerConfig,
    'unix': UnixConfig,

    'default': DevelopmentConfig
}
