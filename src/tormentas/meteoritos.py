"""Tormenta de meteoritos: lluvia de impactos con aviso previo."""
from __future__ import annotations

import math
import random
from typing import List, Tuple

import pygame

from src import config
from src.entidades.entidad_juego import EntidadJuego
from src.graficos import circulo_alpha
from src.tormentas.tormenta import Tormenta


class TormentaMeteoritos(Tormenta):
    """Lluvia de meteoritos: un aro rojo avisa dónde caerán."""

    def __init__(self) -> None:
        super().__init__(duracion=10.0, dano=35)
        self.__velocidadCaida: float = 1.3     # segundos desde el aviso hasta el impacto
        self.__radioImpacto: float = 42.0
        self.__intervalo: float = 0.5
        self.__temporizador: float = 0.0
        self.__pendientes: List[List[float]] = []                 # [x, y, tiempoRestante]
        self.__impactosListos: List[Tuple[float, float]] = []
        self.__explosiones: List[List[float]] = []                # [x, y, ttl]

    def haTerminado(self) -> bool:
        return super().haTerminado() and not self.__pendientes and not self.__explosiones

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._restante > 0:
            self.__temporizador -= dt
            if self.__temporizador <= 0:
                self.__temporizador = self.__intervalo
                self.__pendientes.append([random.uniform(40, config.ANCHO - 40),
                                          random.uniform(config.HUD_ALTO + 40, config.ALTO - 40),
                                          self.__velocidadCaida])
        for m in self.__pendientes:
            m[2] -= dt
        for m in [m for m in self.__pendientes if m[2] <= 0]:
            self.__impactosListos.append((m[0], m[1]))
            self.__explosiones.append([m[0], m[1], 0.4])
        self.__pendientes = [m for m in self.__pendientes if m[2] > 0]
        for ex in self.__explosiones:
            ex[2] -= dt
        self.__explosiones = [ex for ex in self.__explosiones if ex[2] > 0]

    def aplicarEfecto(self, entidades: List[EntidadJuego]) -> None:
        for (ix, iy) in self.__impactosListos:
            for e in entidades:
                cerca = math.hypot(e.getX() - ix, e.getY() - iy) <= self.__radioImpacto + e.getRadio()
                if cerca and e.esAfectablePorTormenta():
                    self.impactar(e)
        self.__impactosListos.clear()

    def impactar(self, e: EntidadJuego) -> None:
        e.recibirDano(self._dano)

    def render(self, pantalla: pygame.Surface) -> None:
        for x, y, t in self.__pendientes:
            frac = max(0.0, t / self.__velocidadCaida)
            circulo_alpha(pantalla, (255, 60, 40), (x, y), self.__radioImpacto, int(70 * (1 - frac)))
            pygame.draw.circle(pantalla, (255, 90, 60), (int(x), int(y)),
                               int(self.__radioImpacto), 2)
            fy = int(y - frac * 320)
            pygame.draw.circle(pantalla, (255, 140, 30), (int(x), fy), 9)
            pygame.draw.circle(pantalla, (255, 235, 120), (int(x), fy), 4)
        for x, y, ttl in self.__explosiones:
            circulo_alpha(pantalla, (255, 170, 40), (x, y), self.__radioImpacto, int(200 * ttl / 0.4))
