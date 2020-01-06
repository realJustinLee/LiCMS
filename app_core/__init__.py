from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config

bootstrap = Bootstrap()
db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    db.init_app(app)

    # Register Error handlers
    from app_core.errors import access_forbidden, page_not_found, internal_server_error
    app.register_error_handler(403, access_forbidden)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)

    # Register Blueprints
    from app_core.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app_core.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app_core.dev_ops import dev_ops as dev_ops_blueprint
    app.register_blueprint(dev_ops_blueprint)

    return app
