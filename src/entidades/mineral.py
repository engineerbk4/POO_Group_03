"""Mineral: combustible que el Explorador recolecta."""
from __future__ import annotations

import pygame

from src.entidades.entidad_juego import EntidadJuego
from src.graficos import Color, dibujar_mineral


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
        color: Color = (80, 240, 220) if self.__valorCombustible == 1 else (255, 220, 70)
        dibujar_mineral(pantalla, self._position_x, self._position_y, self._radio, self._tiempo, color)
