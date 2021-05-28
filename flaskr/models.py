from flask_login import UserMixin, user_logged_in
from flaskr import db

GroupMembers = db.Table('group_member', db.Model.metadata,
                    db.Column('user_id', db.Integer, db.ForeignKey('user.user_id')),
                    db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
                   )

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
    total = db.Column(db.Decimal())

    role = db.relationship("UserRole", back_populates="role_group")
    hours = db.relationship("Log", back_populates="group")
    groups = db.relationship("Group", secondary="GroupMembers", back_populates="users")

    @staticmethod
    def load(email):
        """Loads a user from the database using their email."""
        person = User.query.filter_by(email=email).first()
        return person

    @staticmethod
    def enrol(user_id, email, role, form_class=None):
        """Adds a user to the database so that they can then sign in with Google."""
        #NOT TESTED
        new_user = User(user_id=user_id, email=email, role_id=role, form_class=form_class)
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
    __tablename__ = 'Group'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), unique=True)

    hours = db.Relationship("Log", back_populates="group")
    users = db.relationship("User", secondary="GroupMembers", back_populates="groups")

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
    time = db.Column(db.Decimal())
    status_id = db.Column(db.Integer(), db.ForeignKey('log_status.id'))
    date = db.Column(db.DateTime())
    title = db.Column(db.String())
    description = db.Column(db.Text())

    user = db.relationship("User", back_populates="hours")
    group = db.relationship("Group", back_populates="hours")
    status = db.relationship("LogStatus", back_populates="hours")


class LogStatus(db.Model):
    __tablename__ = "log_status"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    
    hours = db.relationship("Log", back_populates="status")
