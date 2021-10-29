from myserve.staff import staff as staff_blueprint
from myserve.student import student as student_blueprint
from myserve.auth import auth as auth_blueprint
from myserve.models import User
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_uploads import UploadSet, configure_uploads
import os

db = SQLAlchemy()

app = Flask(__name__)

# set some important variables - we're getting the secret key from the
# envrionment for security or just generating a random one
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['UPLOADED_DATA_DEST'] = 'uploads/'

db.init_app(app)

# setup the login manager and where we login users
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

# setup the object used to store files uploaded
data = UploadSet(name='data', extensions=('csv'))
configure_uploads(app, data)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# import the routes from the other files
app.register_blueprint(auth_blueprint)

app.register_blueprint(student_blueprint, url_prefix="/student")

app.register_blueprint(staff_blueprint, url_prefix="/staff")

# let's run the app
if __name__ == "__main__":
    app.run(debug=True)
