from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Profile(db.Model, UserMixin):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String)
    password = db.Column(db.String(120), nullable=False)
    bairro = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String, nullable=False)
    # Implementing UserMixin methods
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False
    __mapper_args__ = {
        'polymorphic_identity': 'profile',
        'polymorphic_on': tipo
    }

class User(Profile):
    __tablename__ = 'users'
    id = db.Column(db.Integer, db.ForeignKey('profiles.id'), primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)  # Include username explicitly
    shop_name = None
    atuacao = None

    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }

class Merchant(Profile):
    __tablename__ = 'merchants'
    id = db.Column(db.Integer, db.ForeignKey('profiles.id'), primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)  # Include username explicitly
    shop_name = db.Column(db.String, nullable=False)
    atuacao = db.Column(db.String,nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'merchant',
    }

class Charity(Profile):
    __tablename__ = 'Charity'
    id = db.Column(db.Integer, db.ForeignKey('profiles.id'), primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)  # Include username explicitly
    shop_name = db.Column(db.String, nullable=False)
    atuacao = db.Column(db.String,nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'charity',
    }