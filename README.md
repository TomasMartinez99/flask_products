# Catálogo de Productos

Una aplicación web desarrollada con Flask que permite gestionar un catálogo de productos con sistema de usuarios, recomendaciones inteligentes y análisis de datos.

![Vista previa de la aplicación](static/img/preview.png)

## Características

- **Autenticación de usuarios:** Registro, inicio de sesión y roles de usuario (admin/normal)
- **Gestión de productos:** Crear, leer, actualizar y eliminar productos
- **Imágenes de productos:** Carga y gestión de imágenes para cada producto
- **Sistema de recomendaciones:** Recomendación de productos similares basada en TF-IDF y similitud del coseno
- **Dashboard analítico:** Visualizaciones y estadísticas sobre los productos del catálogo
- **Validación de formularios:** Validaciones en el lado del servidor y mensajes de error
- **Búsqueda avanzada:** Búsqueda de productos por nombre y descripción
- **Interfaz responsive:** Diseño adaptable a diferentes dispositivos con Tailwind CSS

## Tecnologías utilizadas

- **Backend:**
  - **Flask:** Framework web de Python
  - **SQLAlchemy:** ORM para interactuar con la base de datos
  - **Flask-Login:** Gestión de sesiones de usuario
  - **Flask-WTF:** Manejo y validación de formularios
  - **Pandas & NumPy:** Análisis de datos
  - **Scikit-learn:** Procesamiento de texto y sistema de recomendaciones
  - **Matplotlib & Seaborn:** Generación de visualizaciones

- **Frontend:**
  - **Tailwind CSS:** Framework utility-first para el diseño
  - **Font Awesome:** Iconos vectoriales
  - **JavaScript:** Interactividad en el cliente

- **Base de datos:**
  - **MySQL:** Base de datos relacional

## Instalación y ejecución

1. **Clona el repositorio:**
```
git clone https://github.com/TomasMartinez99/flask_products.git
cd flask_products
```

2. **Crea un entorno virtual (opcional pero recomendado):**
```
python -m venv venv
```

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
```
pip install -r requirements.txt
```

5. **Configura la base de datos:**
   - Crea una base de datos MySQL llamada `flask_products`
   - Asegúrate de que las credenciales en `main.py` coincidan con tu configuración

6. **Ejecuta la aplicación:**
```
python main.py
```

7. **Accede a la aplicación:**
   - Abre tu navegador y ve a `http://localhost:5000`

## Credenciales por defecto
Al iniciar la aplicación por primera vez se crea un usuario administrador:
- Usuario: `admin`
- Contraseña: `adminpass`

## Características del Dashboard

El dashboard analítico proporciona:
- Estadísticas clave sobre productos (total, precios, etc.)
- Distribución de precios
- Proporción de productos con imágenes
- Relación entre precio y longitud de descripción

## Sistema de Recomendación

La aplicación incluye un sistema de recomendación de productos basado en:
- Procesamiento de lenguaje natural con TF-IDF
- Cálculo de similitud mediante similitud del coseno
- Recomendaciones personalizadas en la página de cada producto