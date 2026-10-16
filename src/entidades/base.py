"""Base: refugio con escudo que construye el Explorador."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from src.entidades.entidad_juego import EntidadJuego
from src.graficos import circulo_alpha

if TYPE_CHECKING:
    from src.entidades.explorador import Explorador


class Base(EntidadJuego):
    ZONA_REFUGIO: float = 90.0

    def __init__(self, x: float, y: float, dueno: Explorador, resistencia: int = 120) -> None:
        super().__init__(x, y, resistencia, "base", 26)
        self.__dueno: Explorador = dueno          # ASOCIACIÓN: la base conoce a su dueño
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
        cx, cy = int(self._position_x), int(self._position_y)
        circulo_alpha(pantalla, (120, 200, 255), (cx, cy), self.ZONA_REFUGIO, 25)
        pygame.draw.circle(pantalla, (150, 155, 165), (cx, cy), self._radio)
        pygame.draw.circle(pantalla, (95, 100, 110), (cx, cy), self._radio, 3)
        pygame.draw.circle(pantalla, (210, 215, 225), (cx - 5, cy - 6), 9)
        if self.__escudoActivo:
            circulo_alpha(pantalla, (80, 170, 255), (cx, cy), self._radio + 8, 70)
            pygame.draw.circle(pantalla, (140, 210, 255), (cx, cy), self._radio + 8, 2)
