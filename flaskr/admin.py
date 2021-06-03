from flaskr import app
from flask import Blueprint
from flask_login import current_user, login_required
admin = Blueprint('admin', __name__)