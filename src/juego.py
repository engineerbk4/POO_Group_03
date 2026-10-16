"""Clase Juego: controla el Game Loop, las fases, el HUD y el puntaje."""
from __future__ import annotations

import random
from typing import List, Tuple

import pygame

from src import config
from src.niveles import Nivel


class Juego:
    def __init__(self, niveles: List[Nivel]) -> None:
        if not niveles:
            raise ValueError("el juego necesita al menos un nivel")
        pygame.init()
        self.__pantalla: pygame.Surface = pygame.display.set_mode((config.ANCHO, config.ALTO))
        pygame.display.set_caption(config.TITULO)
        self.__reloj: pygame.time.Clock = pygame.time.Clock()
        self.__fuenteGrande = pygame.font.Font(None, 72)
        self.__fuente = pygame.font.Font(None, 30)
        self.__fuentePeque = pygame.font.Font(None, 23)
        # AGREGACIÓN: los niveles se inyectan desde fuera y tienen vida propia
        self.__niveles: List[Nivel] = niveles
        self.__indiceNivel: int = 0
        self.__nivelActual: Nivel = niveles[0]
        self.__puntajeTotal: int = 0
        self.__highScore: int = 0
        self.__fase: str = "MENU"
        self.__corriendo: bool = True
        self.__fondo: pygame.Surface = self.__crearFondo()

    # ------------------------------------------------------------------
    def iniciar(self) -> None:
        self.__puntajeTotal = 0
        self.__indiceNivel = 0
        self.__nivelActual = self.__niveles[0]
        self.__nivelActual.reiniciar()
        self.__fase = "JUGANDO"

    def registrarHighScore(self) -> None:
        """Por ahora local; luego se delegará en APIClient."""
        self.__highScore = max(self.__highScore, self.__puntajeTotal)

    def gameLoop(self) -> None:
        while self.__corriendo:
            dt = min(self.__reloj.tick(config.FPS) / 1000.0, 0.05)
            self.__procesarEventos()
            self.__actualizar(dt)
            self.__dibujar()
        pygame.quit()

    # ------------------------------------------------------------------
    def __procesarEventos(self) -> None:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.__corriendo = False
            elif evento.type == pygame.KEYDOWN:
                self.__alPresionarTecla(evento.key)

    def __alPresionarTecla(self, tecla: int) -> None:
        if tecla == pygame.K_ESCAPE:
            self.__corriendo = False
        elif self.__fase == "MENU" and tecla == pygame.K_RETURN:
            self.iniciar()
        elif self.__fase == "JUGANDO":
            if tecla == pygame.K_SPACE:
                self.__nivelActual.construirBase()
            elif tecla == pygame.K_f:
                self.__nivelActual.ofrecerMineral()
        elif self.__fase == "NIVEL_COMPLETO" and tecla == pygame.K_RETURN:
            self.__indiceNivel += 1
            self.__nivelActual = self.__niveles[self.__indiceNivel]
            self.__nivelActual.reiniciar()
            self.__fase = "JUGANDO"
        elif self.__fase == "GAME_OVER" and tecla == pygame.K_RETURN:
            self.__nivelActual.reiniciar()
            self.__fase = "JUGANDO"
        elif self.__fase == "FIN" and tecla == pygame.K_RETURN:
            self.__fase = "MENU"

    def __leerMovimiento(self) -> Tuple[float, float]:
        teclas = pygame.key.get_pressed()
        dx = (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT])
        dy = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP])
        return float(dx), float(dy)

    def __actualizar(self, dt: float) -> None:
        if self.__fase != "JUGANDO":
            return
        dx, dy = self.__leerMovimiento()
        self.__nivelActual.moverExplorador(dx, dy)
        self.__nivelActual.update(dt)
        explorador = self.__nivelActual.getExplorador()
        if not explorador.estaViva():
            self.registrarHighScore()
            self.__fase = "GAME_OVER"
        elif self.__nivelActual.isCompletado():
            self.__puntajeTotal += 500 + explorador.getSalud() * 5
            self.registrarHighScore()
            ultimo = self.__indiceNivel == len(self.__niveles) - 1
            self.__fase = "FIN" if ultimo else "NIVEL_COMPLETO"

    # ------------------------------------------------------------------
    def __dibujar(self) -> None:
        self.__pantalla.blit(self.__fondo, (0, 0))
        if self.__fase == "MENU":
            self.__dibujarMenu()
        else:
            self.__nivelActual.render(self.__pantalla)
            self.__dibujarHUD()
            if self.__fase == "NIVEL_COMPLETO":
                self.__dibujarOverlay("¡NIVEL COMPLETADO!", "ENTER para el siguiente nivel", (120, 255, 150))
            elif self.__fase == "GAME_OVER":
                self.__dibujarOverlay("MISIÓN FALLIDA", "ENTER para reintentar el nivel", (255, 110, 110))
            elif self.__fase == "FIN":
                self.__dibujarOverlay("¡ESCAPASTE DE MARTE!", f"Puntaje final: {self.__puntajeTotal} · ENTER = menú", (255, 230, 120))
        pygame.display.flip()

    def __texto(self, texto: str, fuente: pygame.font.Font, color: Tuple[int, int, int],
                centro: Tuple[int, int]) -> None:
        sombra = fuente.render(texto, True, (0, 0, 0))
        img = fuente.render(texto, True, color)
        self.__pantalla.blit(sombra, sombra.get_rect(center=(centro[0] + 2, centro[1] + 2)))
        self.__pantalla.blit(img, img.get_rect(center=centro))

    def __dibujarMenu(self) -> None:
        cx = config.ANCHO // 2
        self.__texto("MISIÓN EN MARTE", self.__fuenteGrande, (255, 220, 120), (cx, 130))
        lineas = [
            "Recolecta combustible, sobrevive a las tormentas y escapa del planeta.",
            "",
            "WASD / Flechas  →  mover al explorador",
            "ESPACIO  →  construir base (cuesta 3 minerales; cura y protege)",
            "F  →  dar 1 mineral a un marciano asustado para volverlo aliado",
            "ESC  →  salir",
            "",
            "Cuidado: radiación (zona verde) y meteoritos (aros rojos).",
        ]
        for i, linea in enumerate(lineas):
            self.__texto(linea, self.__fuente, (255, 255, 255), (cx, 230 + i * 34))
        self.__texto("Presiona ENTER para comenzar", self.__fuente, (120, 255, 150), (cx, 560))
        if self.__highScore:
            self.__texto(f"Mejor puntaje: {self.__highScore}", self.__fuentePeque, (255, 230, 120), (cx, 595))

    def __dibujarHUD(self) -> None:
        nivel = self.__nivelActual
        explorador = nivel.getExplorador()
        pygame.draw.rect(self.__pantalla, (20, 14, 18), (0, 0, config.ANCHO, config.HUD_ALTO))
        self.__texto(f"Nivel {nivel.getNumero()}", self.__fuente, (255, 255, 255), (50, 15))
        # barra de salud
        pygame.draw.rect(self.__pantalla, (90, 20, 20), (100, 7, 170, 16))
        ancho = int(170 * explorador.getSalud() / explorador.getSaludMaxima())
        pygame.draw.rect(self.__pantalla, (60, 220, 100), (100, 7, ancho, 16))
        pygame.draw.rect(self.__pantalla, (255, 255, 255), (100, 7, 170, 16), 2)
        self.__texto(f"Minerales: {explorador.getInventarioMinerales()}", self.__fuente,
                     (110, 240, 225), (370, 15))
        self.__texto(f"Puntaje: {self.__puntajeTotal}", self.__fuente, (255, 230, 120), (config.ANCHO - 120, 15))
        self.__texto(nivel.descripcionObjetivo(), self.__fuentePeque, (255, 255, 255),
                     (config.ANCHO // 2, 38))

    def __dibujarOverlay(self, titulo: str, subtitulo: str, color: Tuple[int, int, int]) -> None:
        velo = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        velo.fill((0, 0, 0, 150))
        self.__pantalla.blit(velo, (0, 0))
        self.__texto(titulo, self.__fuenteGrande, color, (config.ANCHO // 2, config.ALTO // 2 - 30))
        self.__texto(subtitulo, self.__fuente, (255, 255, 255), (config.ANCHO // 2, config.ALTO // 2 + 30))

    def __crearFondo(self) -> pygame.Surface:
        sup = pygame.Surface((config.ANCHO, config.ALTO))
        sup.fill((150, 72, 45))
        rng = random.Random(7)
        for _ in range(55):
            cx, cy, r = rng.randint(0, config.ANCHO), rng.randint(0, config.ALTO), rng.randint(12, 55)
            pygame.draw.circle(sup, (138, 64, 39), (cx, cy), r)
            pygame.draw.circle(sup, (122, 55, 33), (cx, cy), r, 3)
        for _ in range(260):
            pygame.draw.circle(sup, (170, 92, 60), (rng.randint(0, config.ANCHO), rng.randint(0, config.ALTO)), rng.randint(1, 3))
        return sup
