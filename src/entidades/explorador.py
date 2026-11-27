"""Explorador: el personaje que controla el jugador."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, Tuple

import pygame

from src.entidades.entidad_juego import EntidadJuego
from src.graficos import dibujar_explorador
from src.patrones.observer import EventoDominio, Sujeto

if TYPE_CHECKING:  # solo para anotaciones (evita imports circulares)
    from src.entidades.base import Base
    from src.entidades.mineral import Mineral


class Explorador(EntidadJuego, Sujeto):
    """Personaje del jugador. Además es un *Sujeto* observable (patrón Observer):
    avisa ``SALUD_CAMBIADA``, ``MINERAL_RECOLECTADO`` y ``BASE_CONSTRUIDA``."""

    COSTO_BASE: int = 3

    def __init__(self, x: float, y: float) -> None:
        EntidadJuego.__init__(self, x, y, 100, "explorador", 16)
        Sujeto.__init__(self)
        self.__inventarioMinerales: int = 0
        self.__velocidad: float = 230.0
        self.__direccion: Tuple[float, float] = (0.0, 0.0)
        self.__orientacion: Tuple[float, float] = (1.0, 0.0)   # hacia dónde mira el casco

    def getInventarioMinerales(self) -> int:
        return self.__inventarioMinerales

    def estaMoviendose(self) -> bool:
        return self.__direccion != (0.0, 0.0)

    def establecerDireccion(self, dx: float, dy: float) -> None:
        norma = math.hypot(dx, dy)
        self.__direccion = (dx / norma, dy / norma) if norma > 0 else (0.0, 0.0)
        if norma > 0:
            self.__orientacion = self.__direccion

    def almacenar(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("cantidad debe ser positiva")
        self.__inventarioMinerales += cantidad

    def gastarMinerales(self, cantidad: int) -> bool:
        if cantidad <= 0 or cantidad > self.__inventarioMinerales:
            return False
        self.__inventarioMinerales -= cantidad
        return True

    def recolectar(self, m: Mineral) -> None:
        """DEPENDENCIA ``<<use>>`` (Explorador ..> Mineral).

        El Explorador usa al Mineral solo durante este método (lo recibe como
        parámetro) y NO conserva ninguna referencia a él: no es asociación ni
        agregación. Sí guarda el *valor* recolectado en su inventario.
        """
        valor = m.getValorCombustible()
        m.serRecolectado()
        self.almacenar(valor)
        self.notificar(EventoDominio.MINERAL_RECOLECTADO,
                       {"valor": valor, "inventario": self.__inventarioMinerales})

    def construirBase(self) -> Optional[Base]:
        """DEPENDENCIA ``<<create>>`` (Explorador ..> Base): crea una Base si alcanzan los minerales."""
        if not self.gastarMinerales(self.COSTO_BASE):
            return None
        from src.entidades.base import Base  # import local: evita el ciclo Explorador <-> Base
        base = Base(self._position_x, self._position_y, self)
        self.notificar(EventoDominio.BASE_CONSTRUIDA, {"x": round(self._position_x), "y": round(self._position_y)})
        return base

    # ---- la salud cambia en la clase base; aquí solo se avisa a los observadores ----
    def recibirDano(self, cantidad: int) -> None:
        antes = self.getSalud()
        super().recibirDano(cantidad)
        self.__avisarSalud(self.getSalud() - antes)

    def curar(self, cantidad: int) -> None:
        antes = self.getSalud()
        super().curar(cantidad)
        self.__avisarSalud(self.getSalud() - antes)

    def __avisarSalud(self, delta: int) -> None:
        if delta != 0:
            self.notificar(EventoDominio.SALUD_CAMBIADA,
                           {"salud": self.getSalud(), "maxima": self.getSaludMaxima(), "delta": delta})

    def update(self, dt: float) -> None:
        super().update(dt)
        dx, dy = self.__direccion
        paso = self.__velocidad * self.getFactorVelocidad() * dt
        self.setPosicion(self._position_x + dx * paso, self._position_y + dy * paso)

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        dibujar_explorador(pantalla, self._position_x, self._position_y, self._radio,
                           self._tiempo, self.estaMoviendose(), self.__orientacion)
