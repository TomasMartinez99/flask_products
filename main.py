from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, User, Products
from forms import LoginForm, RegisterForm, ProductForm, SearchForm

# Crear aplicación Flask
app = Flask(__name__)

# Configuración de la aplicación
# SECRET_KEY: Clave para proteger sesiones y formularios CSRF
# SQLALCHEMY_DATABASE_URI: Conexión a la base de datos MySQL
# UPLOAD_FOLDER: Carpeta para almacenar imágenes subidas
app.config['SECRET_KEY'] = '9hQ3cGvTp8sN6fEw7mZy2kJxAuRdXb4V'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flask_products'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Asegurarse de que existe la carpeta de uploads
# os.makedirs crea la carpeta si no existe (exist_ok=True evita errores si ya existe)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar la base de datos con la aplicación
db.init_app(app)

# Configurar Flask-Login para gestionar sesiones de usuario
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Vista a la que redirigir si se requiere login
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """
    Función requerida por Flask-Login para cargar un usuario desde la base de datos
    basándose en su ID de usuario
    """
    return User.query.get(int(user_id))

# Función para crear tablas e inicializar datos
def create_tables():
    """
    Crea todas las tablas definidas en los modelos si no existen
    e inicializa un usuario administrador predeterminado
    """
    with app.app_context():
        db.create_all()
        
        # Crear un usuario admin si no existe
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()
            print("Usuario admin creado.")
        
        print("Tablas creadas.")

# Esta función se ejecuta antes de la primera solicitud a la aplicación
""" @app.before_first_request
def initialize_database(): """
"""Inicializa la base de datos antes de la primera solicitud"""
""" create_tables() """

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el inicio de sesión de usuarios
    GET: Muestra el formulario de login
    POST: Procesa el envío del formulario y autentica al usuario
    """
    # Si el usuario ya está autenticado, redirigir a la página principal
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Buscar el usuario por nombre de usuario
        user = User.query.filter_by(username=form.username.data).first()
        
        # Verificar si el usuario existe y la contraseña es correcta
        if user and user.check_password(form.password.data):
            # Iniciar sesión del usuario
            login_user(user)
            flash('Has iniciado sesión correctamente', 'success')
            
            # Redirigir a la página solicitada originalmente o a la página principal
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Maneja el registro de nuevos usuarios
    GET: Muestra el formulario de registro
    POST: Procesa el envío del formulario y crea un nuevo usuario
    """
    # Si el usuario ya está autenticado, redirigir a la página principal
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Crear nuevo usuario con los datos del formulario
        user = User(
            username=form.username.data, 
            email=form.email.data,
            is_admin=True  # Todos los usuarios se registran como admin (para demo)
        )
        user.set_password(form.password.data)
        
        # Guardar en la base de datos
        db.session.add(user)
        db.session.commit()
        
        flash('¡Registro exitoso! Ahora puedes iniciar sesión', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required  # Requiere que el usuario esté autenticado
def logout():
    """Cierra la sesión del usuario actual"""
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('index'))

# Rutas para CRUD de productos
@app.route('/')
def index():
    """
    Página principal que muestra todos los productos
    Incluye funcionalidad de búsqueda
    """
    # Inicializar formulario de búsqueda con parámetros de URL
    # meta={'csrf': False} desactiva CSRF para formularios GET
    search_form = SearchForm(request.args, meta={'csrf': False})
    query = request.args.get('search', '')
    
    # Filtrar productos por texto de búsqueda
    if query:
        # La función contains() de SQLAlchemy realiza una búsqueda LIKE %query%
        products = Products.query.filter(Products.name.contains(query)).all()
    else:
        products = Products.query.all()
    
    return render_template('products/index.html', products=products, search_form=search_form)

@app.route('/products/create', methods=['GET', 'POST'])
@login_required  # Solo usuarios autenticados pueden crear productos
def create_product():
    """
    Maneja la creación de nuevos productos
    GET: Muestra el formulario de creación
    POST: Procesa el formulario y crea un nuevo producto
    """
    form = ProductForm()
    
    if form.validate_on_submit():
        # Manejar la carga de imagen
        image = None
        if form.image.data:
            file = form.image.data
            if file.filename != '':
                # secure_filename sanitiza el nombre del archivo para prevenir ataques
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image = filename
        
        # Crear y guardar el nuevo producto
        product = Products(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image=image,
            user_id=current_user.id  # Asociar producto con el usuario actual
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Producto creado con éxito', 'success')
        return redirect(url_for('index'))
    
    return render_template('products/create.html', form=form)

@app.route('/products/<int:product_id>')
def view_product(product_id):
    """Muestra los detalles de un producto específico"""
    # get_or_404 obtiene el producto o devuelve 404 si no existe
    product = Products.query.get_or_404(product_id)
    return render_template('products/view.html', product=product)

@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """
    Maneja la edición de productos existentes
    Solo el propietario o un administrador puede editar
    """
    product = Products.query.get_or_404(product_id)
    
    # Verificar que el usuario sea el propietario o un admin
    if product.user_id != current_user.id and not current_user.is_admin:
        flash('No tienes permiso para editar este producto', 'danger')
        return redirect(url_for('index'))
    
    # Inicializar el formulario con los datos del producto (obj=product)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        # Actualizar el objeto product con los datos del formulario
        form.populate_obj(product)
        
        # Manejar la carga de imagen
        if form.image.data:
            file = form.image.data
            if file.filename != '':
                # Si hay una imagen existente, intentar borrarla
                if product.image:
                    try:
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error al eliminar imagen antigua: {e}")
                
                # Guardar la nueva imagen
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                product.image = filename
        
        db.session.commit()
        flash('Producto actualizado con éxito', 'success')
        return redirect(url_for('view_product', product_id=product.id))
    
    return render_template('products/edit.html', product=product, form=form)

@app.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """
    Elimina un producto existente
    Solo el propietario o un administrador puede eliminar
    Solo acepta método POST para prevenir eliminaciones accidentales
    """
    product = Products.query.get_or_404(product_id)
    
    # Verificar que el usuario sea el propietario o un admin
    if product.user_id != current_user.id and not current_user.is_admin:
        flash('No tienes permiso para eliminar este producto', 'danger')
        return redirect(url_for('index'))
    
    # Intentar eliminar la imagen si existe
    if product.image:
        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error al eliminar imagen: {e}")
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Producto eliminado con éxito', 'success')
    return redirect(url_for('index'))

# Manejador de contexto para acceder a la URL de la imagen
@app.context_processor
def utility_processor():
    """
    Proporciona funciones útiles a las plantillas
    get_image_url: genera la URL para las imágenes de productos
    """
    def get_image_url(image):
        if image:
            # Para depuración, imprime en consola la ruta que está generando
            img_url = url_for('static', filename=f'uploads/{image}')
            print(f"URL de imagen generada: {img_url}")
            return img_url
        return url_for('static', filename='img/no-image.png')
    
    return dict(get_image_url=get_image_url)

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)  # debug=True para desarrollo, False para producción