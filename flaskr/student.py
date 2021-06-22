from flaskr import app
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
student = Blueprint('student', __name__)
from flaskr.forms import AddHours

@student.route('/dashboard')
@login_required
def dashboard():
    return render_template("student/dashboard.html", user=current_user)

@student.route('/add-hours', methods=['GET', 'POST'])
@login_required
def add_hours():
    form = AddHours()
    form.group.choices = [(group.id, group.name) for group in current_user.groups]
    if form.validate_on_submit():
        flash(f"{form.hours.data} hour(s) logged for '{form.description.data}'", "update")
    elif form.is_submitted():
        flash("Please check that the information you've supplied is correctly formatted.", "error")
    return render_template("student/add_hours.html", user=current_user, form=form)