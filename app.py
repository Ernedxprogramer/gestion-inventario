from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product, Movement
from datetime import datetime
import os
import sys
import io
import qrcode
import socket
from sqlalchemy.exc import SQLAlchemyError

# Detectar si se ejecuta desde PyInstaller
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Ejecutable compilado con PyInstaller
    BASE_DIR = sys._MEIPASS
else:
    # Ejecución normal desde Python
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

def get_local_ip():
    """Obtener la dirección IP local de la máquina"""
    try:
        # Conectar a un servidor DNS para obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def create_app():
    app = Flask(__name__, template_folder=TEMPLATE_DIR)
    
    # Configuración de base de datos: PostgreSQL en producción, SQLite en desarrollo
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Para Render/Heroku: reemplazar postgres:// con postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Desarrollo local con SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'inventory.db')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # SECRET_KEY desde variables de entorno (más seguro)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a7a240f199409281abd23ae2a3ee6c7cc25d0384b7641d009046aeeaec5e3c6d')
    
    db.init_app(app)
    
    # Inicializar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Crear tablas dentro del app context
    with app.app_context():
        db.create_all()
        # Crear usuario admin por defecto si no existe
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@inventario.local', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("[INFO] Usuario admin creado (usuario: admin, contraseña: admin123)")

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('products'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('products'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Tu cuenta ha sido desactivada', 'danger')
                    return redirect(url_for('login'))
                login_user(user)
                flash(f'¡Bienvenido {user.username}!', 'success')
                return redirect(url_for('products'))
            flash('Usuario o contraseña inválidos', 'danger')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Sesión cerrada', 'info')
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # El registro público está deshabilitado
        flash('El registro de nuevos usuarios está deshabilitado. Contacta al administrador.', 'info')
        return redirect(url_for('login'))

    @app.route('/admin/users', methods=['GET', 'POST'])
    @login_required
    def admin_users():
        # Solo admin puede crear usuarios
        if current_user.role != 'admin':
            flash('No tienes permisos para acceder a esta sección', 'danger')
            return redirect(url_for('products'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'vendedor')
            
            # Validaciones
            if not username or not email or not password:
                flash('Todos los campos son requeridos', 'danger')
                return redirect(url_for('admin_users'))
            
            if len(username) < 3:
                flash('El usuario debe tener al menos 3 caracteres', 'danger')
                return redirect(url_for('admin_users'))
            
            if len(password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres', 'danger')
                return redirect(url_for('admin_users'))
            
            if User.query.filter_by(username=username).first():
                flash('El usuario ya existe', 'danger')
                return redirect(url_for('admin_users'))
            
            if User.query.filter_by(email=email).first():
                flash('El email ya está registrado', 'danger')
                return redirect(url_for('admin_users'))
            
            # Validar que el rol sea válido
            if role not in ['admin', 'gerente', 'vendedor']:
                role = 'vendedor'
            
            try:
                user = User(username=username, email=email, role=role, is_active=True)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash(f'Usuario "{username}" creado exitosamente', 'success')
                return redirect(url_for('admin_users'))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f'Error al crear el usuario: {str(e)}', 'danger')
        
        # Listar todos los usuarios
        users = User.query.all()
        return render_template('admin_users.html', users=users)

    @app.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
    @login_required
    def toggle_user_status(user_id):
        # Solo admin puede cambiar estado
        if current_user.role != 'admin':
            flash('No tienes permisos', 'danger')
            return redirect(url_for('products'))
        
        user = User.query.get_or_404(user_id)
        
        # No permitir desactivar al propio admin o al último admin
        if user.id == current_user.id:
            flash('No puedes desactivar tu propia cuenta', 'danger')
        elif user.role == 'admin' and User.query.filter_by(role='admin', is_active=True).count() == 1:
            flash('No puedes desactivar el último administrador', 'danger')
        else:
            user.is_active = not user.is_active
            db.session.commit()
            status = 'activado' if user.is_active else 'desactivado'
            flash(f'Usuario "{user.username}" {status}', 'success')
        
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    def delete_user(user_id):
        # Solo admin puede eliminar
        if current_user.role != 'admin':
            flash('No tienes permisos', 'danger')
            return redirect(url_for('products'))
        
        user = User.query.get_or_404(user_id)
        
        # No permitir eliminar al propio admin o al último admin
        if user.id == current_user.id:
            flash('No puedes eliminar tu propia cuenta', 'danger')
        elif user.role == 'admin' and User.query.filter_by(role='admin').count() == 1:
            flash('No puedes eliminar el último administrador', 'danger')
        else:
            try:
                # Eliminar movimientos del usuario
                Movement.query.filter_by(user_id=user.id).delete(synchronize_session=False)
                db.session.delete(user)
                db.session.commit()
                flash(f'Usuario "{user.username}" eliminado', 'success')
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f'Error al eliminar el usuario: {str(e)}', 'danger')
        
        return redirect(url_for('admin_users'))

    @app.route('/products', methods=['GET', 'POST'])
    @login_required
    def products():
        if request.method == 'POST':
            name = request.form.get('name')
            sku = request.form.get('sku')
            category = request.form.get('category', 'General')
            price = float(request.form.get('price') or 0)
            qty = int(request.form.get('quantity') or 0)
            min_stock = int(request.form.get('min_stock') or 5)
            
            if not name:
                flash('El nombre es requerido', 'danger')
            else:
                p = Product(name=name, sku=sku, category=category, price=price, stock=qty, min_stock=min_stock)
                db.session.add(p)
                db.session.commit()
                flash('Producto agregado', 'success')
                return redirect(url_for('products'))
        
        products = Product.query.order_by(Product.name).all()
        return render_template('products.html', products=products)

    @app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_product(product_id):
        p = Product.query.get_or_404(product_id)
        if request.method == 'POST':
            p.name = request.form.get('name')
            p.sku = request.form.get('sku')
            p.category = request.form.get('category', 'General')
            p.price = float(request.form.get('price') or 0)
            p.min_stock = int(request.form.get('min_stock') or 5)
            db.session.commit()
            flash('Producto actualizado', 'success')
            return redirect(url_for('products'))
        return render_template('edit_product.html', product=p)

    @app.route('/product/<int:product_id>/delete', methods=['POST'])
    @login_required
    def delete_product(product_id):
        # Solo admin puede eliminar
        if current_user.role != 'admin':
            flash('No tienes permisos para eliminar', 'danger')
            return redirect(url_for('products'))
        
        p = Product.query.get_or_404(product_id)
        try:
            # Borrar movimientos relacionados primero para evitar problemas de FK
            Movement.query.filter_by(product_id=p.id).delete(synchronize_session=False)
            db.session.delete(p)
            db.session.commit()
            flash('Producto eliminado', 'info')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'No se pudo eliminar el producto: {e}', 'danger')
        return redirect(url_for('products'))

    @app.route('/movements', methods=['GET', 'POST'])
    @login_required
    def movements():
        if request.method == 'POST':
            product_id = int(request.form.get('product_id'))
            m_type = request.form.get('type')
            qty = int(request.form.get('quantity') or 0)
            price = float(request.form.get('price') or 0)
            note = request.form.get('note')
            product = Product.query.get_or_404(product_id)
            if m_type == 'sale' and product.stock < qty:
                flash('Stock insuficiente para la venta', 'danger')
            else:
                movement = Movement(product_id=product.id, user_id=current_user.id, type=m_type, quantity=qty, price=price, note=note, timestamp=datetime.utcnow())
                if m_type == 'purchase':
                    product.stock += qty
                elif m_type == 'sale':
                    product.stock -= qty
                elif m_type == 'adjust':
                    product.stock += qty
                db.session.add(movement)
                db.session.commit()
                flash('Movimiento guardado', 'success')
                return redirect(url_for('movements'))
        products = Product.query.order_by(Product.name).all()
        movements = Movement.query.order_by(Movement.timestamp.desc()).limit(200).all()
        return render_template('movements.html', products=products, movements=movements)

    @app.route('/report')
    @login_required
    def report():
        products = Product.query.order_by(Product.name).all()
        total_value = sum([p.stock * p.price for p in products])
        
        # Alertas de stock bajo
        low_stock_products = [p for p in products if p.stock < p.min_stock]
        
        # Calcular ganancias por ventas
        all_movements = Movement.query.all()
        
        total_sales = sum([m.quantity * m.price for m in all_movements if m.type == 'sale'])
        total_purchases = sum([m.quantity * m.price for m in all_movements if m.type == 'purchase'])
        
        sales_movements = [m for m in all_movements if m.type == 'sale']
        sales_movements.sort(key=lambda x: x.timestamp, reverse=True)
        
        return render_template(
            'report.html', 
            products=products, 
            total_value=total_value, 
            low_stock_products=low_stock_products,
            total_sales=total_sales,
            total_purchases=total_purchases,
            sales_movements=sales_movements
        )

    @app.route('/quick-sale/<int:product_id>/<int:quantity>')
    def quick_sale(product_id, quantity=1):
        """Registrar venta rápida por escaneo QR - con autenticación integrada"""
        try:
            product = Product.query.get_or_404(product_id)
            
            # Si no está autenticado, mostrar formulario de login integrado
            if not current_user.is_authenticated:
                return render_template(
                    'quick_sale_login.html',
                    product_id=product_id,
                    quantity=quantity,
                    product=product
                )
            
            # Validar stock
            if product.stock < quantity:
                return render_template(
                    'quick_sale_result.html',
                    success=False,
                    message=f'Stock insuficiente. Disponibles: {product.stock}, Solicitados: {quantity}',
                    product=product
                )
            
            # Registrar movimiento CON el usuario autenticado
            movement = Movement(
                product_id=product.id,
                user_id=current_user.id,  # Ahora sí registra el usuario
                type='sale',
                quantity=quantity,
                price=product.price,
                note=f'Venta registrada por {current_user.username} (QR)',
                timestamp=datetime.utcnow()
            )
            
            # Actualizar stock
            product.stock -= quantity
            
            db.session.add(movement)
            db.session.commit()
            
            total = quantity * product.price
            
            return render_template(
                'quick_sale_result.html',
                success=True,
                product=product,
                quantity=quantity,
                total=total,
                vendor=current_user.username,
                message=f'¡Venta registrada! {quantity}x {product.name} = ${total:.2f}'
            )
        
        except Exception as e:
            return render_template(
                'quick_sale_result.html',
                success=False,
                message=f'Error: {str(e)}'
            )

    @app.route('/mobile/quick-sale-process', methods=['POST'])
    def mobile_quick_sale_process():
        """Procesar login + venta rápida desde móvil (escaneo QR)"""
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            product_id = request.form.get('product_id')
            quantity = int(request.form.get('quantity', 1))
            
            # Validar credenciales
            user = User.query.filter_by(username=username).first()
            if not user or not user.check_password(password):
                return render_template(
                    'quick_sale_login.html',
                    error='Usuario o contraseña inválidos',
                    product_id=product_id,
                    quantity=quantity,
                    product=Product.query.get(product_id)
                )
            
            if not user.is_active:
                return render_template(
                    'quick_sale_login.html',
                    error='Tu cuenta ha sido desactivada',
                    product_id=product_id,
                    quantity=quantity,
                    product=Product.query.get(product_id)
                )
            
            # Procesar venta con el usuario autenticado
            product = Product.query.get_or_404(product_id)
            
            # Validar stock
            if product.stock < quantity:
                return render_template(
                    'quick_sale_result.html',
                    success=False,
                    message=f'Stock insuficiente. Disponibles: {product.stock}, Solicitados: {quantity}',
                    product=product
                )
            
            # Registrar movimiento
            movement = Movement(
                product_id=product.id,
                user_id=user.id,
                type='sale',
                quantity=quantity,
                price=product.price,
                note=f'Venta registrada por {user.username} (QR Móvil)',
                timestamp=datetime.utcnow()
            )
            
            # Actualizar stock
            product.stock -= quantity
            
            db.session.add(movement)
            db.session.commit()
            
            total = quantity * product.price
            
            return render_template(
                'quick_sale_result.html',
                success=True,
                product=product,
                quantity=quantity,
                total=total,
                vendor=user.username,
                message=f'¡Venta registrada! {quantity}x {product.name} = ${total:.2f}'
            )
        
        except Exception as e:
            return render_template(
                'quick_sale_result.html',
                success=False,
                message=f'Error: {str(e)}'
            )

    @app.route('/product/<int:product_id>/qr')
    @login_required
    def generate_qr(product_id):
        """Mostrar código QR en HTML"""
        p = Product.query.get_or_404(product_id)
        
        # Determinar el host correcto para el QR
        host = request.host
        
        # Si accede desde localhost, usar IP local en su lugar
        if 'localhost' in host or '127.0.0.1' in host:
            local_ip = get_local_ip()
            # Reemplazar el puerto si está presente
            port = request.host.split(':')[1] if ':' in request.host else '5000'
            host = f"{local_ip}:{port}"
        
        protocol = 'https' if request.is_secure or host.endswith('.ngrok.io') else 'http'
        qr_url = f"{protocol}://{host}" + url_for('quick_sale', product_id=p.id, quantity=1)
        
        return render_template('qr_view.html', product=p, qr_data=qr_url, qr_url=qr_url)
    
    @app.route('/product/<int:product_id>/qr/download')
    @login_required
    def download_qr(product_id):
        """Descargar código QR como imagen PNG"""
        p = Product.query.get_or_404(product_id)
        
        # Determinar el host correcto para el QR
        host = request.host
        
        # Si accede desde localhost, usar IP local en su lugar
        if 'localhost' in host or '127.0.0.1' in host:
            local_ip = get_local_ip()
            # Reemplazar el puerto si está presente
            port = request.host.split(':')[1] if ':' in request.host else '5000'
            host = f"{local_ip}:{port}"
        
        protocol = 'https' if request.is_secure or host.endswith('.ngrok.io') else 'http'
        qr_url = f"{protocol}://{host}" + url_for('quick_sale', product_id=p.id, quantity=1)
        
        # Generar QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        img_io = io.BytesIO()
        img.save(img_io, 'PNG', quality=95)
        img_io.seek(0)
        
        filename = f"QR_{p.name.replace(' ', '_')}_{product_id}.png"
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=filename)

    return app

if __name__ == '__main__':
    app = create_app()
    
    # En producción (Railway), usar el puerto de la variable de entorno
    # En desarrollo, usar puerto 5000
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    
    if debug_mode:
        local_ip = get_local_ip()
        print(f"\n✅ Servidor iniciado correctamente")
        print(f"📍 Acceso local: http://localhost:{port}")
        print(f"🌐 Acceso desde otras máquinas: http://{local_ip}:{port}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)

# Exponer un callable WSGI para servidores (Waitress, uwsgi, etc.)
# Esto permite usar `waitress-serve app:app` o `waitress-serve app:application`
app = create_app()
application = app
