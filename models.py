from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Inicializar SQLAlchemy
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """
    Modelo para usuarios de la aplicación
    Hereda de UserMixin para proporcionar métodos requeridos por Flask-Login
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # Aumentado a 256 para acomodar hashes más largos
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        """
        Genera un hash seguro de la contraseña
        Utiliza werkzeug.security para generar un hash con salt
        """
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """
        Verifica si la contraseña proporcionada coincide con el hash almacenado
        Devuelve True si coincide, False en caso contrario
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """Representación de string del objeto para debugging"""
        return f'<User {self.username}>'

class Products(db.Model):
    """
    Modelo para productos
    Almacena información como nombre, precio, descripción e imagen
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relación con el modelo User
    # backref crea una propiedad 'products' en User para acceder a los productos de un usuario
    user = db.relationship('User', backref=db.backref('products', lazy=True))

    def __repr__(self):
        """Representación de string del objeto para debugging"""
        return f'<Product {self.name}>'