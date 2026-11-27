"""Nivel 3: reunir combustible y llegar al cohete."""
from __future__ import annotations

import math
from typing import Tuple

import pygame

from src import config
from src.graficos import circulo_alpha, dibujar_cohete
from src.niveles.nivel import Nivel
from src.tormentas.fabrica import TormentaFactory


class NivelEscape(Nivel):
    COMBUSTIBLE_NECESARIO: int = 6
    CICLO_TORMENTAS: Tuple[str, ...] = ("meteoritos", "radiacion", "arena")

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(3, fabrica)
        self.__cohete: Tuple[float, float] = (config.ANCHO - 90.0, config.ALTO - 90.0)
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0

    def reiniciar(self) -> None:
        self.__tTormenta = 3.0
        self.__tCriatura = 0.0
        super().reiniciar()

    def _poblar(self) -> None:
        for _ in range(7):
            self._crearMineral()
        for _ in range(3):
            self._crearMarciano()
        for _ in range(2):
            self._crearCriatura()

    def __cercaDelCohete(self) -> bool:
        e = self.getExplorador()
        return math.hypot(e.getX() - self.__cohete[0], e.getY() - self.__cohete[1]) < 60

    def ejecutarReglas(self, dt: float) -> None:
        self.__tTormenta += dt
        self.__tCriatura += dt
        if self.__tTormenta >= 9.0:
            self.__tTormenta = 0.0
            self._lanzarSiguienteTormenta(self.CICLO_TORMENTAS)
        if self.__tCriatura >= 16.0 and len(self._criaturas) < 4:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(5)

    def verificarVictoria(self) -> bool:
        listo = self.getExplorador().getInventarioMinerales() >= self.COMBUSTIBLE_NECESARIO
        return listo and self.__cercaDelCohete()

    def descripcionObjetivo(self) -> str:
        inv = self.getExplorador().getInventarioMinerales()
        if inv >= self.COMBUSTIBLE_NECESARIO:
            return "¡Tanque lleno! Corre al cohete (esquina inferior derecha)"
        return f"Reúne combustible para el cohete: {inv}/{self.COMBUSTIBLE_NECESARIO}"

    def _dibujarEscenario(self, pantalla: pygame.Surface) -> None:
        listo = self.getExplorador().getInventarioMinerales() >= self.COMBUSTIBLE_NECESARIO
        if listo:   # zona de abordaje: late cuando el tanque está lleno
            pulso = 0.5 + 0.5 * math.sin(self.getTiempo() * 4)
            circulo_alpha(pantalla, (120, 255, 150), self.__cohete, 60, int(30 + 40 * pulso))
            pygame.draw.circle(pantalla, (150, 255, 180), (int(self.__cohete[0]), int(self.__cohete[1])), 60, 2)
        dibujar_cohete(pantalla, self.__cohete[0], self.__cohete[1], self.getTiempo(), listo)
