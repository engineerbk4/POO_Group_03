"""Niveles: un Nivel CONTIENE (composición) a sus entidades y tormentas.

Jerarquía:
  Nivel (ABC)
   ├── NivelSupervivencia  (N-1)  Recolecta 10 minerales      – curva suave
   ├── NivelDefensa        (N-2)  Mantén 3 bases 45 s          – presión media
   ├── NivelEscape         (N-3)  Llena el cohete y huye       – presión alta
   ├── NivelTormenta       (N-4)  Sobrevive 60 s sin bases     – frenético
   └── NivelBoss           (N-5)  Elimina al Jefe Marciano     – climax

Balanceo (resumen de cambios respecto a la versión original):
  N-1: tormenta cada 12 s (antes 9 s), 1 criatura inicial (antes 2).
  N-2: duración 45 s (antes 40 s), tormenta cada 10 s (antes 8 s),
       máx. 4 criaturas (antes 5).
  N-3: primera tormenta a los 5 s (antes 3 s), máx. 3 criaturas (antes 4),
       mineral mínimo 6 (antes 5), cohete más grande para ser accesible.
  N-4: nuevo – solo tormentas simultáneas + muchas criaturas; sin bases.
  N-5: nuevo – Jefe Marciano (entidad especial) con mucha vida; al morir
       el jefe se gana. Tormenta permanente de radiación + meteoritos.
"""
from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import pygame

from src import config
from src.entidades import (Base, CriaturaMarciana, EntidadJuego, Explorador,
                           Marciano, MarcianoAsustado, Mineral)
from src.tormentas import Tormenta, TormentaFactory


# ======================================================================
#  CLASE BASE ABSTRACTA
# ======================================================================
class Nivel(ABC):
    def __init__(self, numero: int, fabrica: TormentaFactory) -> None:
        if numero <= 0:
            raise ValueError("numero de nivel inválido")
        self.__numero: int = numero
        self.__completado: bool = False
        self.__fabrica: TormentaFactory = fabrica          # DEPENDENCIA
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

    # ---- acceso -------------------------------------------------------
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

    # ---- ciclo de vida ------------------------------------------------
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

    # ---- creación de entidades (composición) --------------------------
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

    def _registrarEntidad(self, e: EntidadJuego) -> None:
        """Registra una entidad ad-hoc (p.ej. el Jefe) en el game loop."""
        self.__entidades.append(e)

    def _lanzarTormenta(self, tipo: str) -> None:
        self.__tormentas.append(self.__fabrica.crearTormenta(tipo))

    # ---- acciones del jugador ----------------------------------------
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

    # ---- bucle --------------------------------------------------------
    def update(self, dt: float) -> None:
        self._tiempo += dt
        for entidad in self.__entidades:          # POLIMORFISMO
            entidad.update(dt)
        self.__procesarColisiones()
        for tormenta in self.__tormentas:         # POLIMORFISMO
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

    # ---- hooks / contrato de las subclases ----------------------------
    def _alRecolectar(self, valor: int) -> None:
        """Hook opcional."""

    def _dibujarEscenario(self, pantalla: pygame.Surface) -> None:
        """Hook opcional."""

    def _mantenerMinerales(self, minimo: int) -> None:
        while len(self._minerales) < minimo:
            self._crearMineral()

    @abstractmethod
    def _poblar(self) -> None: ...

    @abstractmethod
    def ejecutarReglas(self, dt: float) -> None: ...

    @abstractmethod
    def verificarVictoria(self) -> bool: ...

    @abstractmethod
    def descripcionObjetivo(self) -> str: ...

    # ---- narrativa (hook con valor por defecto) -----------------------
    def narrativa(self) -> str:
        """Texto breve que se muestra en la transición antes de este nivel."""
        return ""


# ======================================================================
#  NIVEL 1 — SUPERVIVENCIA (recolecta 10 minerales)
#  Cambios de balance: tormenta cada 12 s (antes 9), 1 criatura inicial,
#  spawn de criatura extra cada 18 s (antes 14).
# ======================================================================
class NivelSupervivencia(Nivel):
    _MINERAL_OBJETIVO: int = 10
    _TORMENTA_INTERVALO: float = 12.0   # s entre tormentas (↑ desde 9)
    _CRIATURA_INTERVALO: float = 18.0   # s entre spawns (↑ desde 14)
    _MAX_CRIATURAS: int = 3             # límite suave (↓ desde 4)

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(1, fabrica)
        self.__mineralesRecolectados: int = 0
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0
        self.__contadorTormentas: int = 0

    def reiniciar(self) -> None:
        self.__mineralesRecolectados = 0
        self.__tTormenta = 6.0          # primera tormenta a los 6 s (antes 0, disparaba enseguida)
        self.__tCriatura = 0.0
        self.__contadorTormentas = 0
        super().reiniciar()

    def _poblar(self) -> None:
        for _ in range(7):              # 7 minerales al inicio (antes 6)
            self._crearMineral()
        for _ in range(3):
            self._crearMarciano()
        self._crearCriatura()           # 1 criatura inicial (antes 2)

    def _alRecolectar(self, valor: int) -> None:
        self.__mineralesRecolectados += valor

    def ejecutarReglas(self, dt: float) -> None:
        self.__tTormenta += dt
        self.__tCriatura += dt
        if self.__tTormenta >= self._TORMENTA_INTERVALO:
            self.__tTormenta = 0.0
            tipo = "radiacion" if self.__contadorTormentas % 2 == 0 else "meteoritos"
            self.__contadorTormentas += 1
            self._lanzarTormenta(tipo)
        if self.__tCriatura >= self._CRIATURA_INTERVALO and len(self._criaturas) < self._MAX_CRIATURAS:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(6)

    def verificarVictoria(self) -> bool:
        return self.__mineralesRecolectados >= self._MINERAL_OBJETIVO

    def descripcionObjetivo(self) -> str:
        return f"Recolecta combustible: {self.__mineralesRecolectados}/{self._MINERAL_OBJETIVO}"

    def narrativa(self) -> str:
        return (
            "Tu nave aterrizó en Marte. Los sensores detectan depósitos de\n"
            "combustible dispersos por la superficie. ¡Recoléctalos antes\n"
            "de que las tormentas de radiación te atrapen!"
        )


# ======================================================================
#  NIVEL 2 — DEFENSA (mantén 3 bases durante 45 s)
#  Cambios de balance: 45 s (antes 40), tormenta cada 10 s (antes 8),
#  máx 4 criaturas (antes 5), 5 minerales iniciales (antes 4).
# ======================================================================
class NivelDefensa(Nivel):
    DURACION: float = 45.0              # s de resistencia (↑ desde 40)
    TIPOS: Tuple[str, ...] = ("meteoritos", "radiacion", "meteoritos")
    _TORMENTA_INTERVALO: float = 10.0   # s entre tormentas (↑ desde 8)
    _CRIATURA_INTERVALO: float = 12.0   # s entre spawns (↑ desde 10)
    _MAX_CRIATURAS: int = 4             # límite suave (↓ desde 5)

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(2, fabrica)
        self.__basesObjetivo: int = 3
        self.__basesProtegidas: int = 0
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0
        self.__contadorTormentas: int = 0

    def reiniciar(self) -> None:
        self.__basesProtegidas = 0
        self.__tTormenta = 7.0          # primera tormenta a los 7 s (antes 5)
        self.__tCriatura = 0.0
        self.__contadorTormentas = 0
        super().reiniciar()

    def _poblar(self) -> None:
        self.getExplorador().almacenar(6)
        for _ in range(5):              # 5 minerales (antes 4)
            self._crearMineral()
        for _ in range(2):
            self._crearMarciano()
        for _ in range(2):
            self._crearCriatura()

    def ejecutarReglas(self, dt: float) -> None:
        self.__basesProtegidas = len(self._bases)
        self.__tTormenta += dt
        self.__tCriatura += dt
        if self.__tTormenta >= self._TORMENTA_INTERVALO:
            self.__tTormenta = 0.0
            tipo = self.TIPOS[self.__contadorTormentas % len(self.TIPOS)]
            self.__contadorTormentas += 1
            self._lanzarTormenta(tipo)
        if self.__tCriatura >= self._CRIATURA_INTERVALO and len(self._criaturas) < self._MAX_CRIATURAS:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(4)

    def verificarVictoria(self) -> bool:
        return self.getTiempo() >= self.DURACION and self.__basesProtegidas >= self.__basesObjetivo

    def descripcionObjetivo(self) -> str:
        restante = max(0, math.ceil(self.DURACION - self.getTiempo()))
        return (f"Defiende {self.__basesProtegidas}/{self.__basesObjetivo} bases "
                f"(ESPACIO = construir) · Tiempo: {restante}s")

    def narrativa(self) -> str:
        return (
            "Las criaturas marcianas atacan tu campamento base.\n"
            "Construye estructuras de refugio y aguanta el asedio\n"
            "hasta que llegue el refuerzo orbital."
        )


# ======================================================================
#  NIVEL 3 — ESCAPE (llena el cohete con 6 de combustible y huye)
#  Cambios de balance: primera tormenta a los 5 s (antes 3), máx 3
#  criaturas (antes 4), mínimo 6 minerales en mapa (antes 5), radio
#  del cohete ampliado a 70 (antes 60).
# ======================================================================
class NivelEscape(Nivel):
    COMBUSTIBLE_NECESARIO: int = 6
    _RADIO_COHETE: float = 70.0         # zona de embarque más generosa (antes 60)
    _TORMENTA_INTERVALO: float = 10.0   # s entre tormentas (↑ desde 9)
    _CRIATURA_INTERVALO: float = 18.0   # s entre spawns (↑ desde 16)
    _MAX_CRIATURAS: int = 3             # límite suave (↓ desde 4)

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(3, fabrica)
        self.__cohete: Tuple[float, float] = (config.ANCHO - 90.0, config.ALTO - 90.0)
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0
        self.__contadorTormentas: int = 0

    def reiniciar(self) -> None:
        self.__tTormenta = 5.0          # primera tormenta a los 5 s (antes 3)
        self.__tCriatura = 0.0
        self.__contadorTormentas = 0
        super().reiniciar()

    def _poblar(self) -> None:
        for _ in range(8):              # 8 minerales iniciales (antes 7)
            self._crearMineral()
        for _ in range(3):
            self._crearMarciano()
        for _ in range(2):
            self._crearCriatura()

    def __cercaDelCohete(self) -> bool:
        e = self.getExplorador()
        return math.hypot(e.getX() - self.__cohete[0],
                          e.getY() - self.__cohete[1]) < self._RADIO_COHETE

    def ejecutarReglas(self, dt: float) -> None:
        self.__tTormenta += dt
        self.__tCriatura += dt
        if self.__tTormenta >= self._TORMENTA_INTERVALO:
            self.__tTormenta = 0.0
            tipo = "radiacion" if self.__contadorTormentas % 2 else "meteoritos"
            self.__contadorTormentas += 1
            self._lanzarTormenta(tipo)
        if self.__tCriatura >= self._CRIATURA_INTERVALO and len(self._criaturas) < self._MAX_CRIATURAS:
            self.__tCriatura = 0.0
            self._crearCriatura()
        self._mantenerMinerales(6)      # mínimo 6 en mapa (antes 5)

    def verificarVictoria(self) -> bool:
        listo = self.getExplorador().getInventarioMinerales() >= self.COMBUSTIBLE_NECESARIO
        return listo and self.__cercaDelCohete()

    def descripcionObjetivo(self) -> str:
        inv = self.getExplorador().getInventarioMinerales()
        if inv >= self.COMBUSTIBLE_NECESARIO:
            return "¡Tanque lleno! Corre al cohete (esquina inferior derecha)"
        return f"Reúne combustible para el cohete: {inv}/{self.COMBUSTIBLE_NECESARIO}"

    def narrativa(self) -> str:
        return (
            "El suelo marciano tiembla. La ventana de lanzamiento se abre\n"
            "en minutos. Recoge el combustible restante y llega al cohete\n"
            "antes de que las tormentas te atrapen para siempre."
        )

    def _dibujarEscenario(self, pantalla: pygame.Surface) -> None:
        cx, cy = int(self.__cohete[0]), int(self.__cohete[1])
        # Zona de embarque (aro pulsante)
        pulso = int(55 + 20 * math.sin(pygame.time.get_ticks() / 300))
        from src.graficos import circulo_alpha
        circulo_alpha(pantalla, (255, 230, 100), (cx, cy), self._RADIO_COHETE, pulso)
        pygame.draw.circle(pantalla, (255, 230, 100), (cx, cy), int(self._RADIO_COHETE), 2)
        # Cohete
        pygame.draw.polygon(pantalla, (220, 60, 60),
                            [(cx - 16, cy - 10), (cx, cy - 48), (cx + 16, cy - 10)])
        pygame.draw.rect(pantalla, (225, 225, 235), (cx - 16, cy - 10, 32, 46))
        pygame.draw.circle(pantalla, (60, 160, 230), (cx, cy + 6), 7)
        pygame.draw.polygon(pantalla, (220, 60, 60),
                            [(cx - 16, cy + 36), (cx - 28, cy + 48), (cx - 16, cy + 20)])
        pygame.draw.polygon(pantalla, (220, 60, 60),
                            [(cx + 16, cy + 36), (cx + 28, cy + 48), (cx + 16, cy + 20)])


# ======================================================================
#  NIVEL 4 — TORMENTA PERMANENTE (sobrevive 60 s sin bases)
#  Mecánica nueva: tormentas simultáneas y oleadas de criaturas.
#  No se puede construir base (el HUD lo indica).  Muchos minerales
#  en el mapa para curación indirecta vía aliados.
# ======================================================================
class NivelTormenta(Nivel):
    DURACION: float = 60.0
    _TORMENTA_INTERVALO: float = 7.0    # tormentas muy frecuentes
    _CRIATURA_INTERVALO: float = 8.0
    _MAX_CRIATURAS: int = 6
    _OLEADA_INTERVALO: float = 20.0     # cada 20 s llega oleada extra

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(4, fabrica)
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0
        self.__tOleada: float = 0.0
        self.__contadorTormentas: int = 0

    def reiniciar(self) -> None:
        self.__tTormenta = 3.0          # primera tormenta pronto
        self.__tCriatura = 0.0
        self.__tOleada = 0.0
        self.__contadorTormentas = 0
        super().reiniciar()

    def _poblar(self) -> None:
        for _ in range(10):             # muchos minerales para convertir marcianos aliados
            self._crearMineral()
        for _ in range(5):             # 5 marcianos: convirtiéndolos te curan
            self._crearMarciano()
        for _ in range(3):
            self._crearCriatura()

    def ejecutarReglas(self, dt: float) -> None:
        self.__tTormenta += dt
        self.__tCriatura += dt
        self.__tOleada += dt

        if self.__tTormenta >= self._TORMENTA_INTERVALO:
            self.__tTormenta = 0.0
            # Alterna doble tormenta cada 3 ciclos
            if self.__contadorTormentas % 3 == 2:
                self._lanzarTormenta("radiacion")
                self._lanzarTormenta("meteoritos")
            else:
                tipo = "radiacion" if self.__contadorTormentas % 2 == 0 else "meteoritos"
                self._lanzarTormenta(tipo)
            self.__contadorTormentas += 1

        if self.__tCriatura >= self._CRIATURA_INTERVALO and len(self._criaturas) < self._MAX_CRIATURAS:
            self.__tCriatura = 0.0
            self._crearCriatura()

        # Oleada: 2 criaturas extra sin respetar el tope momentáneamente
        if self.__tOleada >= self._OLEADA_INTERVALO:
            self.__tOleada = 0.0
            self._crearCriatura()
            self._crearCriatura()

        self._mantenerMinerales(8)

    def verificarVictoria(self) -> bool:
        return self.getTiempo() >= self.DURACION and self.getExplorador().estaViva()

    def descripcionObjetivo(self) -> str:
        restante = max(0, math.ceil(self.DURACION - self.getTiempo()))
        return f"¡SOBREVIVE! Tiempo restante: {restante}s  ·  Bases deshabilitadas en esta zona"

    def narrativa(self) -> str:
        return (
            "El núcleo marciano está activo. Las bases de refugio son\n"
            "inestables en esta zona: solo la velocidad y los aliados\n"
            "marcianos pueden salvarte. ¡Aguanta 60 segundos!"
        )

    def _dibujarEscenario(self, pantalla: pygame.Surface) -> None:
        """Fondo rojizo más intenso para señalar el peligro extremo."""
        overlay = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        pulso = int(18 + 10 * math.sin(pygame.time.get_ticks() / 400))
        overlay.fill((160, 20, 0, pulso))
        pantalla.blit(overlay, (0, 0))


# ======================================================================
#  ENTIDAD ESPECIAL — JEFE MARCIANO (solo para el nivel 5)
#  Hereda de CriaturaMarciana para reutilizar AI y colisión.
#  Sobrescribe _dibujarCuerpo con un sprite distinto.
# ======================================================================
class JefeMarciano(CriaturaMarciana):
    """Criatura Jefe: más grande, más vida, más daño, más lento."""

    def __init__(self, x: float, y: float, objetivo: Explorador, salud: int = 150) -> None:
        super().__init__(x, y, objetivo, dano=20, velocidad=65.0, salud=salud, radio=32)

    def estaViva(self) -> bool:
        return self.getSalud() > 0

    def _dibujarCuerpo(self, pantalla: pygame.Surface) -> None:
        cx, cy = int(self.getX()), int(self.getY())
        t = pygame.time.get_ticks() / 1000.0
        # Corona de púas
        for i in range(12):
            ang = i * math.pi / 6 + t * 1.5
            px = cx + int(math.cos(ang) * (self._radio + 14))
            py = cy + int(math.sin(ang) * (self._radio + 14))
            pygame.draw.line(pantalla, (220, 30, 30), (cx, cy), (px, py), 3)
        # Cuerpo
        pygame.draw.circle(pantalla, (110, 10, 25), (cx, cy), self._radio)
        pygame.draw.circle(pantalla, (200, 40, 60), (cx, cy), self._radio, 3)
        # Ojos brillantes
        for ox in (-9, 9):
            pygame.draw.circle(pantalla, (255, 200, 0), (cx + ox, cy - 6), 7)
            pygame.draw.circle(pantalla, (0, 0, 0), (cx + ox, cy - 6), 3)
        # Boca amenazante
        pygame.draw.arc(pantalla, (255, 60, 60),
                        (cx - 12, cy + 4, 24, 14), math.pi, 2 * math.pi, 3)
        # Barra de vida extra visible (propia del jefe)
        ancho_barra = 70
        xb = cx - ancho_barra // 2
        yb = cy - self._radio - 16
        pygame.draw.rect(pantalla, (60, 0, 0), (xb, yb, ancho_barra, 8))
        relleno = int(ancho_barra * self.getSalud() / self.getSaludMaxima())
        pygame.draw.rect(pantalla, (220, 40, 40), (xb, yb, relleno, 8))
        pygame.draw.rect(pantalla, (255, 100, 100), (xb, yb, ancho_barra, 8), 1)


# ======================================================================
#  NIVEL 5 — BOSS (derrota al Jefe Marciano)
#  Mecánica: el Jefe tiene 300 HP; las criaturas normales respawn
#  constantemente.  Tormentas dobles muy frecuentes.
# ======================================================================
class NivelBoss(Nivel):
    _VIDA_JEFE: int = 150
    _TORMENTA_INTERVALO: float = 8.0
    _CRIATURA_INTERVALO: float = 10.0
    _MAX_CRIATURAS: int = 5

    def __init__(self, fabrica: TormentaFactory) -> None:
        super().__init__(5, fabrica)
        self.__jefe: Optional[JefeMarciano] = None
        self.__tTormenta: float = 0.0
        self.__tCriatura: float = 0.0
        self.__contadorTormentas: int = 0

    def reiniciar(self) -> None:
        self.__jefe = None
        self.__tTormenta = 5.0
        self.__tCriatura = 0.0
        self.__contadorTormentas = 0
        super().reiniciar()

    def _poblar(self) -> None:
        # Jefe en posición contraria al explorador
        self.__jefe = JefeMarciano(
            config.ANCHO - 120.0,
            config.HUD_ALTO + 100.0,
            self.getExplorador(),
            salud=self._VIDA_JEFE,
        )
        self._registrarEntidad(self.__jefe)

        for _ in range(6):
            self._crearMineral()
        for _ in range(3):
            self._crearMarciano()
        for _ in range(2):
            self._crearCriatura()

    def ejecutarReglas(self, dt: float) -> None:
        self.__tTormenta += dt
        self.__tCriatura += dt

        if self.__tTormenta >= self._TORMENTA_INTERVALO:
            self.__tTormenta = 0.0
            self._lanzarTormenta("radiacion")
            if self.__contadorTormentas % 2 == 1:   # meteoritos en ciclos impares
                self._lanzarTormenta("meteoritos")
            self.__contadorTormentas += 1

        if self.__tCriatura >= self._CRIATURA_INTERVALO and len(self._criaturas) < self._MAX_CRIATURAS:
            self.__tCriatura = 0.0
            self._crearCriatura()

        self._mantenerMinerales(5)

    def verificarVictoria(self) -> bool:
        return self.__jefe is not None and not self.__jefe.estaViva()

    def descripcionObjetivo(self) -> str:
        if self.__jefe is None or not self.__jefe.estaViva():
            return "¡JEFE DERROTADO! ¡Victoria!"
        vida = self.__jefe.getSalud()
        return f"Derrota al Jefe Marciano  ·  Vida del Jefe: {vida} HP"

    def narrativa(self) -> str:
        return (
            "El Jefe de la Colonia Marciana te ha encontrado.\n"
            "Solo derrotándolo podrás abrir el portal de escape.\n"
            "¡Esta es tu última batalla en Marte!"
        )

    def _dibujarEscenario(self, pantalla: pygame.Surface) -> None:
        """Efecto de tormenta eléctrica de fondo."""
        overlay = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        t = pygame.time.get_ticks()
        # Relámpagos aleatorios muy tenues
        if t % 2000 < 80:
            overlay.fill((200, 200, 255, 25))
        pantalla.blit(overlay, (0, 0))
