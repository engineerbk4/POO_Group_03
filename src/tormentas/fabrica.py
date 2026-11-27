"""Patrón fábrica con registro dinámico."""
from __future__ import annotations

from typing import Dict, List, Type

from src.tormentas.tormenta import Tormenta


class TormentaFactory:
    """Patrón fábrica con registro dinámico.

    El cliente (``Nivel``) pide una tormenta por nombre y recibe un ``Tormenta``
    sin conocer la clase concreta. Los tipos se registran desde fuera
    (``main.py``) con ``registrarTormenta``: agregar una tormenta nueva no
    obliga a modificar esta clase (Open/Closed).
    """

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
