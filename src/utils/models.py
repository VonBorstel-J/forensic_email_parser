# src\utils\models.py

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy (to be done in your app configuration)
db = SQLAlchemy()

# Persistent User Model using SQLAlchemy
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def __init__(self, username, email, password, role):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.role = role

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

# Function to fetch user by username
def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

# Function to fetch user by ID
def get_user_by_id(user_id):
    return User.query.get(int(user_id))
