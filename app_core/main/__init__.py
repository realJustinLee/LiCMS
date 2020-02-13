from flask import Blueprint

main = Blueprint('main', __name__)

from app_core.main import views, errors
from app_core.models import Permission


@main.app_context_processor
def inject_permission():
    return dict(Permission=Permission)
