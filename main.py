from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

# Crear aplicación Flask
app = Flask(__name__)

# Configuración simplificada
app.config['SECRET_KEY'] = 'clave-secreta-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flask_products'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Asegurarse de que existe la carpeta de uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar la base de datos
db = SQLAlchemy(app)

# Definir el modelo de Producto
class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Product {self.name}>'

# Crear todas las tablas en la base de datos
with app.app_context():
    db.create_all()

# Rutas para CRUD de productos
@app.route('/')
def index():
    products = Products.query.all()
    return render_template('products/index.html', products=products)

@app.route('/products/create', methods=['GET', 'POST'])
def create_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        # Manejar la carga de imagen
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image = filename
        
        # Crear y guardar el nuevo producto
        product = Products(
            name=name,
            description=description,
            price=price,
            image=image
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Producto creado con éxito', 'success')
        return redirect(url_for('index'))
    
    return render_template('products/create.html')

@app.route('/products/<int:product_id>')
def view_product(product_id):
    product = Products.query.get_or_404(product_id)
    return render_template('products/view.html', product=product)

@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Products.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = request.form.get('price')
        
        # Manejar la carga de imagen
        if 'image' in request.files:
            file = request.files['image']
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
    
    return render_template('products/edit.html', product=product)

@app.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    product = Products.query.get_or_404(product_id)
    
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
    app.run(debug=True)