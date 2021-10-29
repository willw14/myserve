from flask_login import UserMixin, user_logged_in
from functools import wraps
from myserve import db
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.ext.associationproxy import association_proxy

# set user roles and email as global variables so that they're easily editable
USER_ROLE = {"student": 1,
             "staff": 2,
             "admin": 3
             }

EMAIL_END = "burnside.school.nz"


class GroupMembers(db.Model):
    __tablename__ = "group_members"
    user_id = db.Column(
        'user_id',
        db.String,
        db.ForeignKey('user.user_id'),
        primary_key=True)
    group_id = db.Column(
        'group_id',
        db.Integer,
        db.ForeignKey('group.id'),
        primary_key=True)
    group_hours = db.Column('group_hours', db.Numeric())

    user = db.relationship("User", back_populates="groups")
    group = db.relationship("Group", back_populates="users")

    @classmethod
    def load(cls, user_id, group_id):
        """loads a GroupMembers object from the two ids that make it up"""
        return cls.query.filter_by(user_id=user_id, group_id=group_id).first()


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column("user_id", db.String(), primary_key=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String(), unique=True)
    form_class = db.Column(db.String())
    role_id = db.Column("role", db.Integer(), db.ForeignKey('user_role.id'))
    photo = db.Column(db.String())
    total = db.Column(db.Numeric())

    role = db.relationship("UserRole", back_populates="role_group")
    hours = db.relationship(
        "Log",
        back_populates="user",
        foreign_keys="Log.user_id")
    groups = db.relationship("GroupMembers", back_populates="user")

    # bypass GroupMember objects to get a list of user's groups
    groups_proxy = association_proxy('groups', 'group')

    # bypass Log objects to get a list of groups in user's log
    log_group_proxy = association_proxy('hours', 'group')

    @classmethod
    def load_by_email(cls, email):
        """Loads a user from the database using their email."""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def get_all(cls):
        """gets all users in the database"""
        return cls.query.all()

    @classmethod
    def load_by_id(cls, id):
        """Loads a user from the database using their email."""
        return cls.query.filter_by(id=id).first()

    @staticmethod
    def enroll_new_user(user_id, first_name, last_name, form_class, role):
        """Created a user object, suitable for adding to the database.
        If the info supplied is incorrect, a list of the reasons why is returned instead. """
        errors = []
        new_user = User(photo="/static/img/profile-photo-placeholder.jpg")

        # check that the user's id is unique
        if user_id and not User.load_by_id(user_id):
            new_user.id = user_id
            new_user.email = f"{str(user_id).lower()}@{EMAIL_END}"
        else:
            errors.append(
                f'The User ID "{user_id}" is invalid or already in the database.')

        # check that they've put in a valid role
        if role in USER_ROLE.keys():
            new_user.role_id = USER_ROLE[role]
            if new_user.role_id == USER_ROLE["student"]:
                new_user.total = 0
        else:
            errors.append(
                f"{role} is not a valid role for users - it must be 'student', 'staff' or 'admin'.")

        # if their role is student, check that they've put in a form classs
        if new_user.role_id == USER_ROLE["student"]:
            if form_class:
                new_user.form_class = form_class
            else:
                errors.append(
                    f"{role} is not a valid role for users - it must be 'student', 'staff' or 'admin'.")

        # check that we've been given both names
        if first_name and last_name:
            new_user.first_name = first_name
            new_user.last_name = last_name
        else:
            errors.append(
                f"Please ensure that both first and last names are provided for this user.")

        # if there are any errors we don't want to add the object, otherwise
        # it's good to return
        if errors:
            return errors
        else:
            db.session.add(new_user)
            return new_user

    @classmethod
    def get_teachers(cls):
        """Returns a list of all teachers in the database."""
        return cls.query.filter(
            cls.role_id.in_(
                (USER_ROLE["staff"], USER_ROLE["admin"]))).order_by(
            cls.last_name)

    @classmethod
    def get_students(cls):
        """Returns a list of all students in the database."""
        return cls.query.filter(
            cls.role_id == USER_ROLE["student"]).order_by(
            cls.last_name)

    @classmethod
    def get_top_students(cls):
        """Returns a list of the top 5 students in the database."""
        return cls.query.filter(
            cls.role_id == USER_ROLE["student"]).order_by(
            desc(
                cls.total)).limit(5).all()

    def update(self, first_name, last_name, picture):
        """Updates a user's record in the database with account information retrieved from Google"""
        self.first_name, self.last_name = (first_name, last_name)
        self.photo = picture
        db.session.commit()
        return

    def is_allowed(self, role_required):
        """determines if a user should be able to access a certain page depedning on their access level"""
        # users must have required role, unless they are an admin (then they
        # can also access staff pages)
        return self.role_id == role_required or (
            role_required == 2 and self.role_id == 3)

    def name(self):
        """returns the name of the user in a format that's nice for display"""
        return f"{self.first_name} {self.last_name}"

    def get_group_options(self):
        """returns a list of the groups a user is in as (id, name) tuples for use in forms"""
        return [(group_assoc.group.id, group_assoc.group.name)
                for group_assoc in self.groups]

    @classmethod
    def get_teacher_options(cls):
        """returns a list of all teachers in the school as (id, name) tuples for use in forms"""
        return [(teacher.id, f"{teacher.first_name} {teacher.last_name}")
                for teacher in cls.get_teachers()]

    def get_disabled_groups(self):
        """returns a list of the ids of groups which a user has logged hours under. We don't want them to be
        able to be removed from the group if they've logged hours under it"""
        group_ids = set()

        if self.role_id == USER_ROLE["student"]:
            for item in self.hours:
                # filter out hours which weren't put in under a group. If
                # they're added we get problems.
                if item.group_id:
                    group_ids.add(item.group_id)
        else:
            for group in self.groups_proxy:
                # check if they are the only teacher in the group
                if len(group.get_teachers()) <= 1:
                    group_ids.add(group.id)
        return list(group_ids)

    def join_groups(self, groups_join):
        """takes a list of group ids and a user and adds a new GroupMember object to the database for each one,
         adding them to those groups"""
        # setup total placeholder - if its students then we want to start at 0
        # hours, if staff we don't want any placeholder
        if self.role_id == USER_ROLE["student"]:
            placeholder = 0
        else:
            placeholder = None

        # add them to each of the groups passed
        for group_id in groups_join:
            group = GroupMembers(
                group_id=int(group_id),
                user_id=self.id,
                group_hours=placeholder)
            db.session.add(group)
        db.session.commit()

    def leave_groups(self, groups_leave):
        """takes a list of group ids and a user and removes their GroupMember object to the
        database for each one, removing them from those groups"""
        for group_id in groups_leave:
            group = GroupMembers.load(group_id=int(group_id), user_id=self.id)
            db.session.delete(group)
        db.session.commit()

    def get_current_award(self):
        """takes the current amount of hours and returns an award object with the current award earned by the user."""
        awards = Award.get_awards()

        current_award = None

        # compares the users total with each award, giving us the max award
        # they've gotten
        for i in range(len(awards)):
            if self.total >= awards[i].threshold:
                current_award = awards[i]

        return current_award

    def get_next_award(self):
        awards = Award.get_awards()
        current_award = self.get_current_award()

        if current_award is not None:
            index = awards.index(current_award)

            # check if there is actually another award for them to get or if
            # they've maxed out
            if index < len(awards) - 1:
                next_award = awards[index + 1]
            else:
                next_award = None
        else:
            # they've got no award, so it must be the first one
            next_award = awards[0]

        return next_award

    def get_hours_responsible(self):
        """retrieves the hours which a teacher has been indicated by students as being responsible for"""
        return Log.query.filter(Log.teacher_id == self.id).all()

    def remove(self):
        """removes a user and all data associated with them from the database"""
        for hour in self.hours:
            hour.delete()

        for group in self.groups_proxy:
            group.remove_user(self)

        db.session.delete(self)
        db.session.commit()
        return


class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), unique=True)

    hours = db.relationship("Log", back_populates="group")
    users = db.relationship("GroupMembers", back_populates="group")

    def user_total(self, user):
        """takes a user object and finds how many hours the user has completed in that group."""
        group_user = GroupMembers.load(user.id, self.id)
        return group_user.group_hours

    @classmethod
    def load(cls, id):
        """loads a group from the database using its ID"""
        return cls.query.filter_by(id=id).first()

    @classmethod
    def create(cls, name):
        """creates a new group, returning a group object so it can be used for other things"""
        new_group = cls(name=name)
        db.session.add(new_group)
        db.session.commit()
        return new_group

    @classmethod
    def get_all(cls):
        """Loads all groups in the database"""
        return cls.query.all()

    @classmethod
    def get_group_options(cls):
        """returns a sorted list of the groups in the database (id, name) tuples for use in forms"""
        groups = [(group.id, group.name) for group in cls.get_all()]
        # sort the values alphabetically by their name
        groups.sort(key=lambda x: x[1])
        return groups

    def get_teachers(self):
        """uses the group ID to return a list of user objects of the teachers in a particualr group"""
        teachers = User.query.join(
            User.groups).filter(
            GroupMembers.group_id == self.id, User.role_id.in_(
                (USER_ROLE["staff"], USER_ROLE["admin"]))).all()
        return teachers

    def get_students(self):
        """uses the group ID to return a list of GroupMember objects of the students in a particualr group"""
        teachers = GroupMembers.query.join(
            GroupMembers.user).filter(
            GroupMembers.group_id == self.id,
            User.role_id == USER_ROLE["student"]).all()
        return teachers

    def get_no_students(self):
        """returns the number of students in a given group"""
        return len(self.get_students())

    def get_teachers_string(self):
        """gives the teachers of a group in a format suitable for display"""
        teachers = self.get_teachers()
        teacher_names = []
        for teacher in teachers:
            teacher_names.append(teacher.first_name + " " + teacher.last_name)
        return ", ".join(teacher_names)

    def get_user_log(self, user):
        """takes a user object and returns a list of all of a users hours in that group"""
        logged_items = Log.query.filter(
            Log.user_id == user.id,
            Log.group_id == self.id).all()
        return logged_items

    def delete(self):
        """deletes a group"""
        db.session.delete(self)
        db.session.commit()
        return

    def remove_user(self, user):
        """deletes all of a user's hours from a group (if student), then removes them."""
        if user.role_id == USER_ROLE['student']:
            for item in self.get_user_log(user):
                item.delete()
        user.leave_groups([self.id])
        return


class UserRole(db.Model):
    __tablename__ = 'user_role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    role_group = db.relationship("User", back_populates="role")


class Log(db.Model):
    __tablename__ = "log"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey('user.user_id'))
    group_id = db.Column(db.Integer(), db.ForeignKey('group.id'))
    teacher_id = db.Column(db.String(), db.ForeignKey('user.user_id'))
    # this is the hours which the user has spent doing this work
    time = db.Column(db.Numeric())
    status_id = db.Column(
        "status",
        db.Integer(),
        db.ForeignKey('log_status.id'))
    date = db.Column(db.Date())  # this is the date when the work was completed
    # this is the date/time when the item was logged
    log_time = db.Column(db.DateTime())
    description = db.Column(db.String())

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="hours")
    teacher = db.relationship("User", foreign_keys=[teacher_id])
    group = db.relationship("Group", back_populates="hours")
    status = db.relationship("LogStatus", back_populates="hours")

    @classmethod
    def load(cls, id):
        """loads a previous log from the database using its ID"""
        return cls.query.filter_by(id=id).first()

    @classmethod
    def add_hours(cls, user, group_id, teacher_id, time, description, date):
        """creates a new log object in the database to record the hours of users"""
        new_hours = cls(
            user_id=user.id,
            group_id=group_id,
            time=time,
            description=description,
            date=date,
            log_time=datetime.now(),
            status_id=1
        )
        db.session.add(new_hours)

        # we need to update the user's total
        user.total += new_hours.time

        # if the hours were done in a group, then we need to udpate the group
        # total
        if group_id != "None":
            group_member = GroupMembers.load(
                user_id=user.id, group_id=group_id)
            group_member.group_hours += new_hours.time
        else:
            new_hours.teacher_id = teacher_id
            new_hours.group_id = None

        db.session.commit()
        return

    def edit_hours(
            self,
            group_id,
            teacher_id,
            time,
            description,
            date,
            status=1):
        """edits hours previously logged by a user"""
        old_time = self.time
        old_group = self.group
        difference = time - old_time

        self.group_id = group_id
        self.time = time
        self.description = description
        self.date = date
        self.log_time = datetime.now()
        self.status_id = status
        self.teacher_id = None

        # add (or subtract!) any difference in hours from their total
        self.user.total += difference

        # if they recorded their hours under our group, we'll subtract them
        # from the total incase they've changed group
        if old_group:
            old_group_member = GroupMembers.load(self.user_id, old_group.id)
            old_group_member.group_hours -= old_time

        # if there is a new group, we'll add the hours to its total. If there's
        # now a teacher, then we will record that instead
        if group_id == "None":
            self.teacher_id = teacher_id
            self.group_id = None
        else:
            group_member = GroupMembers.load(self.user_id, group_id)
            group_member.group_hours += self.time

        db.session.commit()
        return

    def delete(self):
        """deletes logged hours"""
        # update the user's total
        self.user.total -= self.time

        # if the hours were in a group, then we need to change that total too
        if self.group:
            group_member = GroupMembers.load(self.user_id, self.group.id)
            group_member.group_hours -= self.time

        db.session.delete(self)
        db.session.commit()
        return


class LogStatus(db.Model):
    __tablename__ = "log_status"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())

    hours = db.relationship("Log", back_populates="status")


class Award(db.Model):
    __tablename__ = "award"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    colour = db.Column(db.String())
    threshold = db.Column(db.Integer())

    @staticmethod
    def get_awards():
        """gets all awards stored in the database sorted in order of size ascedning"""
        return Award.query.order_by(Award.threshold).all()
