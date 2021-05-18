from flask_login import UserMixin
from flaskr import db

class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    id = db.Column('SchoolID', db.String(), primary_key=True)
    account_id = db.Column('AccountID', db.String(100), unique=True)
    first_name = db.Column('FirstName', db.String(100))
    last_name = db.Column('LastName', db.String(100))
    email = db.Column('Email', db.String(100))
    role = db.Column('Role', db.Integer())
    is_active = db.Column('IsActive', db.Boolean())
    profile_pic = db.Column('ProfilePic', db.String(1000))

    @staticmethod
    def load(email):
        """Loads a user from their email"""
        person = User.query.filter_by(email=email).first()
        return person

    @staticmethod
    def is_user(email):
        """Checks to see if the user attempting to log in to the site is authorised and in the database.
        Does not check whether the user has logged in before."""
        person = User.load(email)
        return person != None

    def update(self, unique_id, first_name, last_name, picture):
        """Updates a user's record in the database with account information retrieved from Google"""
        self.account_id = unique_id
        self.is_active = True
        self.first_name, self.last_name = (first_name, last_name)
        self.profile_pic = picture
        db.session.commit()
        return