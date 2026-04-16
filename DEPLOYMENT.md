# Configuración de Despliegue desde GitHub

## 📋 Requisitos

Para desplegar desde GitHub, necesitas una plataforma compatible como:
- **Render** (recomendado)
- **Heroku**
- **Railway**
- **Fly.io**

## 🚀 Pasos para Desplegar en Render

### 1. Prepara el Repositorio
Tu repositorio ya está configurado con:
- ✅ `Procfile` - Define cómo ejecutar la aplicación
- ✅ `requirements.txt` - Dependencias de Python
- ✅ `runtime.txt` - Versión de Python
- ✅ `wsgi.py` - Punto de entrada para Gunicorn
- ✅ `.github/workflows/deploy.yml` - CI/CD automático

### 2. Conecta tu Repositorio a Render
1. Ve a [render.com](https://render.com)
2. Crea una cuenta o inicia sesión
3. Haz clic en "New +" → "Web Service"
4. Selecciona "Connect repository"
5. Autoriza GitHub y selecciona tu repositorio
6. Configura:
   - **Name**: `gestion-inventario`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`

### 3. Configura Variables de Entorno
En el dashboard de Render, ve a "Environment" y añade:

```
SECRET_KEY=tu_clave_secreta_aqui
DATABASE_URL=postgresql://usuario:contraseña@host:puerto/nombre_bd
```

### 4. Despliega
- Haz push a `main` en GitHub
- Render automáticamente construirá y desplegará
- El CD automático se encarga del resto

## 📤 Variables de Entorno Requeridas

```env
SECRET_KEY=generada-automaticamente-por-defecto
DATABASE_URL=postgresql://usuario:password@host:5432/database
```

## 🔄 Despliegue Automático

Cada vez que hagas push a la rama `main`:
1. GitHub Actions ejecuta tests
2. Si todo OK, dispara el webhook de Render
3. Render automáticamente redeploy del proyecto

## 📝 Cambios Realizados

- Reemplazado `waitress` con `gunicorn` (servidor estándar para producción)
- Actualizado `Procfile` para usar Gunicorn
- Añadido workflow de GitHub Actions para CI/CD
- Añadido `psycopg2-binary` para soporte PostgreSQL

## 🔐 Seguridad

- Nunca commitees `.env` o archivos con secretos
- Usa "Environment secrets" en la plataforma de hosting
- La `SECRET_KEY` se genera automáticamente
