from flask import g, jsonify
from flask_httpauth import HTTPBasicAuth

from app_core.api import api
from app_core.api.errors import unauthorized, forbidden
from app_core.models import User

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    _user = User.query.filter_by(email=email_or_token.lower()).first()
    if not _user:
        return False
    g.current_user = _user
    g.token_used = False
    return _user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')
    return None


@api.route('/tokens/', methods=['POST'])
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(expiration=600), 'expiration': 600})
