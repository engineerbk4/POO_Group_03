"""Jerarquía de excepciones propias de 'Misión en Marte'.

Las capas de servicio (red y disco) traducen los errores de bajo nivel
(urllib, json, OSError) a estas excepciones de dominio, de modo que el resto
del juego nunca depende de detalles de infraestructura.
"""


class ErrorMisionMarte(Exception):
    """Excepción raíz del dominio del juego."""


class APIError(ErrorMisionMarte):
    """Falló la comunicación con la API externa (red, HTTP, timeout o JSON inválido)."""


class PersistenciaError(ErrorMisionMarte):
    """Falló la lectura o escritura de datos locales (permisos, disco, formato)."""
