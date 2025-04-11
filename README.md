# Catálogo de Productos

Una aplicación web desarrollada con Flask que permite gestionar un catálogo de productos con sistema de usuarios.

![Vista previa de la aplicación](static/img/preview.png)

## Características

- **Autenticación de usuarios:** Registro, inicio de sesión y roles de usuario (admin/normal)
- **Gestión de productos:** Crear, leer, actualizar y eliminar productos
- **Validación de formularios:** Validaciones en el lado del servidor y mensajes de error
- **Búsqueda:** Búsqueda de productos por nombre
- **Interfaz responsive:** Diseño adaptable a diferentes dispositivos

## Tecnologías utilizadas

- **Flask:** Framework web de Python
- **SQLAlchemy:** ORM para interactuar con la base de datos
- **Flask-Login:** Gestión de sesiones de usuario
- **Flask-WTF:** Manejo y validación de formularios
- **Bootstrap 5:** Framework CSS para el frontend
- **SQLite:** Base de datos ligera

## Instalación y ejecución

1. **Clona el repositorio:**
git clone https://github.com/TomasMartinez99/flask_products.git
cd flask_products

2. **Crea un entorno virtual (opcional pero recomendado):**
python -m venv venv

3. **Activa el entorno virtual:**
- En Windows:
  ```
  venv\Scripts\activate
  ```
- En macOS/Linux:
  ```
  source venv/bin/activate
  ```

4. **Instala las dependencias:**
pip install flask flask-sqlalchemy flask-login flask-wtf email-validator

5. **Ejecuta la aplicación:**
python main.py

6. **Accede a la aplicación:**
Abre tu navegador y ve a `http://localhost:5000`

## Credenciales por defecto
Al iniciar la aplicación por primera vez se crea un usuario administrador:
- Usuario: `admin`
- Contraseña: `adminpass`