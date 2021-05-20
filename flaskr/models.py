from flask_login import UserMixin
from flaskr import db


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column("user_id", db.String(), primary_key=True)
    google_id = db.Column(db.String(), unique=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String())
    role_id = db.Column("role", db.Integer(), db.ForeignKey('user_role.id'))
    is_active = db.Column(db.Boolean())
    photo = db.Column(db.String())

    role = db.relationship("UserRole", back_populates="role_group")

    @staticmethod
    def load(email):
        """Loads a user from the database using their email."""
        person = User.query.filter_by(email=email).first()
        return person

    @staticmethod
    def enrol(id, email, role):
        """Adds a user to the database so that they can then sign in with Google."""
        #NOT TESTED
        new_user = User(id=id, email=email, role_id=role)
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

class UserRole(db.Model):
    __tablename__ = 'user_role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    role_group = db.relationship("User", back_populates="role")


