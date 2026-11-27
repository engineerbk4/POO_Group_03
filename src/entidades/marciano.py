"""Marciano: contexto del patrón State."""
from __future__ import annotations

import math
import random
from typing import List

import pygame
from src import config

from src.entidades.entidad_juego import EntidadJuego
from src.entidades.estados import EstadoMarciano, MarcianoAliado
from src.graficos import Color, dibujar_marciano


class Marciano(EntidadJuego):
    """Contexto del patrón State: delega su comportamiento en ``estadoActual``."""

    ALCANCE_OFRENDA: float = 110.0   # distancia máxima del explorador para ofrecer un mineral (tecla F)

    def __init__(self, x: float, y: float, objetivo: EntidadJuego,
                 estadoInicial: EstadoMarciano) -> None:
        super().__init__(x, y, 40, "marciano", 14)
        self.__velocidad: float = 90.0
        self.__objetivo: EntidadJuego = objetivo                # ASOCIACIÓN: conoce a quién seguir/evitar
        self.__estadoActual: EstadoMarciano = estadoInicial     # AGREGACIÓN: estado inyectado
        self.__rumbo: float = random.uniform(0, 2 * math.pi)
        self.__cambioRumbo: float = 0.0
        self.__curaAcumulada: float = 0.0
        # partículas efímeras [x, y, vx, vy, ttl, color]
        self.__particulas: List[list] = []

    def getObjetivo(self) -> EntidadJuego:
        return self.__objetivo

    def getTiempo(self) -> float:
        return self._tiempo

    def cambiarEstado(self, nuevoEstado: EstadoMarciano) -> None:
        self.__estadoActual = nuevoEstado

    def aceptaOfrenda(self) -> bool:
        return self.__estadoActual.aceptaOfrenda()

    def ofrecerMineral(self) -> None:
        self.cambiarEstado(MarcianoAliado())
        self.emitirParticulas(20, (255, 130, 180))
        self.emitirParticulas(10, (255, 235, 130))

    def emitirParticulas(self, cantidad: int, color: Color) -> None:
        for _ in range(cantidad):
            ang = random.uniform(0, 2 * math.pi)
            vel = random.uniform(40, 120)
            self.__particulas.append([self._position_x, self._position_y - 6,
                                      math.cos(ang) * vel, math.sin(ang) * vel - 40,
                                      random.uniform(0.5, 1.0), color])

    # ---- primitivas de movimiento que usan los estados ----
    def __moverPorVector(self, dx: float, dy: float, dt: float, factor: float) -> None:
        norma = math.hypot(dx, dy)
        if norma == 0:
            return
        paso = self.__velocidad * self.getFactorVelocidad() * factor * dt / norma
        self.setPosicion(self._position_x + dx * paso, self._position_y + dy * paso)

    def acercarseA(self, otro: EntidadJuego, dt: float, factor: float = 1.0) -> None:
        self.__moverPorVector(otro.getX() - self._position_x,
                              otro.getY() - self._position_y, dt, factor)

    def alejarseDe(self, otro: EntidadJuego, dt: float, factor: float = 1.0) -> None:
        dx, dy = self._position_x - otro.getX(), self._position_y - otro.getY()
        if (self._position_x <= 33 and dx < 0) or (self._position_x >= config.ANCHO - 33 and dx > 0):
            dx = 0
        if (self._position_y <= config.HUD_ALTO + 55 and dy < 0) or (self._position_y >= config.ALTO - 33 and dy > 0):
            dy = 0
        if dx == dy == 0:
            dx, dy = config.ANCHO / 2 - self._position_x, (config.ALTO + config.HUD_ALTO) / 2 - self._position_y
        self.__moverPorVector(dx, dy, dt, factor)

    def deambular(self, dt: float) -> None:
        self.__cambioRumbo -= dt
        if self.__cambioRumbo <= 0:
            self.__rumbo = random.uniform(0, 2 * math.pi)
            self.__cambioRumbo = random.uniform(1.0, 3.0)
        self.__moverPorVector(math.cos(self.__rumbo), math.sin(self.__rumbo), dt, 0.5)

    def apoyar(self, otro: EntidadJuego, dt: float) -> None:
        """El aliado cura 3 HP/s al explorador cuando está a su lado."""
        self.__curaAcumulada += 3 * dt
        puntos = int(self.__curaAcumulada)
        if puntos >= 1:
            otro.curar(puntos)
            self.__curaAcumulada -= puntos

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__estadoActual.ejecutarAccion(self, dt)   # delegación al estado
        for p in self.__particulas:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 140 * dt                           # gravedad suave
            p[4] -= dt
        self.__particulas = [p for p in self.__particulas if p[4] > 0]

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        dibujar_marciano(pantalla, self._position_x, self._position_y, self._radio, self._tiempo,
                         self.__estadoActual.colorCuerpo(), self.__estadoActual.expresion())
        self.__estadoActual.dibujarDetalles(self, pantalla)    # [F] o aura, según el estado
        for x, y, _vx, _vy, ttl, color in self.__particulas:
            pygame.draw.circle(pantalla, color, (int(x), int(y)), max(1, int(3 * min(1.0, ttl * 2))))
