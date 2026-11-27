"""Constantes globales del juego 'Misión en Marte' (solo lectura)."""
from pathlib import Path

ANCHO: int = 960
ALTO: int = 640
HUD_ALTO: int = 52
FPS: int = 60
TITULO: str = "Misión en Marte"

# Pon True para ver en consola cuándo se destruye cada entidad (__del__).
DEBUG_DESTRUCTORES: bool = False

# ---- rutas de datos (relativas a la raíz del proyecto) ----
RAIZ: Path = Path(__file__).resolve().parent.parent
RUTA_PUNTAJES: Path = RAIZ / "data" / "high_scores.json"
RUTA_LOG: Path = RAIZ / "logs" / "partida.log"

# ---- API externa y ranking ----
API_URL: str = "http://universities.hipolabs.com/search?country=Peru"
API_TIMEOUT: float = 3.0
PAIS: str = "Peru"
UNIVERSIDAD_POR_DEFECTO: str = "Universidad Peruana Cayetano Heredia"
MAX_PUNTAJES: int = 5
