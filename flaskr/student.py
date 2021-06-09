from flaskr import app
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
student = Blueprint('student', __name__)

@student.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        return render_template("student/dashboard.html", user=current_user)
    else:
        return redirect(url_for("auth.index"))