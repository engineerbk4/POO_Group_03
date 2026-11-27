"""Tormenta de radiación: zona que drena vida por segundo."""
from __future__ import annotations

import math
import random
from typing import Dict, List

import pygame

from src import config
from src.entidades.entidad_juego import EntidadJuego
from src.graficos import circulo_alpha
from src.tormentas.tormenta import Tormenta


class TormentaRadiacion(Tormenta):
    """Zona verde que se desplaza y drena vida por segundo (_dano = daño/segundo)."""

    def __init__(self) -> None:
        super().__init__(duracion=9.0, dano=10)
        self.__radioEfecto: float = 100.0
        self.__x: float = random.uniform(150, config.ANCHO - 150)
        self.__y: float = random.uniform(config.HUD_ALTO + 150, config.ALTO - 100)
        ang = random.uniform(0, 2 * math.pi)
        self.__vx: float = math.cos(ang) * 35
        self.__vy: float = math.sin(ang) * 35
        self.__ultimoDt: float = 0.0
        self.__acumulado: Dict[int, float] = {}

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__ultimoDt = dt
        self.__x += self.__vx * dt
        self.__y += self.__vy * dt
        if not 100 < self.__x < config.ANCHO - 100:
            self.__vx = -self.__vx
        if not config.HUD_ALTO + 100 < self.__y < config.ALTO - 100:
            self.__vy = -self.__vy

    def aplicarEfecto(self, entidades: List[EntidadJuego]) -> None:
        if self.haTerminado():
            return
        for e in entidades:
            dentro = math.hypot(e.getX() - self.__x, e.getY() - self.__y) <= self.__radioEfecto
            if dentro and e.esAfectablePorTormenta():
                self.drenarVida(e)

    def drenarVida(self, e: EntidadJuego) -> None:
        acumulado = self.__acumulado.get(e.getId(), 0.0) + self._dano * self.__ultimoDt
        puntos = int(acumulado)
        if puntos >= 1:
            e.recibirDano(puntos)
            acumulado -= puntos
        self.__acumulado[e.getId()] = acumulado

    def render(self, pantalla: pygame.Surface) -> None:
        pulso = 0.5 + 0.5 * math.sin(self._restante * 5)
        circulo_alpha(pantalla, (90, 255, 90), (self.__x, self.__y),
                      self.__radioEfecto, int(45 + 30 * pulso))
        pygame.draw.circle(pantalla, (150, 255, 120), (int(self.__x), int(self.__y)),
                           int(self.__radioEfecto), 2)
