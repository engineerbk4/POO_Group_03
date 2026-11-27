"""Patrón State aplicado al flujo del juego (reemplaza los ``if/elif self.__fase``).

``Juego`` es el *contexto*: guarda un ``EstadoJuego`` y le delega los tres
pasos del Game Loop (eventos, actualización y dibujo). Cada estado concreto
sabe a cuál estado pasar (``juego.cambiarEstado``), por lo que agregar un
estado nuevo no obliga a modificar ``Juego`` (Open/Closed).

    EstadoMenu -> EstadoNarrativa(prólogo) -> EstadoJugando <-> EstadoPausa
                       |-> EstadoNivelCompleto -> EstadoNarrativa(conexión) -> EstadoJugando (siguiente nivel)
                       |-> EstadoGameOver -> EstadoJugando (reintento)
                       '-> EstadoNarrativa(epílogo) -> EstadoVictoria -> EstadoMenu
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Tuple

import pygame

if TYPE_CHECKING:       # solo anotaciones: evita el ciclo juego <-> estados
    from src.juego import Juego

Color = Tuple[int, int, int]
Accion = Callable[["Juego"], None]      # qué hace una escena narrativa cuando el jugador la termina


class EstadoJuego(ABC):
    """Interfaz del patrón State para el flujo global del juego."""

    @abstractmethod
    def manejar_eventos(self, juego: Juego, evento: pygame.event.Event) -> None:
        ...

    @abstractmethod
    def actualizar(self, juego: Juego, dt: float) -> None:
        ...

    @abstractmethod
    def dibujar(self, juego: Juego, pantalla: pygame.Surface) -> None:
        ...

    # ---- ganchos opcionales ----
    def alEntrar(self, juego: Juego) -> None:
        """Se ejecuta al activarse el estado."""

    def alSalir(self, juego: Juego) -> None:
        """Se ejecuta al abandonarse el estado."""

    # ---- utilidades compartidas por los estados concretos ----
    @staticmethod
    def _manejarSalida(juego: Juego, evento: pygame.event.Event) -> bool:
        """Cerrar ventana o ESC terminan el juego desde cualquier estado."""
        if evento.type == pygame.QUIT or \
                (evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE):
            juego.terminar()
            return True
        return False

    @staticmethod
    def _dibujarEscena(juego: Juego, pantalla: pygame.Surface) -> None:
        """Fondo + nivel + HUD + mensajes flotantes: la escena base de los estados con nivel."""
        interfaz = juego.getInterfaz()
        interfaz.dibujarFondo(pantalla)
        nivel = juego.getNivelActual()
        nivel.render(pantalla)
        interfaz.dibujarHUD(pantalla, nivel, juego.getPuntajeNivelActual())
        interfaz.dibujarMensajes(pantalla)


# ----------------------------------------------------------------------
class EstadoMenu(EstadoJuego):
    """Menú principal con dos campos: Nombre del Piloto y Universidad (TAB alterna el foco).

    El foco evita que escribir letras como ``U`` o ``P`` en el nombre cambie la
    universidad por accidente.
    """
    FOCO_NOMBRE: int = 0
    FOCO_UNIVERSIDAD: int = 1

    def __init__(self) -> None:
        self.__nombre: str = ""
        self.__foco: int = self.FOCO_NOMBRE
        self.__reloj: float = 0.0
        self.paso = 0

    def alEntrar(self, juego: Juego) -> None:
        actual = juego.getJugador()
        # si todavía es el valor por defecto, el campo queda vacío y se muestra como marcador
        self.__nombre = "" if actual == juego.getNombrePorDefecto() else actual

    def manejar_eventos(self, juego: Juego, evento: pygame.event.Event) -> None:
        if self._manejarSalida(juego, evento) or evento.type != pygame.KEYDOWN:
            return
        if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.paso < 3:
                self.paso += 1
                if self.paso == 3: juego.setJugador(self.__nombre)
            else: juego.iniciarPartida()
        elif self.paso == 1:
            self.__elegirUniversidad(juego, evento)
        elif self.paso == 2:
            self.__editarNombre(juego, evento)
        elif self.paso == 3 and evento.key == pygame.K_TAB:
            self.paso = 1

    def __editarNombre(self, juego: Juego, evento: pygame.event.Event) -> None:
        if evento.key == pygame.K_BACKSPACE:
            self.__nombre = self.__nombre[:-1]
            return
        if evento.key == pygame.K_DELETE:
            self.__nombre = ""
            return
        caracter = evento.unicode
        if len(caracter) != 1 or not (caracter.isalnum() or caracter == " "):
            return                                  # solo letras, números y espacios
        if len(self.__nombre) >= juego.getLongitudMaxNombre():
            return
        if caracter == " " and (not self.__nombre or self.__nombre.endswith(" ")):
            return                                  # sin espacios al inicio ni dobles
        self.__nombre += caracter

    @staticmethod
    def __elegirUniversidad(juego: Juego, evento: pygame.event.Event) -> None:
        paso = 0
        if evento.key == pygame.K_u:
            paso = -1 if evento.mod & pygame.KMOD_SHIFT else 1
        elif evento.key in (pygame.K_RIGHT, pygame.K_DOWN):
            paso = 1
        elif evento.key in (pygame.K_LEFT, pygame.K_UP):
            paso = -1
        if paso:
            juego.alternarUniversidad(paso)

    def actualizar(self, juego: Juego, dt: float) -> None:
        self.__reloj += dt
        if self.paso == 0 and self.__reloj >= 3: self.paso = 1

    def dibujar(self, juego: Juego, pantalla: pygame.Surface) -> None:
        interfaz = juego.getInterfaz()
        interfaz.dibujarFondo(pantalla)
        interfaz.dibujarMenu(pantalla, juego.getUniversidad(), juego.getEstadoApi(),
                             len(juego.getUniversidades()), juego.getTop5(),
                             nombre=self.__nombre, marcador=juego.getNombrePorDefecto(),
                             maxNombre=juego.getLongitudMaxNombre(),
                             focoNombre=self.__foco == self.FOCO_NOMBRE,
                             cursorVisible=int(self.__reloj * 2) % 2 == 0, paso=self.paso, tiempo=self.__reloj)


# ----------------------------------------------------------------------
class EstadoNarrativa(EstadoJuego):
    """Escena de historia con texto que se redacta letra por letra (máquina de escribir).

    * ENTER / ESPACIO mientras se escribe -> completa el párrafo al instante.
    * ENTER / ESPACIO con el texto completo -> ejecuta ``alFinalizar`` (siguiente estado/nivel).

    El estado no conoce el flujo del juego: recibe la acción final por parámetro
    (Strategy ligera) y las fábricas ``prologo``, ``entreNiveles`` y ``epilogo``
    arman cada escena de la historia.
    """
    VELOCIDAD: float = 42.0         # caracteres por segundo
    CADA_TECLEO: int = 3            # un "tic" de sonido cada N caracteres

    __PROLOGO: str = (
        "En un rincón lejano de la galaxia, el sol de nuestro pequeño explorador se apaga poco a poco.\n\n"
        "Sus sabios descubrieron algo asombroso: el sol que ilumina Marte arde sin extinguirse desde hace "
        "miles de millones de años.\n\n"
        "Por eso viaja hasta aquí: para estudiar la atmósfera marciana, descubrir por qué su sol no se "
        "extingue y salvar a su propia estrella agonizante.")

    __EPILOGO: str = (
        "Lo logró. Con paciencia y generosidad, el explorador pacificó a los marcianos de Marte, que ahora "
        "lo llaman amigo.\n\n"
        "En su cápsula viaja la cura para estabilizar a su sol moribundo. Mientras el planeta rojo se aleja "
        "por la ventana, emprende el regreso a su hogar.")

    def __init__(self, titulo: str, subtitulo: str, texto: str, alFinalizar: Accion,
                 conCarga: bool = False) -> None:
        if not texto:
            raise ValueError("la escena narrativa necesita texto")
        self.__titulo: str = titulo
        self.__subtitulo: str = subtitulo
        self.__texto: str = texto
        self.__alFinalizar: Accion = alFinalizar
        self.__conCarga: bool = conCarga
        self.__cine = None
        self.__grupo = None
        self.__fade = None
        self.__escritos: float = 0.0        # caracteres escritos (con decimales)
        self.__visibles: int = 0            # caracteres enteros visibles
        self.__terminado: bool = False
        self.__reloj: float = 0.0           # para parpadeos y animaciones

    # ---- fábricas de las escenas de la historia ----
    @classmethod
    def prologo(cls) -> EstadoNarrativa:
        obj = cls("PRÓLOGO", "Enlace de misión · Salida hacia Marte", cls.__PROLOGO,
                   lambda juego: juego.comenzarNivelActual(), conCarga=True)
        obj.__grupo = "intro"
        return obj

    @classmethod
    def entreNiveles(cls, indiceCompletado: int) -> EstadoNarrativa:
        """Conexión narrativa tras completar el nivel con índice ``indiceCompletado`` (0 = Nivel 1)."""
        historias = {
            0: ("Nivel 1 completado · Rumbo al Nivel 2",
                "Las primeras muestras de combustible ya están a bordo. Pero los sensores del explorador "
                "acaban de detectar tormentas severas y criaturas hostiles que se acercan.\n\n"
                "Para estudiar la atmósfera y sobrevivir, deberá construir y defender 3 bases de "
                "investigación atmosférica."),
            1: ("Nivel 2 completado · Rumbo al Nivel 3",
                "Las bases resistieron la tormenta y sus instrumentos revelaron el secreto energético de "
                "la atmósfera marciana.\n\n"
                "Pero el clima se vuelve inestable. Debe reunir combustible de emergencia y llegar al "
                "cohete antes del colapso climático."),
        }
        subtitulo, texto = historias.get(
            indiceCompletado,
            (f"Nivel {indiceCompletado + 1} completado",
             "La misión continúa. El explorador se prepara para el siguiente desafío."))
        obj = cls("TRANSMISIÓN", subtitulo, texto, lambda juego: juego.avanzarNivel())
        obj.__grupo = "nivel1" if indiceCompletado == 0 else "nivel2"
        return obj

    @classmethod
    def epilogo(cls) -> EstadoNarrativa:
        obj = cls("EPÍLOGO", "Misión cumplida · Regreso a casa", cls.__EPILOGO,
                   lambda juego: juego.cambiarEstado(EstadoVictoria()))
        obj.__grupo = "final"
        return obj

    # ---- ciclo del estado ----
    def alEntrar(self, juego: Juego) -> None:
        juego.getAudio().reproducir("transmision")
        if self.__grupo:
            from src.cinematicas import Cinematica
            self.__cine = Cinematica(self.__grupo)

    def manejar_eventos(self, juego: Juego, evento: pygame.event.Event) -> None:
        if self.__cine is not None and evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                self._finalizarCine(juego)
                return
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.__fade is not None: return
                if self.__grupo == "final" and self.__cine.indice == len(self.__cine.escenas)-1 and self.__cine.textoCompleto():
                    self.__fade = 0.0
                    return
                self.__cine.avanzar()
                if self.__cine.terminada:
                    self.__alFinalizar(juego)
                else:
                    juego.getAudio().reproducir("transmision")
                return
        if self._manejarSalida(juego, evento) or evento.type != pygame.KEYDOWN:
            return
        if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.__terminado:
                self.__alFinalizar(juego)
            else:
                self.__completar()

    def _finalizarCine(self, juego):
        if self.__grupo == "final":
            if self.__fade is None: self.__fade = 0.0
        else: self.__alFinalizar(juego)

    def actualizar(self, juego: Juego, dt: float) -> None:
        if self.__fade is not None:
            self.__fade += dt
            if self.__fade >= 1.0: self.__alFinalizar(juego)
            return
        if self.__cine is not None:
            self.__cine.update(dt)
            return
        self.__reloj += dt
        if self.__terminado:
            return
        total = len(self.__texto)
        self.__escritos = min(float(total), self.__escritos + dt * self.VELOCIDAD)
        nuevos = int(self.__escritos)
        if nuevos // self.CADA_TECLEO > self.__visibles // self.CADA_TECLEO \
                and self.__texto[nuevos - 1] != " ":
            juego.getAudio().reproducir("tecleo")
        self.__visibles = nuevos
        if nuevos >= total:
            self.__terminado = True

    def dibujar(self, juego: Juego, pantalla: pygame.Surface) -> None:
        if self.__cine is not None:
            self.__cine.draw(pantalla)
            if self.__fade is not None:
                velo = pygame.Surface(pantalla.get_size())
                velo.set_alpha(min(255, int(255*self.__fade)))
                pantalla.blit(velo, (0,0))
            return
        progreso = self.__visibles / len(self.__texto) if self.__conCarga else None
        juego.getInterfaz().dibujarNarrativa(
            pantalla, self.__titulo, self.__subtitulo, self.__texto,
            self.__visibles, self.__terminado, self.__reloj, progreso)

    def __completar(self) -> None:
        self.__escritos = float(len(self.__texto))
        self.__visibles = len(self.__texto)
        self.__terminado = True

    def estaTerminado(self) -> bool:
        return self.__terminado


# ----------------------------------------------------------------------
class EstadoJugando(EstadoJuego):
    def __init__(self):
        self.instrucciones = True

    def manejar_eventos(self, juego: Juego, evento: pygame.event.Event) -> None:
        if self._manejarSalida(juego, evento) or evento.type != pygame.KEYDOWN:
            return
        if self.instrucciones:
            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER): self.instrucciones = False
            return
        nivel = juego.getNivelActual()
        if evento.key == pygame.K_SPACE:
            if not nivel.construirBase():
                juego.getInterfaz().avisar("Necesitas 3 Nox y espacio libre para construir.")
        elif evento.key == pygame.K_f:
            nivel.ofrecerMineral()
        elif evento.key == pygame.K_p:
            juego.cambiarEstado(EstadoPausa(self))

    def actualizar(self, juego: Juego, dt: float) -> None:
        if self.instrucciones: return
        nivel = juego.getNivelActual()
        dx, dy = self.__leerMovimiento()
        nivel.moverExplorador(dx, dy)
        nivel.update(dt)
        juego.getInterfaz().avanzarMensajes(dt)
        explorador = nivel.getExplorador()
        if not explorador.estaViva():
            juego.cambiarEstado(EstadoGameOver())
        elif nivel.isCompletado():
            juego.sumarPuntaje(500 + explorador.getSalud() * 5)
            if hasattr(nivel, "bonificacionTiempo"):
                juego.sumarPuntaje(nivel.bonificacionTiempo())
            juego.registrarNivelCompletado()
            if juego.esUltimoNivel():
                juego.finalizarPartida()
                juego.cambiarEstado(EstadoNarrativa.epilogo())     # el epílogo lleva a EstadoVictoria
            else:
                juego.cambiarEstado(EstadoNivelCompleto())
        elif hasattr(nivel, "tiempoAgotado") and nivel.tiempoAgotado():
            juego.cambiarEstado(EstadoGameOver("Tiempo agotado"))

    @staticmethod
    def __leerMovimiento() -> Tuple[float, float]:
        teclas = pygame.key.get_pressed()
        dx = (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        dy = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP])
        return float(dx), float(dy)

    def dibujar(self, juego: Juego, pantalla: pygame.Surface) -> None:
        if self.instrucciones:
            juego.getInterfaz().dibujarInstrucciones(pantalla, juego.getIndiceNivel())
        else: self._dibujarEscena(juego, pantalla)


# ----------------------------------------------------------------------
class EstadoPausa(EstadoJuego):
    """Congela el nivel. Recuerda el estado anterior para reanudar exactamente donde quedó."""

    def __init__(self, anterior: EstadoJuego) -> None:
        self.__anterior: EstadoJuego = anterior

    def alEntrar(self, juego: Juego) -> None:
        juego.getAudio().reproducir("pausa")

    def manejar_eventos(self, juego: Juego, evento: pygame.event.Event) -> None:
        if self._manejarSalida(juego, evento) or evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_p:
            juego.getAudio().reproducir("pausa")
            juego.cambiarEstado(self.__anterior)

    def actualizar(self, juego: Juego, dt: float) -> None:
        pass            # el tiempo del nivel no avanza mientras está en pausa

    def dibujar(self, juego: Juego, pantalla: pygame.Surface) -> None:
        self.__anterior.dibujar(juego, pantalla)
        juego.getInterfaz().dibujarPausa(pantalla)


# ----------------------------------------------------------------------
class EstadoNivelCompleto(EstadoJuego):
    def manejar_eventos(self, juego: Juego, evento: pygame.event.Event) -> None:
        if self._manejarSalida(juego, evento) or evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_RETURN:
            # primero la conexión narrativa; al terminarla, la escena llama a juego.avanzarNivel()
            juego.cambiarEstado(EstadoNarrativa.entreNiveles(juego.getIndiceNivel()))

    def actualizar(self, juego: Juego, dt: float) -> None:
        juego.getInterfaz().avanzarMensajes(dt)

    def dibujar(self, juego: Juego, pantalla: pygame.Surface) -> None:
        self._dibujarEscena(juego, pantalla)
        juego.getInterfaz().dibujarOverlay(
            pantalla, "¡NIVEL COMPLETADO!", "ENTER para continuar la historia", (120, 255, 150),
            lineas=[f"{juego.getJugador()} · Puntaje: {juego.getPuntajeNivelActual()}"])


# ----------------------------------------------------------------------
class EstadoGameOver(EstadoJuego):
    def __init__(self, motivo="El explorador ha caído"):
        self.motivo = motivo

    def manejar_eventos(self, juego: Juego, evento: pygame.event.Event) -> None:
        if self._manejarSalida(juego, evento) or evento.type != pygame.KEYDOWN:
            return
        if evento.key == pygame.K_RETURN:
            juego.reintentarNivel()

    def actualizar(self, juego: Juego, dt: float) -> None:
        juego.getInterfaz().avanzarMensajes(dt)

    def dibujar(self, juego: Juego, pantalla: pygame.Surface) -> None:
        self._dibujarEscena(juego, pantalla)
        juego.getInterfaz().dibujarOverlay(
            pantalla, "MISIÓN FALLIDA", "ENTER para reintentar el nivel", (255, 110, 110),
            lineas=[self.motivo, f"{juego.getJugador()} · Puntaje: {juego.getPuntajeNivelActual()} · {juego.getUniversidad()}"],
            ranking=juego.getTop5())


# ----------------------------------------------------------------------
class EstadoVictoria(EstadoJuego):
    def __init__(self):
        self.reloj = 0.0
        self.resultados = False

    def manejar_eventos(self, juego, evento):
        if self._manejarSalida(juego, evento) or evento.type != pygame.KEYDOWN: return
        if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.resultados: juego.volverAlMenu()
            elif self.reloj >= 1.2: self.resultados = True

    def actualizar(self, juego, dt):
        self.reloj += dt

    def dibujar(self, juego, pantalla):
        interfaz = juego.getInterfaz()
        if self.resultados:
            interfaz.dibujarResultados(pantalla, juego.getJugador(), juego.getUniversidad(), juego.getPuntajeTotal(), juego.getTop5(), juego.getPuntajesNivel())
        else:
            interfaz.dibujarCelebracion(pantalla, self.reloj)
