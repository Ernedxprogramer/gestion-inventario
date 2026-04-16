from app import create_app, get_local_ip
import os
from waitress import serve

app = create_app()

if __name__ == '__main__':
    # Modo desarrollo local
    local_ip = get_local_ip()
    print(f"\n✅ Servidor iniciado correctamente")
    print(f"📍 Acceso local: http://localhost:5000")
    print(f"📱 Acceso desde red: http://{local_ip}:5000")
    print(f"📲 Escanea el QR con tu teléfono para registrar ventas\n")
    serve(app, host='0.0.0.0', port=5000)
else:
    # Modo producción (Gunicorn/plataformas de hosting)
    pass
