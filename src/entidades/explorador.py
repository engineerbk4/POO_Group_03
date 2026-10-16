"""Explorador: el personaje que controla el jugador."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, Tuple

import pygame

from src.entidades.entidad_juego import EntidadJuego

if TYPE_CHECKING:  # solo para anotaciones (evita imports circulares)
    from src.entidades.base import Base
    from src.entidades.mineral import Mineral


class Explorador(EntidadJuego):
    COSTO_BASE: int = 3

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, 100, "explorador", 16)
        self.__inventarioMinerales: int = 0
        self.__velocidad: float = 230.0
        self.__direccion: Tuple[float, float] = (0.0, 0.0)

    def getInventarioMinerales(self) -> int:
        return self.__inventarioMinerales

    def establecerDireccion(self, dx: float, dy: float) -> None:
        norma = math.hypot(dx, dy)
        self.__direccion = (dx / norma, dy / norma) if norma > 0 else (0.0, 0.0)

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
        """AGREGACIÓN/USO: el mineral existe en el ecosistema, el explorador solo lo toma."""
        valor = m.getValorCombustible()
        m.serRecolectado()
        self.almacenar(valor)

    def construirBase(self) -> Optional[Base]:
        """DEPENDENCIA <<create>>: crea una Base si alcanzan los minerales."""
        if not self.gastarMinerales(self.COSTO_BASE):
            return None
        from src.entidades.base import Base  # import local: evita el ciclo Explorador <-> Base
        return Base(self._position_x, self._position_y, self)

    def update(self, dt: float) -> None:
        super().update(dt)
        dx, dy = self.__direccion
        self.setPosicion(self._position_x + dx * self.__velocidad * dt,
                         self._position_y + dy * self.__velocidad * dt)

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        cx, cy = int(self._position_x), int(self._position_y)
        pygame.draw.circle(pantalla, (235, 235, 245), (cx, cy), self._radio)
        pygame.draw.circle(pantalla, (40, 60, 90), (cx, cy), self._radio, 2)
        pygame.draw.circle(pantalla, (60, 160, 230), (cx + 4, cy - 3), 8)
        pygame.draw.circle(pantalla, (255, 255, 255), (cx + 7, cy - 6), 2)
