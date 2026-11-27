"""Nivel 2: mantener las bases en pie hasta que acabe el tiempo."""
from __future__ import annotations

import math
from typing import Tuple

from src.niveles.nivel import Nivel
from src.tormentas.fabrica import TormentaFactory


class NivelDefensa(Nivel):
    DURACION: float = 45.0
    CICLO_TORMENTAS: Tuple[str, ...] = ("meteoritos", "radiacion", "arena", "meteoritos")

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(2, fabrica)
        self.__basesObjetivo: int = 3
        self.__basesProtegidas: int = 0
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0

    def reiniciar(self) -> None:
        self.__basesProtegidas = 0
        self.__tTormenta = 7.0
        self.__tCriatura = 0.0
        super().reiniciar()

    def _poblar(self) -> None:
        self.getExplorador().almacenar(6)       # alcanza para 2 bases de entrada
        for _ in range(5):
            self._crearMineral()
        for _ in range(2):
            self._crearMarciano()
        for _ in range(2):
            self._crearCriatura()

    def ejecutarReglas(self, dt: float) -> None:
        self.__basesProtegidas = len(self._bases)
        self.__tTormenta += dt
        self.__tCriatura += dt
        if self.__tTormenta >= 10.0:
            self.__tTormenta = 0.0
            self._lanzarSiguienteTormenta(self.CICLO_TORMENTAS)
        if self.__tCriatura >= 12.0 and len(self._criaturas) < 4:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(4)

    def verificarVictoria(self) -> bool:
        return self.getTiempo() >= self.DURACION and self.__basesProtegidas >= self.__basesObjetivo

    def descripcionObjetivo(self) -> str:
        restante = max(0, math.ceil(self.DURACION - self.getTiempo()))
        return (f"Defiende {self.__basesProtegidas}/{self.__basesObjetivo} bases "
                f"(ESPACIO = construir) · Tiempo: {restante}s")
