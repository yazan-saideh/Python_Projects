from .database import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import Enum as SaEnum
from enum import Enum


class AccountType(str, Enum):
    buyer = 'buyer'
    seller = 'seller'


class PropertyType(str, Enum):  # Enum for property types
    apartment = 'apartment'
    house = 'house'


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150))
    last_name = db.Column(db.String(150))
    account_type = db.Column(SaEnum(AccountType), nullable=False)  # Enum for buyer/seller type
    __mapper_args__ = {
        'polymorphic_on': account_type,  # Use account_type to differentiate between Buyer and Seller
        'polymorphic_identity': 'user'
    }


class Buyer(User):
    __tablename__ = 'buyer'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    orders = db.relationship('Order', backref='buyer', cascade="all, delete-orphan")
    __mapper_args__ = {
        'polymorphic_identity': 'buyer',
    }


class Seller(User):
    __tablename__ = 'seller'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    estates = db.relationship('Estate', backref='seller', cascade="all, delete-orphan")
    __mapper_args__ = {
        'polymorphic_identity': 'seller',
    }


class Estate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    size = db.Column(db.Float, nullable=False)
    bedrooms = db.Column(db.Integer)  # Optional
    bathrooms = db.Column(db.Integer)  # Optional
    property_type = db.Column(SaEnum(PropertyType), nullable=False)
    garage = db.Column(db.Boolean, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)  # Correct foreign key
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    # Removed image_filename; images will be stored in EstateImage relationship
    rent_details = db.relationship('House_For_Rent', backref='estate', uselist=False, cascade="all, delete-orphan")
    sale_details = db.relationship('House_For_Sale', backref='estate', uselist=False, cascade="all, delete-orphan")
    images = db.relationship('EstateImage', backref='estate', cascade="all, delete-orphan")  # New relationship


class EstateImage(db.Model):
    __tablename__ = 'estate_image'
    id = db.Column(db.Integer, primary_key=True)
    estate_id = db.Column(db.Integer, db.ForeignKey('estate.id'), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('buyer.id'), nullable=False)  # Correct foreign key for buyer
    estate_id = db.Column(db.Integer, db.ForeignKey('estate.id'), nullable=False)
    estate = db.relationship('Estate', backref='orders')


class House_For_Rent(db.Model):
    __tablename__ = 'house_for_rent'
    id = db.Column(db.Integer, db.ForeignKey('estate.id'), primary_key=True)
    rental_terms = db.Column(db.Text)


class House_For_Sale(db.Model):
    __tablename__ = 'house_for_sale'
    id = db.Column(db.Integer, db.ForeignKey('estate.id'), primary_key=True)
    sale_terms = db.Column(db.Text)