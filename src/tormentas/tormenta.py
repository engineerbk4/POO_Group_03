"""Clase base abstracta de las tormentas (producto del Factory Method)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

import pygame

from src.entidades.entidad_juego import EntidadJuego


class Tormenta(ABC):
    """Producto abstracto de ``TormentaFactory``.

    ``dano`` puede ser 0 para tormentas que no lastiman y solo alteran el
    entorno (por ejemplo ``TormentaArena``, que ralentiza).
    """

    def __init__(self, duracion: float, dano: int) -> None:
        if duracion <= 0 or dano < 0:
            raise ValueError("duracion debe ser positiva y dano no negativo")
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
