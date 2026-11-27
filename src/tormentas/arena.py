"""Tormenta de arena: reduce la visibilidad y la velocidad de todos, sin hacer daño.

Es el tercer tipo de tormenta y demuestra Open/Closed: se registra desde
``main.py`` con ``fabrica.registrarTormenta("arena", TormentaArena)`` sin
modificar ``TormentaFactory`` ni ``Nivel``.
"""
from __future__ import annotations

import math
import random
from typing import List

import pygame

from src import config
from src.entidades.entidad_juego import EntidadJuego
from src.tormentas.tormenta import Tormenta


class TormentaArena(Tormenta):
    FACTOR_VELOCIDAD: float = 0.55

    def __init__(self) -> None:
        super().__init__(duracion=7.0, dano=0)
        self.__tiempo: float = 0.0
        # rachas de arena: [x, y, largo, velocidad]
        self.__rachas: List[List[float]] = [
            [random.uniform(0, config.ANCHO), random.uniform(config.HUD_ALTO, config.ALTO),
             random.uniform(30, 110), random.uniform(380, 700)] for _ in range(70)]

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__tiempo += dt
        for r in self.__rachas:
            r[0] += r[3] * dt
            if r[0] - r[2] > config.ANCHO:
                r[0] = -r[2]
                r[1] = random.uniform(config.HUD_ALTO, config.ALTO)

    def aplicarEfecto(self, entidades: List[EntidadJuego]) -> None:
        if self.haTerminado():
            return
        for e in entidades:
            if e.esAfectablePorTormenta():
                e.ralentizar(self.FACTOR_VELOCIDAD, 0.25)

    def __intensidad(self) -> float:
        """Sube al empezar y baja al terminar (la tormenta entra y sale suavemente)."""
        entrada = min(1.0, self.__tiempo / 1.0)
        salida = min(1.0, max(0.0, self._restante) / 1.0)
        return min(entrada, salida)

    def render(self, pantalla: pygame.Surface) -> None:
        k = self.__intensidad()
        velo = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        pulso = 0.5 + 0.5 * math.sin(self.__tiempo * 2.2)
        velo.fill((190, 112, 89, int((70 + 20 * pulso) * k)))
        for x, y, largo, _v in self.__rachas:
            pygame.draw.line(velo, (250, 192, 146, int(145 * k)), (x - largo, y), (x, y), 2)
        pantalla.blit(velo, (0, 0))
