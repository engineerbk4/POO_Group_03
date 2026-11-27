"""RepositorioPuntajes: persistencia local del Top 5 en JSON.

Responsabilidad única: leer y escribir ``data/high_scores.json``. Los errores
de disco se traducen a ``PersistenciaError`` y el archivo corrupto se
respalda y se reemplaza, así el juego nunca se cae por un problema de datos.

Cada registro guarda: jugador (Nombre del Piloto), puntaje, universidad, país
y fecha. Los archivos antiguos sin el campo ``jugador`` siguen siendo válidos
(se leen como "Explorador").
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src import config
from src.excepciones import PersistenciaError

JUGADOR_POR_DEFECTO: str = "Explorador"
JUGADOR_MAX_CARACTERES: int = 14


def normalizarJugador(nombre: object) -> str:
    """Deja solo letras/números/espacios, colapsa espacios, recorta a 14 y aplica el valor por defecto."""
    texto = "".join(c for c in str(nombre) if c.isalnum() or c == " ")
    texto = " ".join(texto.split())[:JUGADOR_MAX_CARACTERES].strip()
    return texto or JUGADOR_POR_DEFECTO


@dataclass(frozen=True)
class RegistroPuntaje:
    puntaje: int
    universidad: str
    pais: str
    fecha: str
    jugador: str = JUGADOR_POR_DEFECTO

    def aDiccionario(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def desdeDiccionario(datos: Dict[str, Any]) -> "RegistroPuntaje":
        puntaje = int(datos["puntaje"])
        universidad = str(datos["universidad"])
        pais = str(datos["pais"])
        fecha = str(datos["fecha"])
        jugador = normalizarJugador(datos.get("jugador") or "")
        return RegistroPuntaje(puntaje, universidad, pais, fecha, jugador)


class RepositorioPuntajes:
    def __init__(self, ruta: Union[str, Path] = config.RUTA_PUNTAJES,
                 maximo: int = config.MAX_PUNTAJES) -> None:
        if maximo <= 0:
            raise ValueError("maximo debe ser positivo")
        self.__ruta: Path = Path(ruta)
        self.__maximo: int = maximo

    def getRuta(self) -> Path:
        return self.__ruta

    # ---- lectura ----
    def cargar(self) -> List[RegistroPuntaje]:
        try:
            with open(self.__ruta, encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except FileNotFoundError:
            return []                                # primera ejecución: aún no hay ranking
        except PermissionError as error:
            raise PersistenciaError(f"sin permiso para leer {self.__ruta}") from error
        except json.JSONDecodeError:
            self.__respaldarCorrupto()
            return []
        except OSError as error:
            raise PersistenciaError(f"no se pudo leer {self.__ruta}: {error}") from error
        else:
            return self.__ordenar(self.__interpretar(datos))

    def top(self) -> List[RegistroPuntaje]:
        return self.cargar()[:self.__maximo]

    def mejorPuntaje(self) -> int:
        lista = self.cargar()
        return lista[0].puntaje if lista else 0

    # ---- escritura ----
    def registrar(self, puntaje: int, universidad: str, pais: str,
                  reemplaza: Optional[RegistroPuntaje] = None,
                  jugador: str = JUGADOR_POR_DEFECTO) -> RegistroPuntaje:
        """Agrega un puntaje y conserva solo el Top N.

        ``reemplaza`` permite sustituir el registro previo de la misma partida
        (cuando el jugador reintenta un nivel tras perder) sin duplicarla.
        ``jugador`` es el Nombre del Piloto (se normaliza: máx. 14 caracteres).
        """
        if puntaje < 0:
            raise ValueError("el puntaje no puede ser negativo")
        nuevo = RegistroPuntaje(int(puntaje), universidad, pais,
                                datetime.now().isoformat(timespec="seconds"),
                                normalizarJugador(jugador))
        lista = self.cargar()
        if reemplaza is not None and reemplaza in lista:
            lista.remove(reemplaza)
        lista.append(nuevo)
        self.__guardar(self.__ordenar(lista)[:self.__maximo])
        return nuevo

    def __guardar(self, registros: List[RegistroPuntaje]) -> None:
        try:
            self.__ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self.__ruta, "w", encoding="utf-8") as archivo:
                json.dump([r.aDiccionario() for r in registros], archivo,
                          indent=2, ensure_ascii=False)
        except PermissionError as error:
            raise PersistenciaError(f"sin permiso para escribir {self.__ruta}") from error
        except OSError as error:
            raise PersistenciaError(f"no se pudo escribir {self.__ruta}: {error}") from error

    # ---- utilidades ----
    @staticmethod
    def __interpretar(datos: Any) -> List[RegistroPuntaje]:
        registros: List[RegistroPuntaje] = []
        if not isinstance(datos, list):
            return registros
        for item in datos:
            try:
                registros.append(RegistroPuntaje.desdeDiccionario(item))
            except (KeyError, TypeError, ValueError, AttributeError):
                continue                             # entrada dañada: se descarta
        return registros

    @staticmethod
    def __ordenar(registros: List[RegistroPuntaje]) -> List[RegistroPuntaje]:
        return sorted(registros, key=lambda r: (-r.puntaje, r.fecha))

    def __respaldarCorrupto(self) -> None:
        try:
            self.__ruta.replace(self.__ruta.with_suffix(".corrupto.json"))
        except OSError:
            pass
