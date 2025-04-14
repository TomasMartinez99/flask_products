from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, User, Products
from forms import LoginForm, RegisterForm, ProductForm, SearchForm
import pandas as pd
import numpy as np
import seaborn as sns
from io import BytesIO
import base64
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
import matplotlib
matplotlib.use('Agg')  # IMPORTANTE: Debe estar ANTES de importar pyplot
import matplotlib.pyplot as plt

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

# Clase para el sistema de recomendación
class ProductRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.products = None
        self.product_indices = {}
    
    def fit(self, products):
        """Entrena el recomendador con los productos disponibles"""
        self.products = products
        
        # Crear un corpus combinando nombre y descripción
        corpus = []
        for i, product in enumerate(products):
            # Guardar índice para búsquedas rápidas
            self.product_indices[product.id] = i
            
            text = product.name
            if product.description:
                text += " " + product.description
            corpus.append(text)
        
        # Crear matriz TF-IDF si hay productos
        if corpus:
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        
        return self
    
    def get_recommendations(self, product_id, num_recommendations=3):
        """Obtiene productos similares basados en contenido textual"""
        # Verificar si hay productos o matriz
        if not self.products or not self.tfidf_matrix is not None:
            return []
            
        # Verificar si el producto existe
        if product_id not in self.product_indices:
            return []
        
        # Obtener índice del producto
        idx = self.product_indices[product_id]
        
        # Calcular similitud del coseno
        sim_scores = cosine_similarity(
            self.tfidf_matrix[idx:idx+1], 
            self.tfidf_matrix
        ).flatten()
        
        # Obtener los índices de los productos más similares (excluyendo el mismo producto)
        sim_scores[idx] = 0  # Excluir el mismo producto
        top_indices = sim_scores.argsort()[-num_recommendations:][::-1]
        
        # Filtrar por puntaje de similitud positivo
        recommended_products = []
        for i in top_indices:
            if sim_scores[i] > 0:
                recommended_products.append(self.products[i])
        
        return recommended_products

# Inicializar el recomendador globalmente
recommender = ProductRecommender()

@login_manager.user_loader
def load_user(user_id):
    """
    Función requerida por Flask-Login para cargar un usuario desde la base de datos
    basándose en su ID de usuario
    """
    return User.query.get(int(user_id))

# Función para actualizar el recomendador
def update_recommender():
    """Actualiza el modelo de recomendación con los productos actuales"""
    global recommender
    products = Products.query.all()
    recommender.fit(products)
    print(f"Recomendador actualizado con {len(products)} productos")

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
        
        # Actualizar recomendador
        update_recommender()

# Elimina el decorador @app.before_first_request
def initialize_database():
    """Inicializa la base de datos antes de la primera solicitud"""
    create_tables()

with app.app_context():
    initialize_database()

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

# Ruta para el dashboard analítico
@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard con análisis de datos y visualizaciones"""
    # Asegurarte que solo los administradores accedan
    if not current_user.is_admin:
        flash('Solo los administradores pueden acceder al dashboard', 'danger')
        return redirect(url_for('index'))
    
    # Obtener todos los productos
    products = Products.query.all()
    
    # Si no hay productos, mostrar mensaje
    if not products:
        flash('No hay productos para analizar.', 'warning')
        return redirect(url_for('index'))
    
    # Convertir a DataFrame de pandas
    data = [{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'user_id': p.user_id,
        'description_length': len(p.description or ''),
        'has_image': 1 if p.image else 0
    } for p in products]
    
    df = pd.DataFrame(data)
    
    # Análisis básico
    stats = {
        'total_products': len(products),
        'avg_price': df['price'].mean() if len(df) > 0 else 0,
        'max_price': df['price'].max() if len(df) > 0 else 0,
        'min_price': df['price'].min() if len(df) > 0 else 0,
        'price_std': df['price'].std() if len(df) > 0 else 0,
        'products_with_images': df['has_image'].sum() if len(df) > 0 else 0,
        'products_without_images': len(df) - df['has_image'].sum() if len(df) > 0 else 0
    }
    
    # Generar gráficos
    graphs = {}
    
    # Configurar estilo de seaborn
    sns.set_style('whitegrid')
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.size'] = 12
    
    try:
        # Gráfico 1: Distribución de precios
        plt.figure(figsize=(10, 5))
        ax = sns.histplot(df['price'], kde=True, color='#1e70ba', bins=min(15, len(df)))
        plt.title('Distribución de Precios de Productos', fontsize=16)
        plt.xlabel('Precio ($)', fontsize=14)
        plt.ylabel('Frecuencia', fontsize=14)
        # Añadir línea vertical para precio promedio
        if len(df) > 0:
            plt.axvline(df['price'].mean(), color='red', linestyle='--', 
                        label=f'Precio promedio: ${df["price"].mean():.2f}')
            plt.legend()
        
        # Guardar gráfico como imagen
        img = BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        plt.close()
        img.seek(0)
        graphs['price_dist'] = base64.b64encode(img.getvalue()).decode('utf8')
        
        # Gráfico 2: Productos con/sin imágenes - Corregido
        plt.figure(figsize=(8, 8))
        img_counts = df['has_image'].value_counts()
        
        # Verificar que hay datos suficientes y de ambos tipos
        if len(img_counts) > 0:
            # Preparar etiquetas y valores
            labels = []
            values = []
            
            # Añadir valores con imagen si existen
            if 1 in img_counts:
                labels.append('Con imagen')
                values.append(img_counts[1])
                
            # Añadir valores sin imagen si existen
            if 0 in img_counts:
                labels.append('Sin imagen')
                values.append(img_counts[0])
                
            # Solo crear el gráfico si hay datos
            if labels and values:
                colors = ['#1e70ba', '#aaaaaa'][:len(labels)]  # Asegurar que hay suficientes colores
                explode = [0.05, 0][:len(labels)]  # Asegurar que hay suficientes valores de separación
                
                plt.pie(values, 
                        labels=labels,
                        autopct='%1.1f%%',
                        startangle=90,
                        colors=colors,
                        explode=explode,
                        shadow=True)
                plt.title('Proporción de Productos con Imágenes', fontsize=16)
                plt.axis('equal')
                
                # Guardar gráfico como imagen
                img = BytesIO()
                plt.savefig(img, format='png', bbox_inches='tight')
                plt.close()
                img.seek(0)
                graphs['image_pie'] = base64.b64encode(img.getvalue()).decode('utf8')
            else:
                # Si no hay datos suficientes para el gráfico de pastel
                graphs['image_pie'] = None
        else:
            # Si no hay datos para crear el gráfico
            graphs['image_pie'] = None
        
        # Gráfico 3: Precio vs. Longitud de descripción
        if len(df) > 1:  # Solo si hay más de un producto
            plt.figure(figsize=(10, 6))
            sns.scatterplot(x='price', y='description_length', data=df, color='#1e70ba', 
                          alpha=0.7, s=100)
            plt.title('Relación entre Precio y Longitud de Descripción', fontsize=16)
            plt.xlabel('Precio ($)', fontsize=14)
            plt.ylabel('Longitud de descripción (caracteres)', fontsize=14)
            
            # Añadir línea de tendencia si hay suficientes puntos
            z = np.polyfit(df['price'], df['description_length'], 1)
            p = np.poly1d(z)
            plt.plot(df['price'], p(df['price']), "r--", 
                    label=f"Tendencia: y = {z[0]:.2f}x + {z[1]:.2f}")
            plt.legend()
            
            # Guardar gráfico como imagen
            img = BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight')
            plt.close()
            img.seek(0)
            graphs['price_desc'] = base64.b64encode(img.getvalue()).decode('utf8')
        else:
            graphs['price_desc'] = None
            
    except Exception as e:
        # Manejar errores en la generación de gráficos
        print(f"Error al generar gráficos: {e}")
        flash(f"Hubo un problema al generar algunas visualizaciones: {e}", "warning")
        
        # Asegurar que hay valores predeterminados para los gráficos
        if 'price_dist' not in graphs:
            graphs['price_dist'] = None
        if 'image_pie' not in graphs:
            graphs['image_pie'] = None
        if 'price_desc' not in graphs:
            graphs['price_desc'] = None
    
    return render_template('dashboard.html', stats=stats, graphs=graphs)

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
    
    # Implementar búsqueda avanzada
    if query:
        # Dividir la consulta en términos para búsqueda más precisa
        search_terms = query.lower().split()
        
        # Construir condiciones de búsqueda
        search_filters = []
        for term in search_terms:
            term_filter = or_(
                Products.name.ilike(f'%{term}%'),
                Products.description.ilike(f'%{term}%')
            )
            search_filters.append(term_filter)
        
        # Combinar con AND para resultados más relevantes
        products = Products.query.filter(and_(*search_filters)).all()
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
        
        # Actualizar el recomendador
        update_recommender()
        
        flash('Producto creado con éxito', 'success')
        return redirect(url_for('index'))
    
    return render_template('products/create.html', form=form)

@app.route('/products/<int:product_id>')
def view_product(product_id):
    """Muestra los detalles de un producto específico y recomendaciones"""
    # get_or_404 obtiene el producto o devuelve 404 si no existe
    product = Products.query.get_or_404(product_id)
    
    # Obtener recomendaciones
    similar_products = recommender.get_recommendations(product_id, num_recommendations=3)
    
    return render_template('products/view.html', 
                          product=product, 
                          similar_products=similar_products)

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
        # Guardar la imagen actual antes de actualizar otros campos
        current_image = product.image
        
        # Actualizar el objeto product con los datos del formulario
        # Excluimos la imagen para manejarla manualmente
        form.populate_obj(product)
        
        # Restaurar la imagen original (porque populate_obj puede haberla limpiado)
        product.image = current_image
        
        # Manejar la carga de imagen SOLO si se seleccionó un archivo real
        if form.image.data and form.image.data.filename != '':
            file = form.image.data
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
        
        # Actualizar el recomendador
        update_recommender()
        
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
    
    # Actualizar el recomendador
    update_recommender()
    
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