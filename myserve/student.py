from myserve.decorators import permission_required
from myserve.models import USER_ROLE, User, Log, Award, Group
from myserve.forms import AddHours, JoinGroups
from myserve import app
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
student = Blueprint('student', __name__)


@student.route('/dashboard')
@login_required
@permission_required(USER_ROLE["student"])
def dashboard():

    # get the user's current award and next one
    current_award = current_user.get_current_award()
    next_award = current_user.get_next_award()

    return render_template(
        "student/dashboard.html",
        user=current_user,
        current_award=current_award,
        next_award=next_award)


@student.route('/add-hours', methods=['GET', 'POST'])
@login_required
@permission_required(USER_ROLE["student"])
def add_hours():
    form = AddHours()

    # fill in the user's group choices based on the ones they are in
    form.group.choices = current_user.get_group_options() + \
        [(None, "No Group")]
    form.teacher.choices = User.get_teacher_options()

    if form.validate_on_submit():
        # send the form data to the database to be recorded
        Log.add_hours(
            current_user,
            form.group.data,
            form.teacher.data,
            form.hours.data,
            form.description.data,
            form.date.data,
        )
        flash(
            f"{form.hours.data:.2f} hour(s) logged for '{form.description.data}'",
            "update")
        return redirect(url_for('student.add_hours'))
    
    # tell user to look again if there are errors
    elif form.is_submitted():
        flash("Please check the information you've supplied.", "error")

    return render_template(
        "student/add_hours.html",
        user=current_user,
        form=form)


@student.route('/groups')
@login_required
@permission_required(USER_ROLE["student"])
def groups():
    return render_template("student/groups.html", user=current_user)


@student.route('/groups/<int:id>')
@login_required
@permission_required(USER_ROLE["student"])
def group_detail(id):
    group = Group.load(id)

    # check that the user is actually in that group
    if group not in current_user.groups_proxy:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('student.dashboard'))

    return render_template(
        "student/groups_detail.html",
        user=current_user,
        group=group)


@student.route('/log')
@login_required
@permission_required(USER_ROLE["student"])
def log():
    return render_template("student/log.html", user=current_user)


@student.route('/edit-hours/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(USER_ROLE["student"])
def edit_hours(id):
    item = Log.load(id)

    # checks that the item is one of the user's and that a teacher hasn't
    # locked it
    if item not in current_user.hours or item.status_id == 2:
        flash("Whoops! That page doesn't exist.", "error")
        return redirect(url_for('student.dashboard'))

    form = AddHours()

    # get form choices based on the user's groups
    form.group.choices = current_user.get_group_options() + \
        [(None, "No Group")]
    form.teacher.choices = User.get_teacher_options()

    # prefill the form with data from the database
    if request.method == 'GET':
        form.group.data = str(item.group_id)
        form.teacher.data = str(item.teacher_id)
        form.hours.data = item.time
        form.description.data = item.description
        form.date.data = item.date

    elif form.validate_on_submit():
        # if they've submitted the form then we will update the form
        if form.submit.data:
            item.edit_hours(
                form.group.data,
                form.teacher.data,
                form.hours.data,
                form.description.data,
                form.date.data,
            )
            flash(
                f"'{form.description.data}' was updated successfully.",
                "update")

        # if they've clicked the delete button, then we will delete the item
        elif form.delete.data:
            item.delete()
            flash(
                f"'{form.description.data}' was deleted successfully.",
                "update")

        return redirect(url_for('student.log'))

    elif form.is_submitted():
        flash("Please check the information you've supplied.", "error")

    return render_template(
        "student/edit_hours.html",
        user=current_user,
        form=form)


@student.route('/groups/edit', methods=['GET', 'POST'])
@login_required
@permission_required(USER_ROLE["student"])
def edit_groups():
    form = JoinGroups()

    # let's get the users groups and aslo which ones they aren't allowed to
    # leave
    form.groups.choices = Group.get_group_options()
    disabled_groups = current_user.get_disabled_groups()
    current_groups = [str(group.group_id) for group in current_user.groups]

    if request.method == 'GET':
        form.groups.data = current_groups

    elif form.is_submitted:
        # we add the disabled groups back in incase the user has altered the html and tried to leave a group
        # that they've logged hours under already
        form.groups.data.extend([str(group) for group in disabled_groups])

        # time to figure out which groups they've actually left and joined
        groups_join = set(form.groups.data) - set(current_groups)
        groups_leave = set(current_groups) - set(form.groups.data)

        current_user.join_groups(groups_join)
        current_user.leave_groups(groups_leave)
        flash(f"Your groups were updated successfully.", "update")
        return redirect(url_for('student.groups'))

    return render_template(
        "student/edit_groups.html",
        user=current_user,
        form=form,
        disabled_groups=disabled_groups)
