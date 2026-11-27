"""Nivel 1: recolectar combustible y sobrevivir."""
from __future__ import annotations

from typing import Tuple

from src.niveles.nivel import Nivel
from src.tormentas.fabrica import TormentaFactory


class NivelSupervivencia(Nivel):
    CICLO_TORMENTAS: Tuple[str, ...] = ("radiacion", "meteoritos")

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(1, fabrica)
        self.__mineralesObjetivo: int = 10
        self.__mineralesRecolectados: int = 0
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0

    def reiniciar(self) -> None:
        self.__mineralesRecolectados = 0
        self.__tTormenta = 6.0
        self.__tCriatura = 0.0
        super().reiniciar()

    def _poblar(self) -> None:
        for _ in range(7):
            self._crearMineral()
        for _ in range(3):
            self._crearMarciano()
        self._crearCriatura()

    def _alRecolectar(self, valor: int) -> None:
        self.__mineralesRecolectados += valor

    def ejecutarReglas(self, dt: float) -> None:
        self.__tTormenta += dt
        self.__tCriatura += dt
        if self.__tTormenta >= 12.0:
            self.__tTormenta = 0.0
            self._lanzarSiguienteTormenta(self.CICLO_TORMENTAS)
        if self.__tCriatura >= 18.0 and len(self._criaturas) < 3:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(6)

    def verificarVictoria(self) -> bool:
        return self.__mineralesRecolectados >= self.__mineralesObjetivo

    def descripcionObjetivo(self) -> str:
        return f"Recolecta combustible: {self.__mineralesRecolectados}/{self.__mineralesObjetivo}"
