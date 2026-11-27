"""Clase base abstracta de los niveles (contiene las entidades: composición).

Relaciones UML que materializa esta clase
-----------------------------------------
* COMPOSICIÓN   Nivel *-- EntidadJuego, Nivel *-- Tormenta: las crea en
  ``reiniciar()`` / ``_lanzarTormenta()`` y las destruye con el nivel.
* DEPENDENCIA   Nivel ..> TormentaFactory: solo la usa para *solicitar* tormentas.
* Patrón Observer: el Nivel es *Sujeto* (avisa ``MARCIANO_ALIADO``, ``NIVEL_COMPLETADO``,
  ``JUGADOR_DERROTADO``) y a la vez *Observador* del Explorador, cuyos eventos
  (``SALUD_CAMBIADA``, ``MINERAL_RECOLECTADO``, ``BASE_CONSTRUIDA``) retransmite.
  Así los observadores externos se suscriben una sola vez al Nivel, aunque el
  Explorador se vuelva a crear en cada ``reiniciar()``.
"""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pygame

from src import config
from src.entidades.base import Base
from src.entidades.criatura import CriaturaMarciana
from src.entidades.entidad_juego import EntidadJuego
from src.entidades.estados import MarcianoAsustado
from src.entidades.explorador import Explorador
from src.entidades.marciano import Marciano
from src.entidades.mineral import Mineral
from src.patrones.observer import EventoDominio, Observador, Sujeto
from src.tormentas.fabrica import TormentaFactory
from src.tormentas.tormenta import Tormenta


class Nivel(Sujeto, Observador, ABC):
    def __init__(self, numero: int, fabrica: TormentaFactory) -> None:
        if numero <= 0:
            raise ValueError("numero de nivel inválido")
        Sujeto.__init__(self)
        self.__numero: int = numero
        self.__completado: bool = False
        self.__derrotaNotificada: bool = False
        self.__contadorTormentas: int = 0
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
        self._aliadosFormados: int = 0

    # ---- acceso ----
    def getNumero(self) -> int:
        return self.__numero

    def isCompletado(self) -> bool:
        return self.__completado

    def getTiempo(self) -> float:
        return self._tiempo

    def getAliadosFormados(self) -> int:
        return self._aliadosFormados

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
        self.__derrotaNotificada = False
        self.__contadorTormentas = 0
        self._tiempo = 0.0
        self._aliadosFormados = 0
        self.__explorador = Explorador(config.ANCHO / 2, config.ALTO / 2 + 20)
        self.__explorador.suscribir(self)          # el Nivel observa al Explorador
        self.__entidades.append(self.__explorador)
        self._poblar()

    # ---- Observer: el Nivel retransmite los eventos del Explorador ----
    def actualizar(self, evento: str, datos: Dict[str, Any]) -> None:
        datos["nivel"] = self.__numero
        self.notificar(evento, datos)

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

    def _lanzarSiguienteTormenta(self, ciclo: Sequence[str]) -> None:
        """Rota por ``ciclo`` ignorando los tipos que la fábrica no tenga registrados."""
        registrados = self.__fabrica.tiposDisponibles()
        disponibles = [t for t in ciclo if t in registrados]
        if not disponibles:
            return
        tipo = disponibles[self.__contadorTormentas % len(disponibles)]
        self.__contadorTormentas += 1
        self._lanzarTormenta(tipo)

    # ---- acciones del jugador ----
    def moverExplorador(self, dx: float, dy: float) -> None:
        self.getExplorador().establecerDireccion(dx, dy)

    def construirBase(self) -> bool:
        explorador = self.getExplorador()
        if any(b.estaViva() and explorador.distanciaA(b) < 120 for b in self._bases):
            return False
        base = explorador.construirBase()
        if base is None:
            return False
        self.__entidades.append(base)
        self._bases.append(base)
        return True

    def ofrecerMineral(self) -> bool:
        explorador = self.getExplorador()
        cercano: Optional[Marciano] = None
        mejor = Marciano.ALCANCE_OFRENDA
        for m in self._marcianos:
            d = explorador.distanciaA(m)
            if m.aceptaOfrenda() and d < mejor:
                cercano, mejor = m, d
        if cercano is None or not explorador.gastarMinerales(1):
            return False
        cercano.ofrecerMineral()
        self._aliadosFormados += 1
        self.notificar(EventoDominio.MARCIANO_ALIADO,
                       {"x": round(cercano.getX()), "y": round(cercano.getY()), "nivel": self.__numero})
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
        self.__evaluarFinDeNivel()

    def __evaluarFinDeNivel(self) -> None:
        explorador = self.getExplorador()
        if not explorador.estaViva():
            if not self.__derrotaNotificada:
                self.__derrotaNotificada = True
                self.notificar(EventoDominio.JUGADOR_DERROTADO,
                               {"nivel": self.__numero, "tiempo": round(self._tiempo, 1)})
        elif not self.__completado and self.verificarVictoria():
            self.__completado = True
            self.notificar(EventoDominio.NIVEL_COMPLETADO,
                           {"nivel": self.__numero, "salud": explorador.getSalud(),
                            "minerales": explorador.getInventarioMinerales(),
                            "tiempo": round(self._tiempo, 1)})

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
