from flask_login import UserMixin, user_logged_in
from flaskr import db
from datetime import datetime
from sqlalchemy.ext.associationproxy import association_proxy


class GroupMembers(db.Model):
    __tablename__ = "group_members"
    user_id = db.Column('user_id', db.String, db.ForeignKey('user.user_id'), primary_key=True)
    group_id = db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
    group_hours = db.Column('group_hours', db.Numeric())

    user = db.relationship("User", back_populates="groups")
    group = db.relationship("Group", back_populates="users")

    @classmethod
    def load(cls, user_id, group_id):
        return cls.query.filter_by(user_id=user_id, group_id=group_id).first()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column("user_id", db.String(), primary_key=True)
    google_id = db.Column(db.String(), unique=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String())
    form_class = db.Column(db.String())
    role_id = db.Column("role", db.Integer(), db.ForeignKey('user_role.id'))
    is_active = db.Column(db.Boolean())
    photo = db.Column(db.String())
    total = db.Column(db.Numeric())

    role = db.relationship("UserRole", back_populates="role_group")
    hours = db.relationship("Log", back_populates="user")
    groups = db.relationship("GroupMembers", back_populates="user")

    @classmethod
    def load(cls, email):
        """Loads a user from the database using their email."""
        return cls.query.filter_by(email=email).first()

    @staticmethod
    def enrol(user_id, email, role, form_class=None):
        """Adds a user to the database so that they can then sign in with Google."""
        #NOT TESTED
        #Need to enrol users in Group 0 (None)
        new_user = User(id=user_id, email=email, role_id=role, form_class=form_class, total=0)
        db.session.add(new_user)
        db.session.commit()
        return

    @staticmethod
    def is_user(email):
        """Checks to see if the user attempting to log in to the site is authorised and in the database.
        Does not check whether the user has logged in before."""
        person = User.load(email)
        return person != None
        #CHECK IF THE != NONE CAN BE DONE NICELY

    def update(self, unique_id, first_name, last_name, picture):
        """Updates a user's record in the database with account information retrieved from Google"""
        self.google_id = unique_id
        self.is_active = True
        self.first_name, self.last_name = (first_name, last_name)
        self.photo = picture
        db.session.commit()
        return


class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), unique=True)
    access_code = db.Column(db.String(), unique=True)

    hours = db.relationship("Log", back_populates="group")
    users = db.relationship("GroupMembers", back_populates="group")

    def user_total(self, user):
        group_user = GroupMembers.load(self.id, user.id)
        return group_user.group_hours


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
    time = db.Column(db.Numeric())
    status_id = db.Column("status", db.Integer(), db.ForeignKey('log_status.id'))
    date = db.Column(db.Date())
    log_time = db.Column(db.DateTime())
    description = db.Column(db.String())

    user = db.relationship("User", back_populates="hours")
    group = db.relationship("Group", back_populates="hours")
    status = db.relationship("LogStatus", back_populates="hours")

    @staticmethod
    def add_hours(user, group_id, time, description, date):
        new_hours = Log(
            user_id=user.id, 
            group_id=group_id, 
            time=time, 
            description=description,
            date=date,
            log_time=datetime.now(),
            status_id = 1
            )
        db.session.add(new_hours)
        user.total += new_hours.time
        group_member = GroupMembers.load(user_id=user.id, group_id=group_id)
        group_member.group_hours += new_hours.time
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
        return Award.query.order_by(Award.threshold).fetchall()

    @staticmethod
    def get_current_award(hours):
        awards = get_awards()

        index_found = False
        for i in range(len(awards)):
            if hours - awards[i].threshold > 0 and not index_found:
                current_award = awards[i]
                index_found = True
        
        return current_award

    @staticmethod
    def get_next_award(hours):
        awards = get_awards()
        current_award = get_current_award(hours)

        awards.index
