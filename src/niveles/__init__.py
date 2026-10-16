"""Niveles: un Nivel CONTIENE (composición) a sus entidades y tormentas."""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import pygame

from src import config
from src.entidades import (Base, CriaturaMarciana, EntidadJuego, Explorador, Marciano,
                       MarcianoAsustado, Mineral)
from src.tormentas import Tormenta, TormentaFactory


class Nivel(ABC):
    def __init__(self, numero: int, fabrica: TormentaFactory) -> None:
        if numero <= 0:
            raise ValueError("numero de nivel inválido")
        self.__numero: int = numero
        self.__completado: bool = False
        self.__fabrica: TormentaFactory = fabrica          # DEPENDENCIA: "solicita" tormentas
        # COMPOSICIÓN: estas entidades nacen y mueren con el nivel
        self.__entidades: List[EntidadJuego] = []
        self.__tormentas: List[Tormenta] = []
        self.__explorador: Optional[Explorador] = None
        # listas tipadas para las reglas (sin condicionales de tipo)
        self._minerales: List[Mineral] = []
        self._bases: List[Base] = []
        self._marcianos: List[Marciano] = []
        self._criaturas: List[CriaturaMarciana] = []
        self._tiempo: float = 0.0

    # ---- acceso ----
    def getNumero(self) -> int:
        return self.__numero

    def isCompletado(self) -> bool:
        return self.__completado

    def getTiempo(self) -> float:
        return self._tiempo

    def getExplorador(self) -> Explorador:
        if self.__explorador is None:
            raise RuntimeError("El nivel no fue iniciado: llama a reiniciar()")
        return self.__explorador

    # ---- ciclo de vida ----
    def reiniciar(self) -> None:
        self.__entidades.clear()
        self.__tormentas.clear()
        self._minerales.clear()
        self._bases.clear()
        self._marcianos.clear()
        self._criaturas.clear()
        self.__completado = False
        self._tiempo = 0.0
        self.__explorador = Explorador(config.ANCHO / 2, config.ALTO / 2 + 20)
        self.__entidades.append(self.__explorador)
        self._poblar()

    # ---- creación de entidades (composición) ----
    def _posicionLibre(self, distanciaMin: float = 150.0) -> Tuple[float, float]:
        e = self.getExplorador()
        x, y = config.ANCHO / 2, config.HUD_ALTO + 60
        for _ in range(60):
            x = random.uniform(40, config.ANCHO - 40)
            y = random.uniform(config.HUD_ALTO + 40, config.ALTO - 40)
            if math.hypot(x - e.getX(), y - e.getY()) >= distanciaMin:
                break
        return x, y

    def _crearMineral(self) -> Mineral:
        x, y = self._posicionLibre(60)
        m = Mineral(x, y, random.choice([1, 1, 1, 2]))
        self.__entidades.append(m)
        self._minerales.append(m)
        return m

    def _crearMarciano(self) -> Marciano:
        x, y = self._posicionLibre(200)
        m = Marciano(x, y, self.getExplorador(), MarcianoAsustado())
        self.__entidades.append(m)
        self._marcianos.append(m)
        return m

    def _crearCriatura(self) -> CriaturaMarciana:
        x, y = self._posicionLibre(320)
        c = CriaturaMarciana(x, y, self.getExplorador())
        self.__entidades.append(c)
        self._criaturas.append(c)
        return c

    def _lanzarTormenta(self, tipo: str) -> None:
        self.__tormentas.append(self.__fabrica.crearTormenta(tipo))

    # ---- acciones del jugador ----
    def moverExplorador(self, dx: float, dy: float) -> None:
        self.getExplorador().establecerDireccion(dx, dy)

    def construirBase(self) -> bool:
        base = self.getExplorador().construirBase()
        if base is None:
            return False
        self.__entidades.append(base)
        self._bases.append(base)
        return True

    def ofrecerMineral(self) -> bool:
        explorador = self.getExplorador()
        cercano: Optional[Marciano] = None
        mejor = 110.0
        for m in self._marcianos:
            d = explorador.distanciaA(m)
            if m.aceptaOfrenda() and d < mejor:
                cercano, mejor = m, d
        if cercano is None or not explorador.gastarMinerales(1):
            return False
        cercano.ofrecerMineral()
        return True

    # ---- bucle ----
    def update(self, dt: float) -> None:
        self._tiempo += dt
        for entidad in self.__entidades:          # POLIMORFISMO: no importa el tipo concreto
            entidad.update(dt)
        self.__procesarColisiones()
        for tormenta in self.__tormentas:         # POLIMORFISMO también en tormentas
            tormenta.update(dt)
            tormenta.aplicarEfecto(self.__entidades)
        self.__tormentas = [t for t in self.__tormentas if not t.haTerminado()]
        self.ejecutarReglas(dt)
        self.__limpiarMuertos()
        if self.verificarVictoria():
            self.__completado = True

    def __procesarColisiones(self) -> None:
        explorador = self.getExplorador()
        for mineral in self._minerales:
            if mineral.estaViva() and explorador.colisionaCon(mineral):
                valor = mineral.getValorCombustible()
                explorador.recolectar(mineral)
                self._alRecolectar(valor)

    def __limpiarMuertos(self) -> None:
        """Elimina las referencias a objetos muertos para evitar fugas lógicas de memoria."""
        self.__entidades = [e for e in self.__entidades if e.estaViva()]
        self._minerales[:] = [e for e in self._minerales if e.estaViva()]
        self._bases[:] = [e for e in self._bases if e.estaViva()]
        self._marcianos[:] = [e for e in self._marcianos if e.estaViva()]
        self._criaturas[:] = [e for e in self._criaturas if e.estaViva()]

    def render(self, pantalla: pygame.Surface) -> None:
        self._dibujarEscenario(pantalla)
        explorador = self.getExplorador()
        for entidad in self.__entidades:
            if entidad is not explorador:
                entidad.render(pantalla)
        for tormenta in self.__tormentas:
            tormenta.render(pantalla)
        if explorador.estaViva():
            explorador.render(pantalla)

    # ---- hooks / contrato de las subclases ----
    def _alRecolectar(self, valor: int) -> None:
        """Hook opcional."""

    def _dibujarEscenario(self, pantalla: pygame.Surface) -> None:
        """Hook opcional."""

    def _mantenerMinerales(self, minimo: int) -> None:
        while len(self._minerales) < minimo:
            self._crearMineral()

    @abstractmethod
    def _poblar(self) -> None:
        ...

    @abstractmethod
    def ejecutarReglas(self, dt: float) -> None:
        ...

    @abstractmethod
    def verificarVictoria(self) -> bool:
        ...

    @abstractmethod
    def descripcionObjetivo(self) -> str:
        ...


# ----------------------------------------------------------------------
class NivelSupervivencia(Nivel):
    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(1, fabrica)
        self.__mineralesObjetivo: int = 10
        self.__mineralesRecolectados: int = 0
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0
        self.__contadorTormentas: int = 0

    def reiniciar(self) -> None:
        self.__mineralesRecolectados = 0
        self.__tTormenta = 5.0
        self.__tCriatura = 0.0
        self.__contadorTormentas = 0
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
            tipo = "radiacion" if self.__contadorTormentas % 2 == 0 else "meteoritos"
            self.__contadorTormentas += 1
            self._lanzarTormenta(tipo)
        if self.__tCriatura >= 14.0 and len(self._criaturas) < 4:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(6)

    def verificarVictoria(self) -> bool:
        return self.__mineralesRecolectados >= self.__mineralesObjetivo

    def descripcionObjetivo(self) -> str:
        return f"Recolecta combustible: {self.__mineralesRecolectados}/{self.__mineralesObjetivo}"


# ----------------------------------------------------------------------
class NivelDefensa(Nivel):
    DURACION: float = 40.0
    TIPOS: Tuple[str, ...] = ("meteoritos", "radiacion", "meteoritos")

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(2, fabrica)
        self.__basesObjetivo: int = 3
        self.__basesProtegidas: int = 0
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0
        self.__contadorTormentas: int = 0

    def reiniciar(self) -> None:
        self.__basesProtegidas = 0
        self.__tTormenta = 5.0
        self.__tCriatura = 0.0
        self.__contadorTormentas = 0
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
            tipo = self.TIPOS[self.__contadorTormentas % len(self.TIPOS)]
            self.__contadorTormentas += 1
            self._lanzarTormenta(tipo)
        if self.__tCriatura >= 10.0 and len(self._criaturas) < 5:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(4)

    def verificarVictoria(self) -> bool:
        return self.getTiempo() >= self.DURACION and self.__basesProtegidas >= self.__basesObjetivo

    def descripcionObjetivo(self) -> str:
        restante = max(0, math.ceil(self.DURACION - self.getTiempo()))
        return (f"Defiende {self.__basesProtegidas}/{self.__basesObjetivo} bases "
                f"(ESPACIO = construir) · Tiempo: {restante}s")


# ----------------------------------------------------------------------
class NivelEscape(Nivel):
    COMBUSTIBLE_NECESARIO: int = 6

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(3, fabrica)
        self.__cohete: Tuple[float, float] = (config.ANCHO - 90.0, config.ALTO - 90.0)
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0
        self.__contadorTormentas: int = 0

    def reiniciar(self) -> None:
        self.__tTormenta = 3.0
        self.__tCriatura = 0.0
        self.__contadorTormentas = 0
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
            tipo = "radiacion" if self.__contadorTormentas % 2 else "meteoritos"
            self.__contadorTormentas += 1
            self._lanzarTormenta(tipo)
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
        cx, cy = int(self.__cohete[0]), int(self.__cohete[1])
        pygame.draw.polygon(pantalla, (220, 60, 60), [(cx - 16, cy - 10), (cx, cy - 48), (cx + 16, cy - 10)])
        pygame.draw.rect(pantalla, (225, 225, 235), (cx - 16, cy - 10, 32, 46))
        pygame.draw.circle(pantalla, (60, 160, 230), (cx, cy + 6), 7)
        pygame.draw.polygon(pantalla, (220, 60, 60), [(cx - 16, cy + 36), (cx - 28, cy + 48), (cx - 16, cy + 20)])
        pygame.draw.polygon(pantalla, (220, 60, 60), [(cx + 16, cy + 36), (cx + 28, cy + 48), (cx + 16, cy + 20)])
