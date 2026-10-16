"""Clase base abstracta de todas las entidades del juego."""
from __future__ import annotations

import math
from abc import ABC, abstractmethod

import pygame

from src import config


class EntidadJuego(ABC):
    """Toda entidad interactiva hereda de aquí. El Game Loop solo conoce esta clase."""

    __contador: int = 0  # generador de ids (name mangling a nivel de clase)

    def __init__(self, x: float, y: float, salud: int, sprite: str, radio: int) -> None:
        if salud <= 0 or radio <= 0:
            raise ValueError("salud y radio deben ser positivos")
        if not sprite:
            raise ValueError("toda entidad necesita un sprite")
        EntidadJuego.__contador += 1
        self._id: int = EntidadJuego.__contador
        self._position_x: float = float(x)
        self._position_y: float = float(y)
        self._sprite: str = sprite
        self._radio: int = radio
        self._tiempo: float = 0.0
        # Atributos críticos: privados (encapsulamiento estricto)
        self.__salud: int = salud
        self.__saludMaxima: int = salud

    # ---- getters (solo lectura) ----
    def getId(self) -> int:
        return self._id

    def getX(self) -> float:
        return self._position_x

    def getY(self) -> float:
        return self._position_y

    def getRadio(self) -> int:
        return self._radio

    def getSalud(self) -> int:
        return self.__salud

    def getSaludMaxima(self) -> int:
        return self.__saludMaxima

    def estaViva(self) -> bool:
        return self.__salud > 0

    # ---- comportamiento que muta el estado (no hay setSalud) ----
    def setPosicion(self, x: float, y: float) -> None:
        self._position_x = min(max(x, self._radio), config.ANCHO - self._radio)
        self._position_y = min(max(y, config.HUD_ALTO + self._radio), config.ALTO - self._radio)

    def recibirDano(self, cantidad: int) -> None:
        if cantidad < 0:
            raise ValueError("el daño no puede ser negativo")
        if not self.estaViva():
            return
        self.__salud = max(0, self.__salud - cantidad)
        if self.__salud == 0:
            self._alMorir()

    def curar(self, cantidad: int) -> None:
        if cantidad < 0:
            raise ValueError("la cura no puede ser negativa")
        if self.estaViva():
            self.__salud = min(self.__saludMaxima, self.__salud + cantidad)

    def _alMorir(self) -> None:
        """Hook: las subclases pueden reaccionar a su muerte."""

    def esAfectablePorTormenta(self) -> bool:
        """Hook polimórfico: evita preguntar el tipo de la entidad."""
        return True

    # ---- geometría ----
    def distanciaA(self, otro: EntidadJuego) -> float:
        return math.hypot(otro.getX() - self._position_x, otro.getY() - self._position_y)

    def colisionaCon(self, otro: EntidadJuego) -> bool:
        return self.distanciaA(otro) <= self._radio + otro.getRadio()

    # ---- contrato abstracto del Game Loop ----
    @abstractmethod
    def update(self, dt: float) -> None:
        """Las subclases lo sobrescriben y llaman a super().update(dt)."""
        self._tiempo += dt

    def render(self, pantalla: pygame.Surface) -> None:
        self._dibujarCuerpo(pantalla)
        self._dibujarBarraSalud(pantalla)

    @abstractmethod
    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        ...

    def _dibujarBarraSalud(self, pantalla: pygame.Surface) -> None:
        if self.__salud >= self.__saludMaxima:
            return
        ancho = self._radio * 2
        x = int(self._position_x) - self._radio
        y = int(self._position_y) - self._radio - 10
        pygame.draw.rect(pantalla, (70, 0, 0), (x, y, ancho, 5))
        pygame.draw.rect(pantalla, (0, 220, 90),
                         (x, y, int(ancho * self.__salud / self.__saludMaxima), 5))

    def __del__(self) -> None:
        try:
            if config.DEBUG_DESTRUCTORES:
                print(f"[__del__] {type(self).__name__} #{self._id} destruida")
        except Exception:
            pass  # el intérprete puede estar cerrándose
