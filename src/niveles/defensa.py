"""Nivel 2: construir bases y formar un aliado antes del límite."""
from __future__ import annotations

import math
from typing import Tuple

from src.niveles.nivel import Nivel
from src.tormentas.fabrica import TormentaFactory


class NivelDefensa(Nivel):
    DURACION: float = 40.0
    CICLO_TORMENTAS: Tuple[str, ...] = ("meteoritos", "radiacion", "arena", "meteoritos")

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(2, fabrica)
        self.__basesObjetivo: int = 3
        self.__basesProtegidas: int = 0
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0

    def reiniciar(self) -> None:
        self.__basesProtegidas = 0
        self.__tTormenta = 5.0
        self.__tCriatura = 0.0
        super().reiniciar()

    def _poblar(self) -> None:
        self.getExplorador().almacenar(6)       # alcanza para 2 bases de entrada
        for _ in range(4):
            self._crearMineral()
        for _ in range(2):
            self._crearMarciano()
        for _ in range(2):
            self._crearCriatura()

    def ejecutarReglas(self, dt: float) -> None:
        self.__basesProtegidas = len(self._bases)
        self.__tTormenta += dt
        self.__tCriatura += dt
        if self.__tTormenta >= 8.0:
            self.__tTormenta = 0.0
            self._lanzarSiguienteTormenta(self.CICLO_TORMENTAS)
        if self.__tCriatura >= 10.0 and len(self._criaturas) < 5:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(4)
        if self.getAliadosFormados() < 1 and not any(m.estaViva() and m.aceptaOfrenda() for m in self._marcianos):
            self._crearMarciano()

    def verificarVictoria(self) -> bool:
        return (self.getTiempo() <= self.DURACION and sum(b.estaViva() for b in self._bases) >= self.__basesObjetivo
                and self.getAliadosFormados() >= 1)

    def tiempoAgotado(self) -> bool:
        return self.getTiempo() >= self.DURACION and not self.isCompletado()

    def bonificacionTiempo(self) -> int:
        return 10 * max(0, int(self.DURACION - self.getTiempo()))

    def update(self, dt: float) -> None:
        super().update(min(dt, max(0.0, self.DURACION - self.getTiempo())))

    def descripcionObjetivo(self) -> str:
        return " | ".join(texto for texto, _ in self.objetivosHUD())

    def objetivosHUD(self):
        restante = max(0, math.ceil(self.DURACION - self.getTiempo()))
        bases = sum(b.estaViva() for b in self._bases)
        aliados = self.getAliadosFormados()
        return [(f"Bases activas: {bases}/3", bases >= 3),
                (f"Forma aliados: {aliados}/1", aliados >= 1),
                (f"Tiempo restante: {restante}s", False)]
