# Script para compilar el ejecutable con los templates incluidos

& "C:\Gestion de Inventario\.venv\Scripts\Activate.ps1"

cd 'C:\Gestion de Inventario'

# Limpiar builds anteriores
Remove-Item build -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item dist -Recurse -Force -ErrorAction SilentlyContinue

# Compilar con los templates incluidos
python -m PyInstaller `
    --onefile `
    --name gestion_inventario `
    --console `
    --add-data 'templates:templates' `
    wsgi.py

Write-Host "Compilacion completada!" -ForegroundColor Green
Write-Host "Ejecutable en: C:\Gestion de Inventario\dist\gestion_inventario.exe"
