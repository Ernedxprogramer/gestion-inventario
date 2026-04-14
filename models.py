from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='vendedor')  # admin, gerente, vendedor
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(80), unique=True, nullable=True)
    category = db.Column(db.String(100), default='General')
    price = db.Column(db.Float, default=0.0)
    stock = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=5)  # Para alertas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name} ({self.stock})>'

class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('movements', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('movements', lazy=True))
    type = db.Column(db.String(20), nullable=False)  # purchase, sale, adjust
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, default=0.0)
    note = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Movement {self.type} {self.quantity} for {self.product_id}>'
