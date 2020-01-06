from flask import Blueprint

dev_ops = Blueprint('dev_ops', __name__)

from app_core.dev_ops import views
