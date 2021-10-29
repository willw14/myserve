from typing import List
from sqlalchemy.sql.sqltypes import String
from myserve import db, app, data
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from myserve.forms import AddHours, JoinGroups, CreateGroup, UserUpload
from myserve.models import USER_ROLE, User, Log, Group
from myserve.decorators import permission_required
import os

staff = Blueprint('staff', __name__)


@staff.route('/dashboard')
@login_required
@permission_required(USER_ROLE["staff"])
def dashboard():
    # sort the groups a user is in by their size
    groups = sorted(
        current_user.groups_proxy,
        key=lambda x: x.get_no_students(),
        reverse=True)

    # shorten the list if it's too big
    if len(groups) >= 5:
        groups = groups[:5]

    top_students = User.get_top_students()

    return render_template(
        "staff/dashboard.html",
        user=current_user,
        groups=groups,
        students=top_students)


@staff.route('/students')
@login_required
@permission_required(USER_ROLE["staff"])
def students():
    students = User.get_students()
    return render_template(
        "staff/students.html",
        user=current_user,
        students=students)


@staff.route('/students/log/<int:id>')
@login_required
@permission_required(USER_ROLE["staff"])
def student_log(id):
    student = User.load_by_id(id)
    if not student:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    return render_template(
        "staff/student_log.html",
        user=current_user,
        student=student)


@staff.route('/students/groups/<int:id>')
@login_required
@permission_required(USER_ROLE["staff"])
def student_groups(id):
    student = User.load_by_id(id)
    if not student:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    return render_template(
        "staff/student_groups.html",
        user=current_user,
        student=student)


@staff.route('/students/groups/<int:student_id>/<int:group_id>')
@login_required
@permission_required(USER_ROLE["staff"])
def student_group_detail(student_id, group_id):
    student = User.load_by_id(student_id)
    group = Group.load(group_id)
    if not group or not student:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))
    elif group not in student.groups_proxy:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    return render_template(
        "staff/student_group_detail.html",
        user=current_user,
        student=student,
        group=group)


@staff.route('/edit-hours/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(USER_ROLE["staff"])
def edit_hours(id):
    item = Log.load(id)
    student = User.load_by_id(item.user_id)
    if not item:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    form = AddHours()
    # add in the choices for this user to the form
    form.group.choices = student.get_group_options() + [(None, "No Group")]
    form.teacher.choices = User.get_teacher_options()

    # update the form with what they've recorded for this object in the past
    if request.method == 'GET':
        form.group.data = str(item.group_id)
        form.teacher.data = str(item.teacher_id)
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
                status=2
            )
            flash(
                f"'{form.description.data}' was updated successfully.",
                "update")

        elif form.delete.data:
            # deletes the object if they click the delete button
            item.delete()
            flash(
                f"'{form.description.data}' was deleted successfully.",
                "update")
        return redirect(url_for('staff.student_log', id=student.id))

    elif form.is_submitted():
        flash("Please check the information you've supplied.", "error")

    return render_template(
        "staff/edit_hours.html",
        user=current_user,
        form=form,
        student=student)


@staff.route('/groups', methods=['GET', 'POST'])
@login_required
@permission_required(USER_ROLE["staff"])
def groups():
    form = CreateGroup()

    # if they've made a new group, we will set it up and add them to it
    if request.method == "POST" and form.validate_on_submit():
        new_group = Group.create(form.name.data)
        current_user.join_groups([new_group.id])
        flash(f"The group {new_group.name} was added successfuly.", "update")

    return render_template("staff/groups.html", user=current_user, form=form)


@staff.route('/groups/edit', methods=['GET', 'POST'])
@login_required
@permission_required(USER_ROLE["staff"])
def edit_groups():
    form = JoinGroups()
    form.groups.choices = Group.get_group_options()
    disabled_groups = current_user.get_disabled_groups()
    current_groups = [str(group.group_id) for group in current_user.groups]

    if request.method == 'GET':
        form.groups.data = current_groups

    elif form.is_submitted:
        # we add the disabled groups back incase the user has altered the html
        # and tried to leave a group that they're the only teacher left in
        form.groups.data.extend([str(group) for group in disabled_groups])

        # find the groups which they've joined and left by comparing the form
        # with the database
        groups_join = set(form.groups.data) - set(current_groups)
        groups_leave = set(current_groups) - set(form.groups.data)

        current_user.join_groups(groups_join)
        current_user.leave_groups(groups_leave)

        flash(f"Your groups were updated successfully.", "update")
        return redirect(url_for('staff.groups'))

    return render_template(
        "staff/edit_groups.html",
        user=current_user,
        form=form,
        disabled_groups=disabled_groups)


@staff.route('/groups/<int:id>')
@login_required
@permission_required(USER_ROLE["staff"])
def group_detail(id):
    group = Group.load(id)
    if not group:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    return render_template(
        "staff/group_detail.html",
        user=current_user,
        group=group)


@staff.route('/groups/delete/<int:id>')
@login_required
@permission_required(USER_ROLE["staff"])
def group_delete(id):
    group = Group.load(id)
    if not group:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    # remove all the users in the group
    for student in group.get_students():
        group.remove_user(student.user)

    for teacher in group.get_teachers():
        group.remove_user(teacher)

    # delete the group
    group.delete()
    flash(f"{group.name} was deleted successfully.", "update")

    return redirect(url_for("staff.groups"))


@staff.route('/students/groups/delete/<int:student_id>/<int:group_id>')
@login_required
@permission_required(USER_ROLE["staff"])
def student_group_delete(student_id, group_id):
    student = User.load_by_id(student_id)
    group = Group.load(group_id)
    if not group or not student:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))
    # even if the group is valid, check that the user is actually in it
    elif group not in student.groups_proxy:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    group.remove_user(student)
    flash("User removed successfully.", "update")

    return redirect(url_for("staff.group_detail", id=group_id))


@staff.route('/other-hours')
@login_required
@permission_required(USER_ROLE["staff"])
def other_hours():
    return render_template("staff/other_hours.html", user=current_user)


@staff.route('/manage/add', methods=['GET', 'POST'])
@login_required
@permission_required(USER_ROLE["admin"])
def manage_add():
    form = UserUpload()
    errors = []
    if form.validate_on_submit():
        # save the file the user wannts to upload
        filename = data.save(form.file.data)
        file_valid = True
        file_path = app.config['UPLOADED_DATA_DEST'] + filename

        with open(file_path) as file:
            # split the row into a list while taking out the header row
            file_rows = file.read().splitlines()[1:]
            num_users = len(file_rows)

            # process each row individulally
            for index, row in enumerate(file_rows):
                row_data = row.split(",")

                # get the line no in a way that ordinary people will understand
                line_no = index + 2

                # check that they haven't left out info or added extra
                if len(row_data) == 5:
                    # validate the user from the csv
                    new_user = User.enroll_new_user(
                        row_data[0], row_data[1], row_data[2], row_data[3], row_data[4])

                    # if new_user is a list, it means we've got a bunch of
                    # errors and shouldn't upload the file
                    if isinstance(new_user, list):
                        file_valid = False
                        errors.append((line_no, new_user))
                else:
                    file_valid = False
                    errors.append(
                        (line_no,
                         [f"The user at line {line_no} was missing required information. Please ensure that you have at least entered the user's ID, email and role."]))

            # if all of our users have been valid, then we can commit the
            # changes to the db, otherwise we want to cancel the changes
            if file_valid:
                db.session.commit()
                flash(f"{num_users} users were added successfully.", "update")
            else:
                flash(
                    f"There were errors in the file you uploaded. None of the users have been uploaded.",
                    "error")
                db.session.rollback()

        # delete the file the user uploaded to avoid clogging up storage
        os.remove(file_path)

    # tell the user to actually upload a csv file
    elif form.is_submitted():
        flash("Please upload a valid .csv file.", "error")
    return render_template(
        "staff/manage_add.html",
        user=current_user,
        form=form,
        errors=errors)


@staff.route('/manage/remove')
@login_required
@permission_required(USER_ROLE["admin"])
def manage_remove():
    users = User.get_all()
    return render_template(
        "staff/manage_remove.html",
        user=current_user,
        users=users)


@staff.route('/manage/remove/<id>')
@login_required
@permission_required(USER_ROLE["admin"])
def manage_remove_user(id):
    user = User.load_by_id(id)
    if not user:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('staff.dashboard'))

    user.remove()
    flash(f"User {user.id} was removed successfully.", "update")
    return redirect(url_for('staff.manage_remove'))
