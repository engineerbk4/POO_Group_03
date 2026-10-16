"""Tormentas del juego + TormentaFactory (patrón Factory Method con registro dinámico)."""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Type

import pygame

import config
from entidades import EntidadJuego
from graficos import circulo_alpha


class Tormenta(ABC):
    def __init__(self, duracion: float, dano: int) -> None:
        if duracion <= 0 or dano <= 0:
            raise ValueError("duracion y dano deben ser positivos")
        self._duracion: float = duracion
        self._dano: int = dano
        self._restante: float = duracion

    def haTerminado(self) -> bool:
        return self._restante <= 0

    @abstractmethod
    def update(self, dt: float) -> None:
        self._restante -= dt

    @abstractmethod
    def aplicarEfecto(self, entidades: List[EntidadJuego]) -> None:
        ...

    @abstractmethod
    def render(self, pantalla: pygame.Surface) -> None:
        ...


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


class TormentaFactory:
    """Factory Method con registro dinámico: se registran tipos sin tocar esta clase (Open/Closed)."""

    def __init__(self) -> None:
        self.__registroTormentas: Dict[str, Type[Tormenta]] = {}

    def registrarTormenta(self, tipo: str, claseTormenta: Type[Tormenta]) -> None:
        if not tipo:
            raise ValueError("el tipo no puede estar vacío")
        self.__registroTormentas[tipo] = claseTormenta

    def crearTormenta(self, tipo: str) -> Tormenta:
        if tipo not in self.__registroTormentas:
            raise KeyError(f"Tipo de tormenta no registrado: {tipo}")
        return self.__registroTormentas[tipo]()

    def tiposDisponibles(self) -> List[str]:
        return list(self.__registroTormentas)
