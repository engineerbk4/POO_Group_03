"""Clase Juego: coordina el Game Loop y delega todo lo demás.

Responsabilidad única (SRP): ejecutar el ciclo eventos -> actualizar -> dibujar
y mantener la partida en curso (nivel actual, puntaje y Nombre del Piloto). Todo
lo demás se delega en colaboradores especializados que recibe por inyección de
dependencias:

* ``EstadoJuego``       -> flujo del juego (patrón State: menú, narrativa, jugando, pausa...)
* ``InterfazJuego``     -> dibujo de fondo, HUD, menús, narrativa y ranking
* ``APIClient``         -> comunicación HTTP
* ``RepositorioPuntajes`` -> persistencia JSON del Top 5
* ``GestorAudio``       -> efectos de sonido

Relaciones UML: AGREGACIÓN ``Juego o-- Nivel`` (los niveles llegan desde
``main.py`` y tienen vida propia) y ASOCIACIÓN con los servicios inyectados.
"""
from __future__ import annotations

from typing import List, Optional

import pygame

from src import config
from src.estados_juego.estado_juego import (EstadoJuego, EstadoJugando,
                                            EstadoMenu, EstadoNarrativa)
from src.excepciones import PersistenciaError
from src.niveles.nivel import Nivel
from src.patrones.observer import Observador, EventoDominio
from src.servicios.api_client import APIClient
from src.servicios.gestor_audio import GestorAudio
from src.servicios.repositorio_puntajes import (JUGADOR_MAX_CARACTERES,
                                                JUGADOR_POR_DEFECTO,
                                                RegistroPuntaje,
                                                RepositorioPuntajes,
                                                normalizarJugador)
from src.vista.interfaz import InterfazJuego


class _ObservadorPuntaje(Observador):
    def __init__(self, juego):
        self.juego = juego

    def actualizar(self, evento, datos):
        self.juego.actualizarEventoPuntaje(evento, datos)


class Juego:
    def __init__(self, niveles: List[Nivel], apiClient: APIClient,
                 repositorio: RepositorioPuntajes, interfaz: InterfazJuego,
                 audio: GestorAudio) -> None:
        if not niveles:
            raise ValueError("el juego necesita al menos un nivel")
        pygame.init()
        self.__ventana = pygame.display.set_mode((config.ANCHO, config.ALTO), pygame.RESIZABLE)
        self.__pantalla = pygame.Surface((config.ANCHO, config.ALTO)).convert()
        self.__pantallaCompleta = False
        self.__tamanoVentana = (config.ANCHO, config.ALTO)
        pygame.display.set_caption(config.TITULO)
        self.__reloj: pygame.time.Clock = pygame.time.Clock()
        # AGREGACIÓN: los niveles se inyectan desde fuera y tienen vida propia
        self.__niveles: List[Nivel] = niveles
        # servicios inyectados (bajo acoplamiento: Juego solo conoce sus interfaces públicas)
        self.__api: APIClient = apiClient
        self.__repositorio: RepositorioPuntajes = repositorio
        self.__interfaz: InterfazJuego = interfaz
        self.__audio: GestorAudio = audio
        # partida en curso
        self.__indiceNivel: int = 0
        self.__puntajeTotal: int = 0
        self.__puntajesNivel = [0] * len(niveles)
        self.__puntajeInicioNivel = 0
        self.__jugador: str = JUGADOR_POR_DEFECTO
        self.__universidad: str = config.UNIVERSIDAD_POR_DEFECTO
        self.__registroPartida: Optional[RegistroPuntaje] = None
        self.__top5: List[RegistroPuntaje] = []
        self.__corriendo: bool = True
        # contexto del patrón State
        self.__estado: EstadoJuego = EstadoMenu()
        self.__refrescarTop5()
        self.__estado.alEntrar(self)
        self.__actualizarMusica()
        for nivel in self.__niveles:
            nivel.suscribir(_ObservadorPuntaje(self))

    # ------------------------------------------------------------------
    # Game Loop
    # ------------------------------------------------------------------
    def gameLoop(self) -> None:
        while self.__corriendo:
            dt = min(self.__reloj.tick(config.FPS) / 1000.0, 0.05)
            self.procesarEventos()
            self.actualizar(dt)
            self.dibujar()
        pygame.quit()

    def procesarEventos(self) -> None:
        for evento in pygame.event.get():
            if evento.type == pygame.KEYDOWN and (evento.key == pygame.K_F11 or (evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and getattr(evento, "mod", 0) & pygame.KMOD_ALT)):
                self.alternarPantallaCompleta()
                continue
            self.__estado.manejar_eventos(self, evento)

    def actualizar(self, dt: float) -> None:
        self.__estado.actualizar(self, dt)

    def dibujar(self) -> None:
        self.__estado.dibujar(self, self.__pantalla)
        ventana = pygame.display.get_surface()
        w, h = ventana.get_size()
        escala = min(w / config.ANCHO, h / config.ALTO)
        tam = (max(1, int(config.ANCHO * escala)), max(1, int(config.ALTO * escala)))
        ventana.fill((8, 7, 16))
        imagen = self.__pantalla if tam == self.__pantalla.get_size() else pygame.transform.scale(self.__pantalla, tam)
        ventana.blit(imagen, ((w-tam[0])//2, (h-tam[1])//2))
        pygame.display.flip()

    def alternarPantallaCompleta(self):
        try:
            if self.__pantallaCompleta:
                self.__ventana = pygame.display.set_mode(self.__tamanoVentana, pygame.RESIZABLE)
            else:
                self.__tamanoVentana = pygame.display.get_surface().get_size()
                self.__ventana = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.__pantallaCompleta = not self.__pantallaCompleta
        except pygame.error as error:
            print(f"[pantalla] {error}")

    def terminar(self) -> None:
        self.__corriendo = False

    def estaCorriendo(self) -> bool:
        return self.__corriendo

    # ------------------------------------------------------------------
    # Patrón State: transición entre estados
    # ------------------------------------------------------------------
    def cambiarEstado(self, nuevo: EstadoJuego) -> None:
        self.__estado.alSalir(self)
        self.__estado = nuevo
        nuevo.alEntrar(self)
        self.__actualizarMusica()

    def __actualizarMusica(self) -> None:
        reproducir = getattr(self.__audio, "musica", None)
        if reproducir is None:
            return
        estado = type(self.__estado).__name__
        pista = {"EstadoMenu": "menu", "EstadoNarrativa": "historia",
                 "EstadoVictoria": "victoria", "EstadoGameOver": "derrota",
                 "EstadoNivelCompleto": "victoria"}.get(estado, f"nivel{self.__indiceNivel + 1}")
        reproducir(pista, 0.09 if estado == "EstadoPausa" else 0.24)

    def getEstado(self) -> EstadoJuego:
        return self.__estado

    # ------------------------------------------------------------------
    # Flujo de la partida (lo invocan los estados)
    # ------------------------------------------------------------------
    def iniciarPartida(self) -> None:
        """Reinicia la partida y abre el prólogo; al terminarlo, la narrativa llama a comenzarNivelActual()."""
        self.__puntajeTotal = 0
        self.__puntajesNivel = [0] * len(self.__niveles)
        self.__puntajeInicioNivel = 0
        self.__indiceNivel = 0
        self.__registroPartida = None
        self.cambiarEstado(EstadoNarrativa.prologo())

    def comenzarNivelActual(self) -> None:
        self.__comenzarNivel()

    def avanzarNivel(self) -> None:
        self.__indiceNivel += 1
        self.__comenzarNivel()

    def reintentarNivel(self) -> None:
        self.__puntajeTotal = self.__puntajeInicioNivel
        self.__puntajesNivel[self.__indiceNivel] = 0
        self.__comenzarNivel()

    def volverAlMenu(self) -> None:
        self.cambiarEstado(EstadoMenu())

    def __comenzarNivel(self) -> None:
        self.__puntajeInicioNivel = self.__puntajeTotal
        self.getNivelActual().reiniciar()
        self.__interfaz.limpiarMensajes()
        self.cambiarEstado(EstadoJugando())

    def actualizarEventoPuntaje(self, evento, datos):
        puntos = {EventoDominio.MINERAL_RECOLECTADO: 20 * datos.get("valor", 0),
                  EventoDominio.BASE_CONSTRUIDA: 100,
                  EventoDominio.MARCIANO_ALIADO: 100}.get(evento, 0)
        if puntos and datos.get("nivel") == self.getNivelActual().getNumero():
            self.sumarPuntaje(puntos)
            self.__interfaz.avisar(f"+{puntos} puntos")

    def sumarPuntaje(self, puntos: int) -> None:
        self.__puntajeTotal += max(0, puntos)

    def registrarNivelCompletado(self) -> None:
        self.__puntajesNivel[self.__indiceNivel] = self.__puntajeTotal - self.__puntajeInicioNivel

    def getPuntajesNivel(self) -> List[int]:
        return list(self.__puntajesNivel)

    def esUltimoNivel(self) -> bool:
        return self.__indiceNivel == len(self.__niveles) - 1

    def finalizarPartida(self) -> None:
        """Guarda el puntaje en el Top 5. Un fallo de disco nunca interrumpe el juego."""
        if self.__puntajeTotal > 0:
            try:
                self.__registroPartida = self.__repositorio.registrar(
                    self.__puntajeTotal, self.__universidad, config.PAIS,
                    self.__registroPartida, jugador=self.__jugador)
            except PersistenciaError as error:
                print(f"[puntajes] no se pudo guardar el puntaje: {error}")
        self.__refrescarTop5()

    def __refrescarTop5(self) -> None:
        try:
            self.__top5 = self.__repositorio.top()
        except PersistenciaError as error:
            print(f"[puntajes] no se pudo leer el ranking: {error}")
            self.__top5 = []

    # ------------------------------------------------------------------
    # Nombre del piloto
    # ------------------------------------------------------------------
    def setJugador(self, nombre: str) -> None:
        """Valida el nombre (letras/números/espacios, máx. 14); si queda vacío usa "Explorador"."""
        self.__jugador = normalizarJugador(nombre)

    def getJugador(self) -> str:
        return self.__jugador

    @staticmethod
    def getNombrePorDefecto() -> str:
        return JUGADOR_POR_DEFECTO

    @staticmethod
    def getLongitudMaxNombre() -> int:
        return JUGADOR_MAX_CARACTERES

    # ------------------------------------------------------------------
    # Universidad representante (datos que vienen de APIClient)
    # ------------------------------------------------------------------
    def alternarUniversidad(self, paso: int = 1) -> None:
        lista = self.__api.universidades()
        if not lista:
            return
        try:
            indice = lista.index(self.__universidad)
        except ValueError:
            indice = -1 if paso > 0 else 0
        self.__universidad = lista[(indice + paso) % len(lista)]

    # ------------------------------------------------------------------
    # Consultas para los estados y la vista
    # ------------------------------------------------------------------
    def getNivelActual(self) -> Nivel:
        return self.__niveles[self.__indiceNivel]

    def getIndiceNivel(self) -> int:
        return self.__indiceNivel

    def getPuntajeNivelActual(self) -> int:
        return self.__puntajeTotal - self.__puntajeInicioNivel

    def getPuntajeTotal(self) -> int:
        return self.__puntajeTotal

    def getUniversidad(self) -> str:
        return self.__universidad

    def getUniversidades(self) -> List[str]:
        return self.__api.universidades()

    def getEstadoApi(self) -> str:
        return self.__api.estado()

    def getTop5(self) -> List[RegistroPuntaje]:
        return list(self.__top5)

    def getInterfaz(self) -> InterfazJuego:
        return self.__interfaz

    def getAudio(self) -> GestorAudio:
        return self.__audio
