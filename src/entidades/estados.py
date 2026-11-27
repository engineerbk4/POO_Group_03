"""Patrón State: estados del Marciano.

``Marciano`` es el *contexto*; ``EstadoMarciano`` la interfaz; ``MarcianoAsustado``
y ``MarcianoAliado`` los estados concretos. Cada estado decide cómo se mueve,
cómo luce y qué indicadores dibuja, sin ``if`` sobre el tipo de estado.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame

from src.graficos import Color, dibujar_aura_curacion, dibujar_indicador_tecla

if TYPE_CHECKING:
    from src.entidades.marciano import Marciano


class EstadoMarciano(ABC):
    """Interfaz del patrón State: cada estado define su propia conducta y apariencia."""

    @abstractmethod
    def ejecutarAccion(self, contexto: Marciano, dt: float) -> None:
        ...

    @abstractmethod
    def colorCuerpo(self) -> Color:
        ...

    @abstractmethod
    def aceptaOfrenda(self) -> bool:
        ...

    @abstractmethod
    def expresion(self) -> str:
        """Gesto del rostro: ``"asustado"`` o ``"feliz"``."""

    @abstractmethod
    def dibujarDetalles(self, contexto: Marciano, pantalla: pygame.Surface) -> None:
        """Indicadores propios del estado (tecla [F], aura de curación...)."""


class MarcianoAsustado(EstadoMarciano):
    DISTANCIA_PANICO: float = 220.0

    def ejecutarAccion(self, contexto: Marciano, dt: float) -> None:
        objetivo = contexto.getObjetivo()
        if contexto.distanciaA(objetivo) < self.DISTANCIA_PANICO:
            contexto.alejarseDe(objetivo, dt, 1.8)
        else:
            contexto.deambular(dt)

    def colorCuerpo(self) -> Color:
        return (130, 205, 90)

    def aceptaOfrenda(self) -> bool:
        return True

    def expresion(self) -> str:
        return "asustado"

    def dibujarDetalles(self, contexto: Marciano, pantalla: pygame.Surface) -> None:
        # indicador [F] cuando el jugador está lo bastante cerca para ofrecer un mineral
        if contexto.distanciaA(contexto.getObjetivo()) <= contexto.ALCANCE_OFRENDA:
            dibujar_indicador_tecla(pantalla, contexto.getX(),
                                    contexto.getY() - contexto.getRadio() - 34,
                                    "[F]", contexto.getTiempo())


class MarcianoAliado(EstadoMarciano):
    DISTANCIA_SEGUIMIENTO: float = 70.0

    def ejecutarAccion(self, contexto: Marciano, dt: float) -> None:
        objetivo = contexto.getObjetivo()
        if contexto.distanciaA(objetivo) > self.DISTANCIA_SEGUIMIENTO:
            contexto.acercarseA(objetivo, dt, 1.6)
        else:
            contexto.apoyar(objetivo, dt)

    def colorCuerpo(self) -> Color:
        return (90, 190, 235)

    def aceptaOfrenda(self) -> bool:
        return False

    def expresion(self) -> str:
        return "feliz"

    def dibujarDetalles(self, contexto: Marciano, pantalla: pygame.Surface) -> None:
        curando = contexto.distanciaA(contexto.getObjetivo()) <= self.DISTANCIA_SEGUIMIENTO
        dibujar_aura_curacion(pantalla, contexto.getX(), contexto.getY(), contexto.getRadio(),
                              contexto.getTiempo(), curando)
