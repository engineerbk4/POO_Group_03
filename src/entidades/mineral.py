"""Mineral: combustible que el Explorador recolecta."""
from __future__ import annotations

import math

import pygame

from src.entidades.entidad_juego import EntidadJuego
from src.graficos import Color


class Mineral(EntidadJuego):
    def __init__(self, x: float, y: float, valorCombustible: int = 1) -> None:
        super().__init__(x, y, 1, "mineral", 10)
        if valorCombustible <= 0:
            raise ValueError("valorCombustible debe ser positivo")
        self.__valorCombustible: int = valorCombustible

    def getValorCombustible(self) -> int:
        return self.__valorCombustible

    def serRecolectado(self) -> None:
        self.recibirDano(self.getSalud())  # el mineral "muere" al recolectarse

    def esAfectablePorTormenta(self) -> bool:
        return False

    def update(self, dt: float) -> None:
        super().update(dt)

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        cx, cy = int(self._position_x), int(self._position_y)
        r = self._radio + int(2 * math.sin(self._tiempo * 4))
        color: Color = (80, 240, 220) if self.__valorCombustible == 1 else (255, 220, 70)
        puntos = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(pantalla, color, puntos)
        pygame.draw.polygon(pantalla, (255, 255, 255), puntos, 2)
