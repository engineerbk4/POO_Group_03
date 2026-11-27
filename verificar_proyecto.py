"""Verificación automática de 'Misión en Marte' (sin abrir ventana ni usar la tarjeta de sonido).

Uso:   python verificar_proyecto.py

Comprueba:
  1. Carga y actualización polimórfica de los 3 niveles (+ las 3 tormentas)
  2. Transiciones del patrón State de Juego: Menú -> Jugando -> Pausa -> Game Over (-> Victoria)
  3. Patrón Observer (sujetos, observadores HUD / Logger / Audio)
  4. APIClient: en línea (simulado), fallos de red y respaldo offline
  5. RepositorioPuntajes: lectura/escritura JSON y manejo de errores
  6. Extras: audio seguro, clases abstractas y ausencia de isinstance() en el dominio
Código de salida 0 = todo correcto, 1 = hubo fallos.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import ast
import io
import json
import random
import sys
import tempfile
import traceback
import urllib.error
from pathlib import Path
from typing import Any, Callable, List
from unittest import mock

import pygame

from src import config
from src.entidades.entidad_juego import EntidadJuego
from src.estados_juego.estado_juego import (EstadoGameOver, EstadoJuego, EstadoJugando, EstadoNarrativa,
                                            EstadoMenu, EstadoNivelCompleto, EstadoPausa,
                                            EstadoVictoria)
from src.excepciones import APIError, ErrorMisionMarte, PersistenciaError
from src.juego import Juego
from src.niveles.defensa import NivelDefensa
from src.niveles.escape import NivelEscape
from src.niveles.nivel import Nivel
from src.niveles.supervivencia import NivelSupervivencia
from src.patrones.observer import (EventoDominio, Observador, ObservadorAudio, ObservadorHUD,
                                   ObservadorLogger, Sujeto)
from src.servicios.api_client import APIClient
from src.servicios.gestor_audio import GestorAudio
from src.servicios.repositorio_puntajes import RepositorioPuntajes
from src.tormentas.arena import TormentaArena
from src.tormentas.fabrica import TormentaFactory
from src.tormentas.meteoritos import TormentaMeteoritos
from src.tormentas.radiacion import TormentaRadiacion
from src.tormentas.tormenta import Tormenta
from src.vista.interfaz import InterfazJuego

RAIZ = Path(__file__).resolve().parent
DT = 1 / 60

pruebas: List[tuple] = []


def prueba(nombre: str):
    def registrar(funcion: Callable[[], None]) -> Callable[[], None]:
        pruebas.append((nombre, funcion))
        return funcion
    return registrar


def verificar(condicion: bool, mensaje: str) -> None:
    if not condicion:
        raise AssertionError(mensaje)


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def crearFabrica() -> TormentaFactory:
    fabrica = TormentaFactory()
    fabrica.registrarTormenta("radiacion", TormentaRadiacion)
    fabrica.registrarTormenta("meteoritos", TormentaMeteoritos)
    fabrica.registrarTormenta("arena", TormentaArena)
    return fabrica


def crearNiveles(fabrica: TormentaFactory) -> List[Nivel]:
    return [NivelSupervivencia(fabrica), NivelDefensa(fabrica), NivelEscape(fabrica)]


class Grabadora(Observador):
    def __init__(self) -> None:
        self.eventos: List[tuple] = []

    def actualizar(self, evento: str, datos: dict) -> None:
        self.eventos.append((evento, datos))

    def nombres(self) -> List[str]:
        return [e for e, _ in self.eventos]


class RespuestaFalsa:
    def __init__(self, contenido: bytes) -> None:
        self.__contenido = contenido
        self.cerrada = False

    def read(self) -> bytes:
        return self.__contenido

    def close(self) -> None:
        self.cerrada = True


def abridorQue(respuesta: Any = None, error: Exception = None, capturar: dict = None):
    def abridor(peticion, timeout=None):
        if capturar is not None:
            capturar["timeout"] = timeout
            capturar["url"] = peticion.full_url
        if error is not None:
            raise error
        return respuesta
    return abridor


def crearJuego(directorio: Path, api: APIClient = None):
    fabrica = crearFabrica()
    niveles = crearNiveles(fabrica)
    hud = ObservadorHUD()
    audio = GestorAudio()
    for nivel in niveles:
        nivel.suscribir(hud)
    repo = RepositorioPuntajes(directorio / "puntajes.json")
    api = api or APIClient(abridor=abridorQue(error=urllib.error.URLError("sin red")))
    juego = Juego(niveles, api, repo, InterfazJuego(hud), audio)
    return juego, niveles, repo


def pulsar(juego: Juego, tecla: int, mod: int = 0) -> None:
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=tecla, mod=mod, unicode="", scancode=0))
    juego.procesarEventos()


# ----------------------------------------------------------------------
# 1. Niveles
# ----------------------------------------------------------------------
@prueba("1. Los 3 niveles cargan, se actualizan polimórficamente y se dibujan")
def probarNiveles() -> None:
    random.seed(3)
    pantalla = pygame.display.set_mode((config.ANCHO, config.ALTO))
    fabrica = crearFabrica()
    verificar(sorted(fabrica.tiposDisponibles()) == ["arena", "meteoritos", "radiacion"],
              "la fábrica debe tener las 3 tormentas registradas")
    for nivel in crearNiveles(fabrica):
        nivel.reiniciar()
        verificar(nivel.getExplorador().estaViva(), "el explorador debe nacer vivo")
        for tipo in fabrica.tiposDisponibles():          # cada tormenta se lanza y se dibuja
            nivel._lanzarTormenta(tipo)
        explorador = nivel.getExplorador()
        for frame in range(900):                         # 15 s simulados
            nivel.moverExplorador(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))
            nivel.update(DT)
            if frame % 30 == 0:
                nivel.render(pantalla)
            explorador.curar(1)                          # evita morir y corta la simulación
        verificar(nivel.getTiempo() > 14, f"nivel {nivel.getNumero()}: el tiempo debe avanzar")
        nivel.render(pantalla)

    # Nivel 1: recolectar 10 de combustible => victoria
    n1 = NivelSupervivencia(fabrica)
    n1.reiniciar()
    n1._aliadosFormados = 2
    for _ in range(400):
        if n1.isCompletado():
            break
        objetivo = n1._minerales[0]
        n1.getExplorador().setPosicion(objetivo.getX(), objetivo.getY())
        n1.update(DT)
        n1.getExplorador().curar(100)
    verificar(n1.isCompletado(), "el nivel 1 debe completarse al recolectar 10 de combustible")

    # Nivel 3: 6 de combustible + llegar al cohete
    n3 = NivelEscape(fabrica)
    n3.reiniciar()
    n3.getExplorador().almacenar(NivelEscape.COMBUSTIBLE_NECESARIO)
    n3.getExplorador().setPosicion(config.ANCHO - 90, config.ALTO - 90)
    n3.update(DT)
    verificar(n3.isCompletado(), "el nivel 3 debe completarse con combustible junto al cohete")

    # La arena ralentiza sin dañar; sin la tormenta, la velocidad vuelve a la normal
    n = NivelSupervivencia(fabrica)
    n.reiniciar()
    n._lanzarTormenta("arena")
    n.update(DT)
    verificar(n.getExplorador().getFactorVelocidad() < 1.0, "la arena debe ralentizar al explorador")
    verificar(n.getExplorador().getSalud() == n.getExplorador().getSaludMaxima(),
              "la arena no debe dañar")
    for _ in range(600):
        n.update(DT)
    verificar(n.getExplorador().getFactorVelocidad() == 1.0, "la velocidad debe normalizarse al acabar")

    # Una fábrica sin 'arena' no rompe a los niveles (el ciclo ignora tipos no registrados)
    parcial = TormentaFactory()
    parcial.registrarTormenta("radiacion", TormentaRadiacion)
    n2 = NivelDefensa(parcial)
    n2.reiniciar()
    for _ in range(60 * 30):
        n2.update(DT)
        n2.getExplorador().curar(100)


# ----------------------------------------------------------------------
# 2. Estados de Juego
# ----------------------------------------------------------------------
@prueba("2. Transiciones de estado: Menú -> Jugando -> Pausa -> Jugando -> Game Over (-> Victoria)")
def probarEstados() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        juego, niveles, repo = crearJuego(Path(tmp))
        verificar(type(juego.getEstado()) is EstadoMenu, "debe arrancar en EstadoMenu")
        juego.actualizar(DT)
        juego.dibujar()

        for _ in range(4):
            pulsar(juego, pygame.K_RETURN)
        verificar(type(juego.getEstado()) is EstadoNarrativa, "Menú -> prólogo")
        pulsar(juego, pygame.K_ESCAPE)
        verificar(type(juego.getEstado()) is EstadoJugando, "Prólogo -> EstadoJugando")
        pulsar(juego, pygame.K_RETURN)
        nivel = juego.getNivelActual()
        for _ in range(30):
            juego.actualizar(DT)
            juego.dibujar()
        t0 = nivel.getTiempo()
        verificar(t0 > 0, "el nivel debe avanzar mientras se juega")

        pulsar(juego, pygame.K_p)
        verificar(type(juego.getEstado()) is EstadoPausa, "P -> EstadoPausa")
        for _ in range(30):
            juego.actualizar(DT)
            juego.dibujar()
        verificar(nivel.getTiempo() == t0, "en pausa el nivel NO debe avanzar")

        pulsar(juego, pygame.K_p)
        verificar(type(juego.getEstado()) is EstadoJugando, "P otra vez -> vuelve a EstadoJugando")
        juego.actualizar(DT)
        verificar(nivel.getTiempo() > t0, "al reanudar el nivel avanza de nuevo")

        # derrota
        juego.sumarPuntaje(123)
        nivel.getExplorador().recibirDano(10 ** 6)
        juego.actualizar(DT)
        verificar(type(juego.getEstado()) is EstadoGameOver, "explorador muerto -> EstadoGameOver")
        juego.dibujar()
        pulsar(juego, pygame.K_RETURN)
        verificar(type(juego.getEstado()) is EstadoJugando, "ENTER en Game Over reintenta el nivel")
        verificar(juego.getNivelActual().getExplorador().estaViva(), "el reintento reinicia al explorador")

        verificar(juego.getPuntajeTotal() == 0, "reintentar restaura puntaje")
        # nivel completo y victoria (recorriendo los 3 niveles)
        for indice in range(len(niveles)):
            pulsar(juego, pygame.K_RETURN)
            actual = juego.getNivelActual()
            verificar(juego.getPuntajeNivelActual() == 0, "puntaje local empieza en cero")
            actual.getExplorador().almacenar(NivelEscape.COMBUSTIBLE_NECESARIO)
            if indice == 0:
                actual.getExplorador().almacenar(10)
                actual._aliadosFormados = 2
            elif indice == 1:
                actual.getExplorador().almacenar(9)
                for x in (150, 350, 550):
                    actual.getExplorador().setPosicion(x, 250)
                    verificar(actual.construirBase(), "base separada")
                actual._aliadosFormados = 1
                actual._tiempo = 20
            else:
                actual.getExplorador().setPosicion(config.ANCHO - 90, config.ALTO - 90)
            juego.actualizar(DT)
            esUltimo = indice == len(niveles) - 1
            if esUltimo and isinstance(juego.getEstado(), EstadoNarrativa):
                pulsar(juego, pygame.K_ESCAPE)
                juego.actualizar(1.1)
            esperado = EstadoVictoria if esUltimo else EstadoNivelCompleto
            verificar(type(juego.getEstado()) is esperado,
                      f"nivel {indice + 1} completado -> {esperado.__name__}, está en {type(juego.getEstado()).__name__}")
            juego.dibujar()
            if esUltimo:
                juego.actualizar(1.3)
                pulsar(juego, pygame.K_RETURN)
                juego.dibujar()
                verificar(sum(juego.getPuntajesNivel()) == juego.getPuntajeTotal(), "desglose suma total")
            pulsar(juego, pygame.K_RETURN)
            if isinstance(juego.getEstado(), EstadoNarrativa):
                pulsar(juego, pygame.K_ESCAPE)
        verificar(type(juego.getEstado()) is EstadoMenu, "ENTER en Victoria vuelve al menú")
        verificar(juego.getPuntajeTotal() > 0, "completar niveles debe sumar puntaje")
        verificar(len(repo.top()) >= 1, "el puntaje final debe quedar guardado en el Top 5")

        # cambio de universidad con U
        pulsar(juego, pygame.K_RETURN)
        antes = juego.getUniversidad()
        pulsar(juego, pygame.K_u)
        verificar(juego.getUniversidad() != antes, "U debe cambiar la universidad representante")

        # ESC termina el juego
        pulsar(juego, pygame.K_ESCAPE)
        verificar(not juego.estaCorriendo(), "ESC debe terminar el juego")


# ----------------------------------------------------------------------
# 3. Observer
# ----------------------------------------------------------------------
@prueba("3. Patrón Observer: sujetos, suscripción y observadores concretos")
def probarObserver() -> None:
    # Sujeto básico
    sujeto = Sujeto()
    a, b = Grabadora(), Grabadora()
    sujeto.suscribir(a)
    sujeto.suscribir(a)                                  # duplicado ignorado
    sujeto.suscribir(b)
    sujeto.notificar("X", {"k": 1})
    verificar(len(a.eventos) == 1 and len(b.eventos) == 1, "cada observador recibe 1 notificación")
    sujeto.desuscribir(b)
    sujeto.notificar("Y")
    verificar(len(a.eventos) == 2 and len(b.eventos) == 1, "un observador desuscrito deja de recibir")

    # Explorador + Nivel (retransmisión)
    fabrica = crearFabrica()
    nivel = NivelSupervivencia(fabrica)
    grabadora = Grabadora()
    with tempfile.TemporaryDirectory() as tmp:
        rutaLog = Path(tmp) / "logs" / "partida.log"
        logger = ObservadorLogger(rutaLog)
        hud = ObservadorHUD()
        nivel.suscribir(grabadora)
        nivel.suscribir(logger)
        nivel.suscribir(hud)
        nivel.reiniciar()
        e = nivel.getExplorador()

        e.recibirDano(40)
        e.curar(10)
        verificar(EventoDominio.SALUD_CAMBIADA in grabadora.nombres(), "SALUD_CAMBIADA")
        ultimo = grabadora.eventos[-1][1]
        verificar(ultimo["delta"] == 10 and ultimo["salud"] == 70, "SALUD_CAMBIADA lleva delta y salud")

        mineral = nivel._minerales[0]
        e.setPosicion(mineral.getX(), mineral.getY())
        nivel.update(DT)
        verificar(EventoDominio.MINERAL_RECOLECTADO in grabadora.nombres(), "MINERAL_RECOLECTADO")

        e.almacenar(3)
        verificar(nivel.construirBase(), "con 3+ minerales se construye una base")
        verificar(EventoDominio.BASE_CONSTRUIDA in grabadora.nombres(), "BASE_CONSTRUIDA")

        marciano = nivel._marcianos[0]
        e.setPosicion(marciano.getX(), marciano.getY())
        e.almacenar(1)
        verificar(nivel.ofrecerMineral(), "se puede ofrecer un mineral a un marciano cercano")
        verificar(EventoDominio.MARCIANO_ALIADO in grabadora.nombres(), "MARCIANO_ALIADO")

        nivel.reiniciar()                                # el explorador nuevo sigue siendo observado
        grabadora.eventos.clear()
        nivel.getExplorador().recibirDano(20)
        verificar(grabadora.nombres() == [EventoDominio.SALUD_CAMBIADA],
                  "tras reiniciar, el nuevo explorador sigue notificando por el nivel")

        nivel.getExplorador().recibirDano(10 ** 6)
        nivel.update(DT)
        nivel.update(DT)
        verificar(grabadora.nombres().count(EventoDominio.JUGADOR_DERROTADO) == 1,
                  "JUGADOR_DERROTADO se notifica una sola vez")

        # NIVEL_COMPLETADO
        nivel.reiniciar()
        nivel.getExplorador().almacenar(10)
        nivel._aliadosFormados = 2
        nivel.update(DT)
        verificar(EventoDominio.NIVEL_COMPLETADO in grabadora.nombres(), "NIVEL_COMPLETADO")

        # ObservadorHUD: mensajes flotantes que caducan
        verificar(len(hud.getMensajes()) > 0, "el HUD debe acumular mensajes")
        hud.avanzar(10.0)
        verificar(len(hud.getMensajes()) == 0, "los mensajes del HUD caducan")

        # ObservadorLogger: archivo con marca de tiempo (sin ruido de curaciones pequeñas)
        verificar(rutaLog.exists(), "el logger debe crear logs/partida.log")
        lineas = rutaLog.read_text(encoding="utf-8").splitlines()
        verificar(any(EventoDominio.BASE_CONSTRUIDA in l for l in lineas), "el log contiene BASE_CONSTRUIDA")
        verificar(all(l[:4].isdigit() and l[4] == "-" for l in lineas), "cada línea del log lleva fecha")
        logger.actualizar(EventoDominio.SALUD_CAMBIADA, {"delta": 1})
        verificar(len(rutaLog.read_text(encoding="utf-8").splitlines()) == len(lineas),
                  "los cambios de salud diminutos no ensucian el log")

    # ObservadorLogger tolera rutas sin permisos
    logger_malo = ObservadorLogger(Path("/proc/no_se_puede/partida.log"))
    with mock.patch("sys.stdout", new_callable=io.StringIO):
        logger_malo.actualizar(EventoDominio.BASE_CONSTRUIDA, {})

    # ObservadorAudio traduce eventos a sonidos
    sonidos: List[str] = []

    class AudioFalso:
        def reproducir(self, nombre: str) -> None:
            sonidos.append(nombre)

    oa = ObservadorAudio(AudioFalso(), pausaDano=0.0)
    for ev, datos in [(EventoDominio.MINERAL_RECOLECTADO, {}), (EventoDominio.BASE_CONSTRUIDA, {}),
                      (EventoDominio.MARCIANO_ALIADO, {}), (EventoDominio.NIVEL_COMPLETADO, {}),
                      (EventoDominio.JUGADOR_DERROTADO, {}),
                      (EventoDominio.SALUD_CAMBIADA, {"delta": -5}),
                      (EventoDominio.SALUD_CAMBIADA, {"delta": 5})]:
        oa.actualizar(ev, datos)
    verificar(sonidos == ["mineral", "base", "aliado", "nivel", "gameover", "dano"],
              f"sonidos incorrectos: {sonidos}")


# ----------------------------------------------------------------------
# 4. APIClient
# ----------------------------------------------------------------------
@prueba("4. APIClient: respuesta correcta, fallos de red y respaldo offline")
def probarApi() -> None:
    cuerpo = json.dumps([
        {"name": "Universidad Nacional de Ingeniería", "country": "Peru"},
        {"name": "Universidad Peruana Cayetano Heredia", "country": "Peru"},
        {"name": "Universidad Peruana Cayetano Heredia", "country": "Peru"},   # duplicada
        {"name": "Universidad Zeta", "country": "Peru"},
        {"sin_nombre": True},
    ]).encode("utf-8")

    # --- en línea (red simulada, determinista) ---
    capturado: dict = {}
    respuesta = RespuestaFalsa(cuerpo)
    api = APIClient(abridor=abridorQue(respuesta, capturar=capturado))
    verificar(api.estado() == APIClient.CARGANDO, "estado inicial CARGANDO")
    lista = api.cargar()
    verificar(api.estado() == APIClient.EN_LINEA, "con respuesta válida queda EN_LINEA")
    verificar(lista[0] == "Universidad Peruana Cayetano Heredia", "la UPCH va primero")
    verificar(lista.count("Universidad Peruana Cayetano Heredia") == 1, "sin duplicados")
    verificar("Universidad Zeta" in lista and len(lista) == 3, "incluye las demás universidades")
    verificar(capturado["timeout"] == 3.0, "timeout de 3 segundos")
    verificar(capturado["url"] == "http://universities.hipolabs.com/search?country=Peru", "URL de la API")
    verificar(respuesta.cerrada, "la respuesta debe cerrarse (finally)")

    # --- fallos: cada uno debe convertirse en APIError y activar el respaldo ---
    fallos = {
        "URLError": urllib.error.URLError("sin internet"),
        "HTTPError": urllib.error.HTTPError("http://x", 503, "no disponible", None, None),
        "TimeoutError": TimeoutError("timed out"),
        "OSError": ConnectionResetError("reset"),
    }
    for nombre, error in fallos.items():
        api = APIClient(abridor=abridorQue(error=error))
        try:
            api.consultarUniversidades()
        except APIError:
            pass
        else:
            raise AssertionError(f"{nombre} debía lanzar APIError")
        lista = api.cargar()                              # versión segura: nunca lanza
        verificar(api.estado() == APIClient.OFFLINE, f"{nombre}: debe quedar OFFLINE")
        verificar(lista[0] == "Universidad Peruana Cayetano Heredia", f"{nombre}: respaldo con UPCH")
        verificar(api.ultimoError() != "", f"{nombre}: guarda el motivo del fallo")

    for nombre, contenido in {"JSON inválido": b"<html>no es json", "no es lista": b'{"a": 1}',
                              "lista vacía": b"[]", "bytes inválidos": b"\xff\xfe\x00"}.items():
        api = APIClient(abridor=abridorQue(RespuestaFalsa(contenido)))
        try:
            api.consultarUniversidades()
        except APIError:
            pass
        else:
            raise AssertionError(f"{nombre} debía lanzar APIError")
        api.cargar()
        verificar(api.estado() == APIClient.OFFLINE, f"{nombre}: debe quedar OFFLINE")

    # --- carga asíncrona: no bloquea y termina ---
    api = APIClient(abridor=abridorQue(RespuestaFalsa(cuerpo)))
    api.iniciarCargaAsincrona()
    api.esperarCarga(5)
    verificar(api.estado() == APIClient.EN_LINEA, "la carga asíncrona termina EN_LINEA")

    # --- red real (informativo: sin internet debe degradar a offline sin fallar) ---
    real = APIClient()
    real.cargar()
    print(f"      [info] API real -> {real.estado()}"
          + (f" ({real.ultimoError()})" if real.ultimoError() else f" ({len(real.universidades())} universidades)"))
    verificar(real.estado() in (APIClient.EN_LINEA, APIClient.OFFLINE), "la API real nunca bloquea el juego")
    verificar(real.universidades()[0] == "Universidad Peruana Cayetano Heredia", "UPCH siempre disponible")


# ----------------------------------------------------------------------
# 5. Repositorio JSON
# ----------------------------------------------------------------------
@prueba("5. RepositorioPuntajes: lectura/escritura JSON y manejo de errores")
def probarRepositorio() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "datos" / "high_scores.json"
        repo = RepositorioPuntajes(ruta)
        verificar(repo.cargar() == [], "FileNotFoundError -> lista vacía")
        for puntaje in (300, 1200, 50, 900, 700, 1500, 20):
            repo.registrar(puntaje, "Universidad Peruana Cayetano Heredia", "Peru")
        top = repo.top()
        verificar([r.puntaje for r in top] == [1500, 1200, 900, 700, 300], f"Top 5 ordenado: {top}")
        verificar(repo.mejorPuntaje() == 1500, "mejor puntaje")
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        verificar(len(datos) == 5 and datos[0]["pais"] == "Peru", "el archivo JSON es válido y de 5 entradas")
        verificar(RepositorioPuntajes(ruta).top() == top, "los datos persisten entre instancias")

        # reemplazo del registro de la misma partida (sin duplicados)
        r1 = repo.registrar(2000, "UNI", "Peru")
        r2 = repo.registrar(2500, "UNI", "Peru", reemplaza=r1)
        verificar(sum(1 for r in repo.top() if r.universidad == "UNI") == 1, "reemplaza sin duplicar")
        verificar(repo.top()[0] == r2, "queda el puntaje más alto")

        # JSON corrupto -> se respalda y se continúa
        ruta.write_text("{ esto no es json", encoding="utf-8")
        verificar(repo.cargar() == [], "JSONDecodeError -> lista vacía")
        verificar(ruta.with_suffix(".corrupto.json").exists(), "el archivo corrupto se respalda")
        repo.registrar(10, "UNI", "Peru")
        verificar(len(repo.top()) == 1, "se puede seguir guardando tras un archivo corrupto")

        # entradas dañadas se descartan
        ruta.write_text('[{"puntaje": 5}, {"puntaje": 9, "universidad": "U", "pais": "Peru", "fecha": "x"}]',
                        encoding="utf-8")
        verificar(len(repo.cargar()) == 1, "las entradas dañadas se ignoran")

        # PermissionError
        with mock.patch("builtins.open", side_effect=PermissionError("denegado")):
            for accion in (repo.cargar, lambda: repo.registrar(1, "U", "Peru")):
                try:
                    accion()
                except PersistenciaError:
                    pass
                else:
                    raise AssertionError("PermissionError debe convertirse en PersistenciaError")

        # Juego sigue funcionando aunque el disco falle
        juego, _, _ = crearJuego(Path(tmp))
        juego.sumarPuntaje(100)
        with mock.patch("builtins.open", side_effect=PermissionError("denegado")), \
                mock.patch("sys.stdout", new_callable=io.StringIO):
            juego.finalizarPartida()
    try:
        RepositorioPuntajes(Path("x"), maximo=0)
    except ValueError:
        pass
    else:
        raise AssertionError("maximo=0 debe rechazarse")

    # el archivo real del proyecto existe y es JSON válido
    real = RAIZ / "data" / "high_scores.json"
    verificar(isinstance(json.loads(real.read_text(encoding="utf-8")), list), "data/high_scores.json válido")


# ----------------------------------------------------------------------
# 6. Extras de calidad
# ----------------------------------------------------------------------
@prueba("6. Audio seguro, clases abstractas y dominio sin isinstance()")
def probarExtras() -> None:
    audio = GestorAudio()
    print(f"      [info] audio disponible: {audio.estaDisponible()} -> {audio.nombres()}")
    for nombre in ("mineral", "base", "aliado", "dano", "pausa", "nivel", "gameover", "no_existe"):
        audio.reproducir(nombre)
    if audio.estaDisponible():
        verificar(len(audio.nombres()) == 7, "deben existir los 7 efectos")

    # sin tarjeta de audio: no explota
    with mock.patch("pygame.mixer.get_init", return_value=None), \
            mock.patch("pygame.mixer.init", side_effect=pygame.error("sin dispositivo")), \
            mock.patch("sys.stdout", new_callable=io.StringIO):
        mudo = GestorAudio()
    verificar(not mudo.estaDisponible(), "sin mezclador queda silencioso")
    mudo.reproducir("mineral")

    for abstracta in (EntidadJuego, EstadoJuego, Tormenta, Nivel, Observador):
        try:
            abstracta()                                  # type: ignore[abstract]
        except TypeError:
            pass
        else:
            raise AssertionError(f"{abstracta.__name__} debe ser abstracta")

    verificar(issubclass(APIError, ErrorMisionMarte) and issubclass(PersistenciaError, ErrorMisionMarte)
              and issubclass(ErrorMisionMarte, Exception), "jerarquía de excepciones")

    # el dominio (entidades, niveles, tormentas, estados) no usa isinstance()
    ofensores = []
    for carpeta in ("entidades", "niveles", "tormentas", "estados_juego"):
        for archivo in (RAIZ / "src" / carpeta).glob("*.py"):
            arbol = ast.parse(archivo.read_text(encoding="utf-8"))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Call) and getattr(nodo.func, "id", "") == "isinstance":
                    ofensores.append(f"{archivo.name}:{nodo.lineno}")
    verificar(not ofensores, f"isinstance() en el dominio: {ofensores}")

    # Open/Closed: una tormenta nueva se registra sin tocar la fábrica
    class TormentaPrueba(TormentaArena):
        pass

    fabrica = TormentaFactory()
    fabrica.registrarTormenta("prueba", TormentaPrueba)
    verificar(isinstance(fabrica.crearTormenta("prueba"), Tormenta), "la fábrica crea tormentas registradas")
    try:
        fabrica.crearTormenta("inexistente")
    except KeyError:
        pass
    else:
        raise AssertionError("tipo no registrado debe lanzar KeyError")


# ----------------------------------------------------------------------
def main() -> int:
    pygame.init()
    pygame.display.set_mode((config.ANCHO, config.ALTO))
    fallos = 0
    for nombre, funcion in pruebas:
        try:
            funcion()
        except Exception:
            fallos += 1
            print(f"[FALLA] {nombre}")
            traceback.print_exc()
        else:
            print(f"[ OK  ] {nombre}")
    pygame.quit()
    total = len(pruebas)
    print(f"\n{total - fallos}/{total} pruebas correctas")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
