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
        self.__tTormenta = 5.0
        self.__tCriatura = 0.0
        super().reiniciar()

    def _poblar(self) -> None:
        for _ in range(6):
            self._crearMineral()
        for _ in range(3):
            self._crearMarciano()
        for _ in range(2):
            self._crearCriatura()

    def _alRecolectar(self, valor: int) -> None:
        self.__mineralesRecolectados += valor

    def ejecutarReglas(self, dt: float) -> None:
        self.__tTormenta += dt
        self.__tCriatura += dt
        if self.__tTormenta >= 9.0:
            self.__tTormenta = 0.0
            self._lanzarSiguienteTormenta(self.CICLO_TORMENTAS)
        if self.__tCriatura >= 14.0 and len(self._criaturas) < 4:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(6)
        if self.getAliadosFormados() < 2 and not any(m.estaViva() and m.aceptaOfrenda() for m in self._marcianos):
            self._crearMarciano()

    def verificarVictoria(self) -> bool:
        return (self.getExplorador().getInventarioMinerales() >= self.__mineralesObjetivo
                and self.getAliadosFormados() >= 2)

    def descripcionObjetivo(self) -> str:
        return " | ".join(texto for texto, _ in self.objetivosHUD())

    def objetivosHUD(self):
        nox = self.getExplorador().getInventarioMinerales()
        aliados = self.getAliadosFormados()
        return [(f"Nox en inventario: {nox}/10", nox >= 10),
                (f"Forma aliados: {aliados}/2", aliados >= 2)]
