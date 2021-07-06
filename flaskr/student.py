from flaskr import app
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
student = Blueprint('student', __name__)
from flaskr.forms import AddHours
from flaskr.models import Log

@student.route('/dashboard')
@login_required
def dashboard():
    widgets = []
    return render_template("student/dashboard.html", user=current_user, widgets=widgets)

@student.route('/add-hours', methods=['GET', 'POST'])
@login_required
def add_hours():
    form = AddHours()
    form.group.choices = [(group_assoc.group.id, group_assoc.group.name) for group_assoc in current_user.groups]
    if form.validate_on_submit():
        flash(f"{form.hours.data} hour(s) logged for '{form.description.data}'", "update")
        Log.add_hours(
            current_user,
            form.group.data,
            form.hours.data,
            form.description.data,
            form.date.data,
        )
    elif form.is_submitted():
        flash("Please check that the information you've supplied is correctly formatted.", "error")
    return render_template("student/add_hours.html", user=current_user, form=form)

@student.route('/groups')
@login_required
def groups():
    return render_template("student/groups.html", user=current_user)

@student.route('/log')
@login_required
def log():
    return render_template("student/log.html", user=current_user)