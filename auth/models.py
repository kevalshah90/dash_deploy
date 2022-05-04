from flask_login import UserMixin
from . import db

class users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    fullname = db.Column(db.String(500))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(500))
    jobtitle = db.Column(db.String(500))
    country = db.Column(db.String(10))
    emailverified = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)

class pass_recovery(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100))
    token = db.Column(db.String(100))
    status = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    updated = db.Column(db.DateTime)

class email_verification(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100))
    token = db.Column(db.String(100))
    status = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    updated = db.Column(db.DateTime)

class login_history(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    login_datetime = db.Column(db.DateTime)

def init_db():
    db.create_all()
    db.session.commit()

if __name__ == '__main__':
    init_db()
