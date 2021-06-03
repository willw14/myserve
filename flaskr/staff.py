from flaskr import app
from flask import Blueprint
from flask_login import current_user, login_required
staff = Blueprint('staff', __name__)