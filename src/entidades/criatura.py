"""CriaturaMarciana: enemigo que persigue al Explorador."""
from __future__ import annotations

import math

import pygame

from src.entidades.entidad_juego import EntidadJuego
from src.entidades.explorador import Explorador
from src.graficos import dibujar_criatura


class CriaturaMarciana(EntidadJuego):
    def __init__(self, x: float, y: float, objetivo: Explorador,
                 dano: int = 12, velocidad: float = 120.0) -> None:
        super().__init__(x, y, 60, "criatura", 16)
        if dano <= 0 or velocidad <= 0:
            raise ValueError("dano y velocidad deben ser positivos")
        self.__dano: int = dano
        self.__velocidad: float = velocidad
        self.__objetivo: Explorador = objetivo        # ASOCIACIÓN (CriaturaMarciana -> Explorador)
        self.__enfriamiento: float = 0.0

    def perseguir(self, e: Explorador, dt: float) -> None:
        dx, dy = e.getX() - self._position_x, e.getY() - self._position_y
        norma = math.hypot(dx, dy)
        if norma > 0:
            paso = self.__velocidad * self.getFactorVelocidad() * dt / norma
            self.setPosicion(self._position_x + dx * paso, self._position_y + dy * paso)

    def atacar(self, e: EntidadJuego) -> None:
        if self.__enfriamiento <= 0:
            e.recibirDano(self.__dano)
            self.__enfriamiento = 1.0

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__enfriamiento = max(0.0, self.__enfriamiento - dt)
        if not self.__objetivo.estaViva():
            return
        self.perseguir(self.__objetivo, dt)
        if self.colisionaCon(self.__objetivo):
            self.atacar(self.__objetivo)

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        # se pone "furiosa" un instante después de morder
        dibujar_criatura(pantalla, self._position_x, self._position_y, self._radio,
                         self._tiempo, self.__enfriamiento > 0.6)
