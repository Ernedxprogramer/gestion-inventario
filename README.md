# Sistema simple de gestión de inventario

Pequeña aplicación web para gestionar productos, compras, ventas y movimientos.

Requisitos
- Python 3.8+
- Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar

```bash
python "app.py"
```

Abrir en el navegador: http://127.0.0.1:5000

Características
- Listar y crear productos
- Editar y eliminar productos
- Registrar compras, ventas y ajustes
- Reporte de inventario y valor total

Notas
- La base de datos es SQLite (`inventory.db`) creada automáticamente en el directorio del proyecto.
- Para producción cambie `SECRET_KEY` y use una base de datos más robusta.

Despliegue (producción)

- Se recomienda usar un servidor WSGI de producción como `waitress` en Windows.

Instalar dependencias (incluye `waitress`):

```powershell
pip install -r requirements.txt
```

Ejecutar con Waitress:

```powershell
waitress-serve --listen=*:5000 --call "app:create_app"
```

Recuerde cambiar `SECRET_KEY` antes de exponer la app y usar una base de datos adecuada.
