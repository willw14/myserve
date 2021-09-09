from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from flaskr.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

from flaskr.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from flaskr.student import student as student_blueprint
app.register_blueprint(student_blueprint, url_prefix="/student")

from flaskr.staff import staff as staff_blueprint
app.register_blueprint(staff_blueprint, url_prefix="/staff")

if __name__ == "__main__":
    app.run()
