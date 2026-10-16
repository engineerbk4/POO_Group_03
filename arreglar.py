import os
import shutil

os.makedirs('src/entidades', exist_ok=True)
os.makedirs('src/niveles', exist_ok=True)
os.makedirs('src/tormentas', exist_ok=True)

rutas = {
    'entidades.py': 'src/entidades/__init__.py',
    'niveles.py': 'src/niveles/__init__.py',
    'tormentas.py': 'src/tormentas/__init__.py',
    'juego.py': 'src/juego.py',
    'config.py': 'src/config.py',
    'graficos.py': 'src/graficos.py'
}

for origen, destino in rutas.items():
    if os.path.exists(origen):
        shutil.move(origen, destino)

archivos = [
    'main.py',
    'src/juego.py',
    'src/entidades/__init__.py',
    'src/niveles/__init__.py',
    'src/tormentas/__init__.py',
    'src/graficos.py'
]

reemplazos = {
    'import config': 'from src import config',
    'from graficos': 'from src.graficos',
    'from juego': 'from src.juego',
    'from entidades': 'from src.entidades',
    'from niveles': 'from src.niveles',
    'from tormentas': 'from src.tormentas'
}

for ruta in archivos:
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        for viejo, nuevo in reemplazos.items():
            contenido = contenido.replace(viejo, nuevo)
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)

print("¡Estructura replicada con éxito!")