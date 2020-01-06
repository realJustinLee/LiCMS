from flask import Blueprint

auth = Blueprint('auth', __name__)

from app_core.auth import views
