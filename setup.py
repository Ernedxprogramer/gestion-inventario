from setuptools import setup
import py2exe
import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

setup(
    name='Gestion de Inventario',
    version='1.0',
    description='Sistema de Gestión de Inventario',
    author='Tu Nombre',
    
    console=[{
        'script': 'wsgi.py',
        'dest_base': 'gestion_inventario'
    }],
    
    options={
        'py2exe': {
            'packages': ['flask', 'flask_sqlalchemy', 'waitress', 'jinja2', 'sqlalchemy'],
            'includes': ['encodings', 'encodings.*'],
            'bundle_files': 1,
            'compressed': True,
        }
    },
    
    zipfile=None,
)
