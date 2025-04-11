from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from models import User

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(),
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    submit = SubmitField('Registrarse')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso. Por favor, elige otro.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email ya está registrado. Por favor, usa otro.')

class ProductForm(FlaskForm):
    name = StringField('Nombre del Producto', validators=[DataRequired(), Length(min=3, max=100)])
    price = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0.01, message='El precio debe ser mayor que 0')])
    description = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    image = FileField('Imagen del Producto', validators=[Optional()])
    submit = SubmitField('Guardar Producto')

class SearchForm(FlaskForm):
    search = StringField('Buscar productos', validators=[Optional()])
    submit = SubmitField('Buscar')