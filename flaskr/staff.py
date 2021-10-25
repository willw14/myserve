from flask_wtf.form import _is_submitted
from flaskr import app
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from flaskr.forms import AddHours, JoinGroups, CreateGroup
from flaskr.models import STAFF_ID, ADMIN_ID, User, Log, Award, Group
from flaskr.decorators import permission_required

staff = Blueprint('staff', __name__)

@staff.route('/dashboard')
@login_required
@permission_required(STAFF_ID)
def dashboard():
    return render_template("staff/dashboard.html", user=current_user)

@staff.route('/students')
@login_required
@permission_required(STAFF_ID)
def students():
    students = User.get_students()
    return render_template("staff/students.html", user=current_user, students=students)

@staff.route('/students/log/<int:id>')
@login_required
@permission_required(STAFF_ID)
def student_log(id):
    student = User.load_by_id(id)
    if not student:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    return render_template("staff/student_log.html", user=current_user, student=student)

@staff.route('/students/groups/<int:id>')
@login_required
@permission_required(STAFF_ID)
def student_groups(id):
    student = User.load_by_id(id)
    if not student:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    return render_template("staff/student_groups.html", user=current_user, student=student)

@staff.route('/students/groups/<int:student_id>/<int:group_id>')
@login_required
@permission_required(STAFF_ID)
def student_group_detail(student_id, group_id):
    student = User.load_by_id(student_id)
    group = Group.load(group_id)
    if not group or not student:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))
    elif group not in student.groups_proxy:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    return render_template("staff/student_group_detail.html", user=current_user, student=student, group=group)

@staff.route('/edit-hours/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(STAFF_ID)
def edit_hours(id):
    item = Log.load(id)
    student = User.load_by_id(item.user_id)
    if not item:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    form = AddHours()
    form.group.choices = student.get_group_options() + [(None, "No Group")]
    form.teacher.choices = User.get_teacher_options()

    if request.method == 'GET':
        form.group.data = item.group_id
        form.teacher.data = item.teacher_id
        form.hours.data = item.time
        form.description.data = item.description
        form.date.data = item.date
    elif form.validate_on_submit():
        if form.submit.data:
            item.edit_hours(
                form.group.data,
                form.teacher.data,
                form.hours.data,
                form.description.data,
                form.date.data,
                status = 2
            )
            flash(f"'{form.description.data}' was updated successfully.", "update")
        elif form.delete.data:
            item.delete()
            flash(f"'{form.description.data}' was deleted successfully.", "update")
        return redirect(url_for('staff.student_log', id=student.id))
    elif form.is_submitted():
        flash("Please check the information you've supplied.", "error")
    return render_template("staff/edit_hours.html", user=current_user, form=form, student=student)

@staff.route('/groups', methods=['GET', 'POST'])
@login_required
@permission_required(STAFF_ID)
def groups():
    form = CreateGroup()
    if request.method == "POST" and form.validate_on_submit():
        new_group = Group.create(form.name.data)
        current_user.join_groups([new_group.id])
    return render_template("staff/groups.html", user=current_user, form=form)

@staff.route('/groups/edit', methods=['GET', 'POST'])
@login_required
@permission_required(STAFF_ID)
def edit_groups():
    form = JoinGroups()
    form.groups.choices = Group.get_group_options()
    disabled_groups = current_user.get_disabled_groups()
    current_groups = [str(group.group_id) for group in current_user.groups]

    if request.method == 'GET':
        form.groups.data = current_groups
    elif form.is_submitted:
        #we add the disabled groups back in incase the user has altered the html and tried to leave a group
        #that they're the only teacher left in
        form.groups.data.extend([str(group) for group in disabled_groups])

        groups_join = set(form.groups.data) - set(current_groups)
        groups_leave = set(current_groups) - set(form.groups.data)
        current_user.join_groups(groups_join)
        current_user.leave_groups(groups_leave)
        flash(f"Your groups were updated successfully.", "update")
        return redirect(url_for('staff.groups'))
    return render_template("staff/edit_groups.html", user=current_user, form=form, disabled_groups=disabled_groups)

@staff.route('/groups/<int:id>')
@login_required
@permission_required(STAFF_ID)
def group_detail(id):
    group = Group.load(id)

    return render_template("staff/group_detail.html", user=current_user, group=group)

@staff.route('/groups/delete/<int:id>')
@login_required
@permission_required(STAFF_ID)
def group_delete(id):
    group = Group.load(id)
    for student in group.get_students():
        for item in group.get_user_log(student.user):
            item.delete()
        student.user.leave_groups([group.id])
    
    for teacher in group.get_teachers():
        teacher.leave_groups([group.id])
    
    group.delete()
    flash(f"{group.name} was deleted successfully.", "updates")

    return redirect(url_for("staff.groups"))

@staff.route('/other-hours')
@login_required
@permission_required(STAFF_ID)
def other_hours():
    return render_template("staff/other_hours.html", user=current_user)