"""Base: refugio con escudo que construye el Explorador."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.entidades.entidad_juego import EntidadJuego
from src.graficos import dibujar_base

if TYPE_CHECKING:
    from src.entidades.explorador import Explorador


class Base(EntidadJuego):
    ZONA_REFUGIO: float = 90.0

    def __init__(self, x: float, y: float, dueno: Explorador, resistencia: int = 120) -> None:
        super().__init__(x, y, resistencia, "base", 26)
        # ASOCIACIÓN (Base -> Explorador): la base conoce a su dueño durante toda su vida
        self.__dueno: Explorador = dueno
        self.__resistencia: int = resistencia
        self.__escudoActivo: bool = True
        self.__energiaEscudo: int = 40
        self.__recarga: float = 0.0
        self.__curaAcumulada: float = 0.0

    def getResistencia(self) -> int:
        return self.__resistencia

    def isEscudoActivo(self) -> bool:
        return self.__escudoActivo

    def proteger(self) -> None:
        self.__escudoActivo = True
        self.__energiaEscudo = 40

    def destruir(self) -> None:
        super().recibirDano(self.getSalud())  # ignora el escudo

    def recibirDano(self, cantidad: int) -> None:
        if self.__escudoActivo:
            self.__energiaEscudo -= cantidad
            if self.__energiaEscudo <= 0:
                self.__escudoActivo = False
                self.__recarga = 6.0
            cantidad -= cantidad // 2  # el escudo absorbe la mitad
        super().recibirDano(cantidad)

    def update(self, dt: float) -> None:
        super().update(dt)
        if not self.__escudoActivo:
            self.__recarga -= dt
            if self.__recarga <= 0:
                self.proteger()
            return
        if self.__dueno.estaViva() and self.distanciaA(self.__dueno) <= self.ZONA_REFUGIO:
            self.__curaAcumulada += 4 * dt          # refugio: cura 4 HP/s
            puntos = int(self.__curaAcumulada)
            if puntos >= 1:
                self.__dueno.curar(puntos)
                self.__curaAcumulada -= puntos

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        dibujar_base(pantalla, self._position_x, self._position_y, self._radio, self._tiempo,
                     self.__escudoActivo, self.ZONA_REFUGIO)
