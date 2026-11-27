"""APIClient: toda la comunicación HTTP del juego vive en esta clase.

* Alta cohesión comunicacional: cada método trabaja sobre el mismo dato
  externo (la lista de universidades) y nada más.
* Acoplamiento de datos con ``Juego``: hacia afuera solo salen tipos simples
  (``str`` y ``List[str]``). Nunca se expone una respuesta HTTP ni una
  excepción de red: los errores se traducen a ``APIError``.
* El juego jamás se bloquea: la consulta corre en un hilo, con timeout de
  3 s, y si falla se usa una lista de respaldo offline (que incluye la UPCH).
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from typing import Any, Callable, List, Optional

from src import config
from src.excepciones import APIError


class APIClient:
    CARGANDO: str = "CARGANDO"
    EN_LINEA: str = "EN_LINEA"
    OFFLINE: str = "OFFLINE"

    LISTA_RESPALDO: List[str] = [
        "Universidad Peruana Cayetano Heredia",
        "Pontificia Universidad Católica del Perú",
        "Universidad Nacional Mayor de San Marcos",
        "Universidad Nacional de Ingeniería",
        "Universidad Peruana de Ciencias Aplicadas",
        "Universidad de Lima",
        "Universidad del Pacífico",
        "Universidad de Ingeniería y Tecnología",
        "Universidad de San Martín de Porres",
    ]
    PRIORITARIA: str = config.UNIVERSIDAD_POR_DEFECTO
    MAX_UNIVERSIDADES: int = 25

    def __init__(self, url: str = config.API_URL, timeout: float = config.API_TIMEOUT,
                 abridor: Optional[Callable[..., Any]] = None) -> None:
        self.__url: str = url
        self.__timeout: float = timeout
        # inyectable para poder simular la red en las pruebas
        self.__abridor: Callable[..., Any] = abridor or urllib.request.urlopen
        self.__candado: threading.Lock = threading.Lock()
        self.__universidades: List[str] = list(self.LISTA_RESPALDO)
        self.__estado: str = self.CARGANDO
        self.__ultimoError: str = ""
        self.__hilo: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Capa de red (puede lanzar APIError)
    # ------------------------------------------------------------------
    def consultarUniversidades(self) -> List[str]:
        """Consulta la API real. Lanza ``APIError`` ante cualquier fallo."""
        peticion = urllib.request.Request(
            self.__url, headers={"User-Agent": "MisionEnMarte/1.0", "Accept": "application/json"})
        respuesta: Any = None
        try:
            respuesta = self.__abridor(peticion, timeout=self.__timeout)
            texto = respuesta.read().decode("utf-8")
            datos = json.loads(texto)
        except urllib.error.HTTPError as error:        # antes que URLError: es su subclase
            raise APIError(f"la API respondió con error HTTP {error.code}") from error
        except urllib.error.URLError as error:
            raise APIError(f"no se pudo conectar con la API: {error.reason}") from error
        except TimeoutError as error:
            raise APIError(f"la API no respondió en {self.__timeout} s") from error
        except json.JSONDecodeError as error:
            raise APIError("la API devolvió un JSON inválido") from error
        except (OSError, ValueError) as error:         # red cortada, bytes inválidos, etc.
            raise APIError(f"respuesta ilegible de la API: {error}") from error
        else:
            return self.__extraerNombres(datos)
        finally:
            cerrar = getattr(respuesta, "close", None)
            if callable(cerrar):
                cerrar()

    def __extraerNombres(self, datos: Any) -> List[str]:
        if not isinstance(datos, list):
            raise APIError("formato inesperado: se esperaba una lista de universidades")
        nombres: List[str] = []
        for item in datos:
            nombre = item.get("name") if isinstance(item, dict) else None
            if isinstance(nombre, str) and nombre.strip() and nombre.strip() not in nombres:
                nombres.append(nombre.strip())
        if not nombres:
            raise APIError("la API no devolvió universidades")
        return self.__priorizar(nombres)

    def __priorizar(self, nombres: List[str]) -> List[str]:
        """UPCH primero, luego las conocidas del respaldo y luego el resto alfabético."""
        conocidas = [n for n in self.LISTA_RESPALDO if n in nombres and n != self.PRIORITARIA]
        resto = sorted(n for n in nombres if n not in conocidas and n != self.PRIORITARIA)
        lista = [self.PRIORITARIA] + conocidas + resto
        return lista[:self.MAX_UNIVERSIDADES]

    # ------------------------------------------------------------------
    # Capa segura (nunca lanza): la que usa el juego
    # ------------------------------------------------------------------
    def cargar(self) -> List[str]:
        """Intenta la API y, si falla, deja activa la lista offline. Nunca lanza."""
        try:
            lista = self.consultarUniversidades()
        except APIError as error:
            with self.__candado:
                self.__universidades = list(self.LISTA_RESPALDO)
                self.__estado = self.OFFLINE
                self.__ultimoError = str(error)
        else:
            with self.__candado:
                self.__universidades = lista
                self.__estado = self.EN_LINEA
                self.__ultimoError = ""
        return self.universidades()

    def iniciarCargaAsincrona(self) -> None:
        """Lanza ``cargar`` en un hilo para no congelar la ventana al arrancar."""
        if self.__hilo is not None and self.__hilo.is_alive():
            return
        self.__hilo = threading.Thread(target=self.cargar, name="api-universidades", daemon=True)
        self.__hilo.start()

    def esperarCarga(self, timeout: Optional[float] = None) -> None:
        if self.__hilo is not None:
            self.__hilo.join(timeout)

    # ---- consultas de estado (solo tipos simples) ----
    def universidades(self) -> List[str]:
        with self.__candado:
            return list(self.__universidades)

    def estado(self) -> str:
        with self.__candado:
            return self.__estado

    def ultimoError(self) -> str:
        with self.__candado:
            return self.__ultimoError
