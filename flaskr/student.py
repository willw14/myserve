from flaskr import app
from flask import Blueprint
from flask_login import current_user, login_required
student = Blueprint('student', __name__)

@student.route('/')
def index():
    if current_user.is_authenticated:
        print(current_user.role, current_user.role_id)

        return (
            "<p>Hello, {} {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.first_name, current_user.last_name, current_user.email, current_user.photo
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'