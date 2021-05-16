from flask_login import UserMixin
from flaskr import db

class User(UserMixin, db.Model):
    school_id = db.Column(db.String(), primary_key=True) # primary keys are required by SQLAlchemy
    account_id = db.Column(db.String(100), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(1000))
    email = db.Column()