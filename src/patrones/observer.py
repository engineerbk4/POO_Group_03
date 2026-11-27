"""Patrón Observer: notificación de eventos del dominio sin acoplamiento.

Roles del patrón
----------------
* ``Observador``  (interfaz)         -> ``actualizar(evento, datos)``
* ``Sujeto``      (mixin observable) -> ``suscribir / desuscribir / notificar``
* Sujetos concretos:      ``Explorador`` y ``Nivel``
* Observadores concretos: ``ObservadorHUD``, ``ObservadorLogger`` y ``ObservadorAudio``

El sujeto NO conoce a sus observadores concretos: solo guarda referencias a la
interfaz ``Observador`` (bajo acoplamiento, Open/Closed: agregar un observador
nuevo no modifica al sujeto). Los observadores reaccionan a los eventos en el
momento en que ocurren, sin hacer *polling* sobre el estado del juego.
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from src.servicios.gestor_audio import GestorAudio

Color = Tuple[int, int, int]


class EventoDominio:
    """Catálogo de eventos del dominio (constantes de solo lectura)."""
    SALUD_CAMBIADA: str = "SALUD_CAMBIADA"
    MINERAL_RECOLECTADO: str = "MINERAL_RECOLECTADO"
    BASE_CONSTRUIDA: str = "BASE_CONSTRUIDA"
    MARCIANO_ALIADO: str = "MARCIANO_ALIADO"
    NIVEL_COMPLETADO: str = "NIVEL_COMPLETADO"
    JUGADOR_DERROTADO: str = "JUGADOR_DERROTADO"


# ----------------------------------------------------------------------
# Interfaz y sujeto
# ----------------------------------------------------------------------
class Observador(ABC):
    """Interfaz que implementan quienes quieren enterarse de los eventos."""

    @abstractmethod
    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        ...


class Sujeto:
    """Mixin observable. Las clases hijas deben llamar a ``Sujeto.__init__(self)``."""

    def __init__(self) -> None:
        self.__observadores: List[Observador] = []

    def suscribir(self, observador: Observador) -> None:
        if observador not in self.__observadores:
            self.__observadores.append(observador)

    def desuscribir(self, observador: Observador) -> None:
        if observador in self.__observadores:
            self.__observadores.remove(observador)

    def cantidadObservadores(self) -> int:
        return len(self.__observadores)

    def notificar(self, evento: str, datos: Optional[Dict[str, Any]] = None) -> None:
        # copia de la lista: un observador puede desuscribirse mientras se notifica
        for observador in list(self.__observadores):
            observador.actualizar(evento, dict(datos or {}))


# ----------------------------------------------------------------------
# Observador 1: HUD (mensajes flotantes)
# ----------------------------------------------------------------------
@dataclass
class MensajeFlotante:
    texto: str
    color: Color
    restante: float
    total: float

    def opacidad(self) -> float:
        """1.0 al aparecer, baja a 0.0 en el último medio segundo."""
        return max(0.0, min(1.0, self.restante / 0.5))


class ObservadorHUD(Observador):
    """Convierte eventos del dominio en alertas visibles en pantalla.

    No dibuja nada: solo mantiene la cola de mensajes. ``InterfazJuego`` la lee
    para renderizarla, de modo que modelo y vista siguen desacoplados.
    """

    DURACION: float = 2.4

    def __init__(self, maxMensajes: int = 4, umbralImpacto: int = 15,
                 umbralCritico: int = 30) -> None:
        self.__mensajes: List[MensajeFlotante] = []
        self.__maxMensajes: int = maxMensajes
        self.__umbralImpacto: int = umbralImpacto
        self.__umbralCritico: int = umbralCritico
        self.__reloj: float = 0.0
        self.__ultimoAvisoCritico: float = -99.0

    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        if evento == EventoDominio.SALUD_CAMBIADA:
            self.__alCambiarSalud(datos)
        elif evento == EventoDominio.MINERAL_RECOLECTADO:
            self.__agregar(f"+{datos.get('valor', 1)} mineral", (110, 240, 225))
        elif evento == EventoDominio.BASE_CONSTRUIDA:
            self.__agregar("Base construida: escudo y refugio activos", (150, 210, 255))
        elif evento == EventoDominio.MARCIANO_ALIADO:
            self.__agregar("¡Un marciano se unió como aliado!", (130, 255, 170))
        elif evento == EventoDominio.NIVEL_COMPLETADO:
            self.__agregar("¡Objetivo cumplido!", (120, 255, 150))
        elif evento == EventoDominio.JUGADOR_DERROTADO:
            self.__agregar("El explorador ha caído...", (255, 110, 110))

    def __alCambiarSalud(self, datos: Dict[str, Any]) -> None:
        delta = int(datos.get("delta", 0))
        salud = int(datos.get("salud", 0))
        if delta <= -self.__umbralImpacto:
            self.__agregar(f"¡Impacto! {delta} HP", (255, 150, 90))
        if delta < 0 and 0 < salud <= self.__umbralCritico \
                and self.__reloj - self.__ultimoAvisoCritico > 4.0:
            self.__ultimoAvisoCritico = self.__reloj
            self.__agregar("¡Salud crítica! Busca una base o un aliado", (255, 90, 90))

    def __agregar(self, texto: str, color: Color) -> None:
        self.__mensajes.append(MensajeFlotante(texto, color, self.DURACION, self.DURACION))
        del self.__mensajes[:-self.__maxMensajes]

    def avanzar(self, dt: float) -> None:
        self.__reloj += dt
        for m in self.__mensajes:
            m.restante -= dt
        self.__mensajes = [m for m in self.__mensajes if m.restante > 0]

    def getMensajes(self) -> List[MensajeFlotante]:
        return list(self.__mensajes)

    def limpiar(self) -> None:
        self.__mensajes.clear()


# ----------------------------------------------------------------------
# Observador 2: Logger (archivo + consola)
# ----------------------------------------------------------------------
class ObservadorLogger(Observador):
    """Registra cada evento con marca de tiempo en ``logs/partida.log``."""

    def __init__(self, ruta: Union[str, Path], consola: bool = False,
                 umbralSalud: int = 5) -> None:
        self.__ruta: Path = Path(ruta)
        self.__consola: bool = consola
        self.__umbralSalud: int = umbralSalud   # ignora curas/daños diminutos (ruido)
        self.__fallosEscritura: int = 0

    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        if evento == EventoDominio.SALUD_CAMBIADA \
                and abs(int(datos.get("delta", 0))) < self.__umbralSalud:
            return
        marca = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        detalle = json.dumps(datos, ensure_ascii=False, default=str, sort_keys=True)
        linea = f"{marca} | {evento} | {detalle}"
        if self.__consola:
            print(linea)
        self.__escribir(linea)

    def __escribir(self, linea: str) -> None:
        try:
            self.__ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(self.__ruta, "a", encoding="utf-8") as archivo:
                archivo.write(linea + "\n")
        except OSError as error:
            # el log es secundario: jamás debe tumbar la partida
            self.__fallosEscritura += 1
            if self.__fallosEscritura == 1:
                print(f"[logger] no se pudo escribir en {self.__ruta}: {error}")

    def getRuta(self) -> Path:
        return self.__ruta


# ----------------------------------------------------------------------
# Observador 3: Audio (efectos de sonido)
# ----------------------------------------------------------------------
class ObservadorAudio(Observador):
    """Traduce eventos del dominio a efectos de sonido (vía ``GestorAudio``)."""

    def __init__(self, audio: GestorAudio, pausaDano: float = 0.25) -> None:
        self.__audio: GestorAudio = audio
        self.__pausaDano: float = pausaDano
        self.__ultimoDano: float = -99.0

    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        if evento == EventoDominio.SALUD_CAMBIADA:
            ahora = time.monotonic()
            if int(datos.get("delta", 0)) < 0 and ahora - self.__ultimoDano >= self.__pausaDano:
                self.__ultimoDano = ahora      # la radiación daña cada frame: se limita
                self.__audio.reproducir("dano")
        elif evento == EventoDominio.MINERAL_RECOLECTADO:
            self.__audio.reproducir("mineral")
        elif evento == EventoDominio.BASE_CONSTRUIDA:
            self.__audio.reproducir("base")
        elif evento == EventoDominio.MARCIANO_ALIADO:
            self.__audio.reproducir("aliado")
        elif evento == EventoDominio.NIVEL_COMPLETADO:
            self.__audio.reproducir("nivel")
        elif evento == EventoDominio.JUGADOR_DERROTADO:
            self.__audio.reproducir("gameover")
