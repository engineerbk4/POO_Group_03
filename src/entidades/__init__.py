"""Entidades del juego: jerarquía de EntidadJuego + patrón State del Marciano."""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import pygame

from src import config
from src.graficos import Color, circulo_alpha


# ======================================================================
#  CLASE BASE ABSTRACTA
# ======================================================================
class EntidadJuego(ABC):
    """Toda entidad interactiva hereda de aquí. El Game Loop solo conoce esta clase."""

    __contador: int = 0  # generador de ids (name mangling a nivel de clase)

    def __init__(self, x: float, y: float, salud: int, sprite: str, radio: int) -> None:
        if salud <= 0 or radio <= 0:
            raise ValueError("salud y radio deben ser positivos")
        if not sprite:
            raise ValueError("toda entidad necesita un sprite")
        EntidadJuego.__contador += 1
        self._id: int = EntidadJuego.__contador
        self._position_x: float = float(x)
        self._position_y: float = float(y)
        self._sprite: str = sprite
        self._radio: int = radio
        self._tiempo: float = 0.0
        # Atributos críticos: privados (encapsulamiento estricto)
        self.__salud: int = salud
        self.__saludMaxima: int = salud

    # ---- getters (solo lectura) ----
    def getId(self) -> int:
        return self._id

    def getX(self) -> float:
        return self._position_x

    def getY(self) -> float:
        return self._position_y

    def getRadio(self) -> int:
        return self._radio

    def getSalud(self) -> int:
        return self.__salud

    def getSaludMaxima(self) -> int:
        return self.__saludMaxima

    def estaViva(self) -> bool:
        return self.__salud > 0

    # ---- comportamiento que muta el estado (no hay setSalud) ----
    def setPosicion(self, x: float, y: float) -> None:
        self._position_x = min(max(x, self._radio), config.ANCHO - self._radio)
        self._position_y = min(max(y, config.HUD_ALTO + self._radio), config.ALTO - self._radio)

    def recibirDano(self, cantidad: int) -> None:
        if cantidad < 0:
            raise ValueError("el daño no puede ser negativo")
        if not self.estaViva():
            return
        self.__salud = max(0, self.__salud - cantidad)
        if self.__salud == 0:
            self._alMorir()

    def curar(self, cantidad: int) -> None:
        if cantidad < 0:
            raise ValueError("la cura no puede ser negativa")
        if self.estaViva():
            self.__salud = min(self.__saludMaxima, self.__salud + cantidad)

    def _alMorir(self) -> None:
        """Hook: las subclases pueden reaccionar a su muerte."""

    def esAfectablePorTormenta(self) -> bool:
        """Hook polimórfico: evita preguntar el tipo de la entidad."""
        return True

    # ---- geometría ----
    def distanciaA(self, otro: EntidadJuego) -> float:
        return math.hypot(otro.getX() - self._position_x, otro.getY() - self._position_y)

    def colisionaCon(self, otro: EntidadJuego) -> bool:
        return self.distanciaA(otro) <= self._radio + otro.getRadio()

    # ---- contrato abstracto del Game Loop ----
    @abstractmethod
    def update(self, dt: float) -> None:
        """Las subclases lo sobrescriben y llaman a super().update(dt)."""
        self._tiempo += dt

    def render(self, pantalla: pygame.Surface) -> None:
        self._dibujarCuerpo(pantalla)
        self._dibujarBarraSalud(pantalla)

    @abstractmethod
    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        ...

    def _dibujarBarraSalud(self, pantalla: pygame.Surface) -> None:
        if self.__salud >= self.__saludMaxima:
            return
        ancho = self._radio * 2
        x = int(self._position_x) - self._radio
        y = int(self._position_y) - self._radio - 10
        pygame.draw.rect(pantalla, (70, 0, 0), (x, y, ancho, 5))
        pygame.draw.rect(pantalla, (0, 220, 90),
                         (x, y, int(ancho * self.__salud / self.__saludMaxima), 5))

    def __del__(self) -> None:
        try:
            if config.DEBUG_DESTRUCTORES:
                print(f"[__del__] {type(self).__name__} #{self._id} destruida")
        except Exception:
            pass  # el intérprete puede estar cerrándose


# ======================================================================
#  MINERAL
# ======================================================================
class Mineral(EntidadJuego):
    def __init__(self, x: float, y: float, valorCombustible: int = 1) -> None:
        super().__init__(x, y, 1, "mineral", 10)
        if valorCombustible <= 0:
            raise ValueError("valorCombustible debe ser positivo")
        self.__valorCombustible: int = valorCombustible

    def getValorCombustible(self) -> int:
        return self.__valorCombustible

    def serRecolectado(self) -> None:
        self.recibirDano(self.getSalud())  # el mineral "muere" al recolectarse

    def esAfectablePorTormenta(self) -> bool:
        return False

    def update(self, dt: float) -> None:
        super().update(dt)

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        cx, cy = int(self._position_x), int(self._position_y)
        r = self._radio + int(2 * math.sin(self._tiempo * 4))
        color: Color = (80, 240, 220) if self.__valorCombustible == 1 else (255, 220, 70)
        puntos = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        pygame.draw.polygon(pantalla, color, puntos)
        pygame.draw.polygon(pantalla, (255, 255, 255), puntos, 2)


# ======================================================================
#  EXPLORADOR
# ======================================================================
class Explorador(EntidadJuego):
    COSTO_BASE: int = 3

    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, 100, "explorador", 16)
        self.__inventarioMinerales: int = 0
        self.__velocidad: float = 230.0
        self.__direccion: Tuple[float, float] = (0.0, 0.0)

    def getInventarioMinerales(self) -> int:
        return self.__inventarioMinerales

    def establecerDireccion(self, dx: float, dy: float) -> None:
        norma = math.hypot(dx, dy)
        self.__direccion = (dx / norma, dy / norma) if norma > 0 else (0.0, 0.0)

    def almacenar(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("cantidad debe ser positiva")
        self.__inventarioMinerales += cantidad

    def gastarMinerales(self, cantidad: int) -> bool:
        if cantidad <= 0 or cantidad > self.__inventarioMinerales:
            return False
        self.__inventarioMinerales -= cantidad
        return True

    def recolectar(self, m: Mineral) -> None:
        """AGREGACIÓN/USO: el mineral existe en el ecosistema, el explorador solo lo toma."""
        valor = m.getValorCombustible()
        m.serRecolectado()
        self.almacenar(valor)

    def construirBase(self) -> Optional[Base]:
        """DEPENDENCIA <<create>>: crea una Base si alcanzan los minerales."""
        if not self.gastarMinerales(self.COSTO_BASE):
            return None
        return Base(self._position_x, self._position_y, self)

    def update(self, dt: float) -> None:
        super().update(dt)
        dx, dy = self.__direccion
        self.setPosicion(self._position_x + dx * self.__velocidad * dt,
                         self._position_y + dy * self.__velocidad * dt)

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        cx, cy = int(self._position_x), int(self._position_y)
        pygame.draw.circle(pantalla, (235, 235, 245), (cx, cy), self._radio)
        pygame.draw.circle(pantalla, (40, 60, 90), (cx, cy), self._radio, 2)
        pygame.draw.circle(pantalla, (60, 160, 230), (cx + 4, cy - 3), 8)
        pygame.draw.circle(pantalla, (255, 255, 255), (cx + 7, cy - 6), 2)


# ======================================================================
#  BASE
# ======================================================================
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


# ======================================================================
#  PATRÓN STATE (Marciano)
# ======================================================================
class EstadoMarciano(ABC):
    """Interfaz del patrón State: cada estado define su propia acción."""

    @abstractmethod
    def ejecutarAccion(self, contexto: Marciano, dt: float) -> None:
        ...

    @abstractmethod
    def colorCuerpo(self) -> Color:
        ...

    @abstractmethod
    def aceptaOfrenda(self) -> bool:
        ...


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


class Marciano(EntidadJuego):
    """Contexto del patrón State: delega su comportamiento en estadoActual."""

    def __init__(self, x: float, y: float, objetivo: EntidadJuego,
                 estadoInicial: EstadoMarciano) -> None:
        super().__init__(x, y, 40, "marciano", 14)
        self.__velocidad: float = 90.0
        self.__objetivo: EntidadJuego = objetivo
        self.__estadoActual: EstadoMarciano = estadoInicial   # AGREGACIÓN: estado inyectado
        self.__rumbo: float = random.uniform(0, 2 * math.pi)
        self.__cambioRumbo: float = 0.0
        self.__curaAcumulada: float = 0.0

    def getObjetivo(self) -> EntidadJuego:
        return self.__objetivo

    def cambiarEstado(self, nuevoEstado: EstadoMarciano) -> None:
        self.__estadoActual = nuevoEstado

    def aceptaOfrenda(self) -> bool:
        return self.__estadoActual.aceptaOfrenda()

    def ofrecerMineral(self) -> None:
        self.cambiarEstado(MarcianoAliado())

    # ---- primitivas de movimiento que usan los estados ----
    def __moverPorVector(self, dx: float, dy: float, dt: float, factor: float) -> None:
        norma = math.hypot(dx, dy)
        if norma == 0:
            return
        paso = self.__velocidad * factor * dt / norma
        self.setPosicion(self._position_x + dx * paso, self._position_y + dy * paso)

    def acercarseA(self, otro: EntidadJuego, dt: float, factor: float = 1.0) -> None:
        self.__moverPorVector(otro.getX() - self._position_x,
                              otro.getY() - self._position_y, dt, factor)

    def alejarseDe(self, otro: EntidadJuego, dt: float, factor: float = 1.0) -> None:
        self.__moverPorVector(self._position_x - otro.getX(),
                              self._position_y - otro.getY(), dt, factor)

    def deambular(self, dt: float) -> None:
        self.__cambioRumbo -= dt
        if self.__cambioRumbo <= 0:
            self.__rumbo = random.uniform(0, 2 * math.pi)
            self.__cambioRumbo = random.uniform(1.0, 3.0)
        self.__moverPorVector(math.cos(self.__rumbo), math.sin(self.__rumbo), dt, 0.5)

    def apoyar(self, otro: EntidadJuego, dt: float) -> None:
        """El aliado cura 3 HP/s al explorador cuando está a su lado."""
        self.__curaAcumulada += 3 * dt
        puntos = int(self.__curaAcumulada)
        if puntos >= 1:
            otro.curar(puntos)
            self.__curaAcumulada -= puntos

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__estadoActual.ejecutarAccion(self, dt)   # delegación al estado

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        cx, cy = int(self._position_x), int(self._position_y)
        color = self.__estadoActual.colorCuerpo()
        pygame.draw.line(pantalla, color, (cx, cy - 10), (cx, cy - 20), 2)
        pygame.draw.circle(pantalla, (255, 240, 120), (cx, cy - 21), 3)
        pygame.draw.circle(pantalla, color, (cx, cy), self._radio)
        for ox in (-5, 5):
            pygame.draw.circle(pantalla, (255, 255, 255), (cx + ox, cy - 3), 4)
            pygame.draw.circle(pantalla, (20, 20, 20), (cx + ox, cy - 3), 2)


# ======================================================================
#  CRIATURA MARCIANA (enemigo)
# ======================================================================
class CriaturaMarciana(EntidadJuego):
    def __init__(self, x: float, y: float, objetivo: Explorador,
                 dano: int = 12, velocidad: float = 120.0) -> None:
        super().__init__(x, y, 60, "criatura", 16)
        if dano <= 0 or velocidad <= 0:
            raise ValueError("dano y velocidad deben ser positivos")
        self.__dano: int = dano
        self.__velocidad: float = velocidad
        self.__objetivo: Explorador = objetivo        # ASOCIACIÓN
        self.__enfriamiento: float = 0.0

    def perseguir(self, e: Explorador, dt: float) -> None:
        dx, dy = e.getX() - self._position_x, e.getY() - self._position_y
        norma = math.hypot(dx, dy)
        if norma > 0:
            paso = self.__velocidad * dt / norma
            self.setPosicion(self._position_x + dx * paso, self._position_y + dy * paso)

    def atacar(self, e: EntidadJuego) -> None:
        if self.__enfriamiento <= 0:
            e.recibirDano(self.__dano)
            self.__enfriamiento = 1.0

    def update(self, dt: float) -> None:
        super().update(dt)
        self.__enfriamiento = max(0.0, self.__enfriamiento - dt)
        if not self.__objetivo.estaViva():
            return
        self.perseguir(self.__objetivo, dt)
        if self.colisionaCon(self.__objetivo):
            self.atacar(self.__objetivo)

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        cx, cy = int(self._position_x), int(self._position_y)
        for i in range(8):
            ang = i * math.pi / 4 + self._tiempo * 2
            pygame.draw.line(pantalla, (200, 40, 40), (cx, cy),
                             (cx + int(math.cos(ang) * (self._radio + 7)),
                              cy + int(math.sin(ang) * (self._radio + 7))), 3)
        pygame.draw.circle(pantalla, (170, 30, 45), (cx, cy), self._radio)
        for ox in (-5, 5):
            pygame.draw.circle(pantalla, (255, 230, 60), (cx + ox, cy - 2), 4)
            pygame.draw.circle(pantalla, (0, 0, 0), (cx + ox, cy - 2), 2)
