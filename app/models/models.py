from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nickname = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64))
    surname = db.Column(db.String(64))
    avatar = db.Column(db.String(256), default='default_avatar.png')
    password_hash = db.Column(db.String(128), nullable=False)
    wishlist_items = db.relationship('WishlistItem', backref='owner', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float)
    details = db.Column(db.Text)
    event = db.Column(db.String(128))
    link = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WishlistItem {self.name}>'
