"""InterfazJuego: toda la presentación (fondo, HUD, menú, pausa, overlays, ranking y narrativa).

Responsabilidad única: dibujar. No decide reglas ni cambia estados; recibe los
datos que necesita por parámetro y lee los mensajes flotantes del
``ObservadorHUD`` (que se llena por eventos, sin *polling* sobre el juego).
"""
from __future__ import annotations

import random
import math
from typing import List, Optional, Sequence, Tuple

import pygame

from src import config
from src.niveles.nivel import Nivel
from src.patrones.observer import ObservadorHUD
from src.servicios.api_client import APIClient
from src.servicios.repositorio_puntajes import RegistroPuntaje

Color = Tuple[int, int, int]


class InterfazJuego:
    def __init__(self, observadorHUD: ObservadorHUD) -> None:
        pygame.font.init()
        self.__fuenteGrande = pygame.font.Font(None, 72)
        self.__fuenteMedia = pygame.font.Font(None, 30)
        self.__fuente = pygame.font.Font(None, 26)
        self.__fuentePeque = pygame.font.Font(None, 23)
        self.__hud: ObservadorHUD = observadorHUD
        self.__fondo: pygame.Surface = self.__crearFondo()
        # recursos de la pantalla narrativa (se crean una sola vez)
        self.__fondoNarrativa: pygame.Surface = self.__crearFondoNarrativa()
        self.__panelRect: pygame.Rect = pygame.Rect(60, 150, config.ANCHO - 120,
                                                    max(120, config.ALTO - 150 - 140))
        self.__panelSuperficie: pygame.Surface = pygame.Surface(self.__panelRect.size, pygame.SRCALPHA)
        self.__panelSuperficie.fill((0, 0, 0, 170))
        self.__cacheTexto: str = ""
        self.__cacheLineas: List[str] = []

    # ------------------------------------------------------------------
    # Mensajes flotantes (alimentados por el patrón Observer)
    # ------------------------------------------------------------------
    def avanzarMensajes(self, dt: float) -> None:
        self.__hud.avanzar(dt)

    def limpiarMensajes(self) -> None:
        self.__hud.limpiar()

    def dibujarMensajes(self, pantalla: pygame.Surface) -> None:
        y = config.HUD_ALTO + 22
        for m in self.__hud.getMensajes():
            img = self.__fuenteMedia.render(m.texto, True, m.color)
            sombra = self.__fuenteMedia.render(m.texto, True, (0, 0, 0))
            alpha = int(255 * m.opacidad())
            img.set_alpha(alpha)
            sombra.set_alpha(alpha)
            centro = (config.ANCHO // 2, y)
            pantalla.blit(sombra, sombra.get_rect(center=(centro[0] + 2, centro[1] + 2)))
            pantalla.blit(img, img.get_rect(center=centro))
            y += 26

    # ------------------------------------------------------------------
    # Elementos comunes
    # ------------------------------------------------------------------
    def dibujarFondo(self, pantalla: pygame.Surface) -> None:
        pantalla.blit(self.__fondo, (0, 0))

    def __texto(self, pantalla: pygame.Surface, texto: str, fuente: pygame.font.Font,
                color: Color, centro: Tuple[int, int]) -> None:
        sombra = fuente.render(texto, True, (0, 0, 0))
        img = fuente.render(texto, True, color)
        pantalla.blit(sombra, sombra.get_rect(center=(centro[0] + 2, centro[1] + 2)))
        pantalla.blit(img, img.get_rect(center=centro))

    def __textoIzquierda(self, pantalla: pygame.Surface, texto: str, fuente: pygame.font.Font,
                         color: Color, posicion: Tuple[int, int]) -> None:
        """Texto alineado a la izquierda (esquina superior izquierda en ``posicion``)."""
        sombra = fuente.render(texto, True, (0, 0, 0))
        img = fuente.render(texto, True, color)
        pantalla.blit(sombra, (posicion[0] + 2, posicion[1] + 2))
        pantalla.blit(img, posicion)

    @staticmethod
    def __recortar(texto: str, maximo: int) -> str:
        return texto if len(texto) <= maximo else texto[:maximo - 1] + "…"

    # ------------------------------------------------------------------
    # Menú principal
    # ------------------------------------------------------------------
    def dibujarMenu(self, pantalla, universidad, estadoApi, totalUniversidades, top5,
                    nombre="", marcador="Explorador", maxNombre=14, focoNombre=True,
                    cursorVisible=True, paso=3, tiempo=0):
        from src.graficos import sprite_v9
        from src.cinematicas import BG, CREAM, GOLD, PEACH, EDGE, INK
        pantalla.fill(BG)
        rng = random.Random(451)
        for i in range(130):
            x,y=rng.randrange(960),rng.randrange(640)
            pygame.draw.rect(pantalla, (75,48,82) if i%5 else (170,133,151),(x,y,1+i%2,1+i%2))
        titulo=pygame.font.SysFont('georgia,cambria,serif',48,bold=True)
        medio=pygame.font.SysFont('trebuchetms,verdana',22)
        pequeno=pygame.font.SysFont('trebuchetms,verdana',16)
        meta=pygame.font.SysFont('consolas,couriernew',17,bold=True)
        def txt(t,x,y,f=medio,c=CREAM): self.__texto(pantalla,t,f,c,(x,y))
        def panel(r):
            pygame.draw.rect(pantalla,INK,r,border_radius=8)
            pygame.draw.rect(pantalla,EDGE,r,1,border_radius=8)
        if paso==0:
            pantalla.fill((5,4,10)); txt('UNA MISIÓN EN MARTE',480,320,titulo,GOLD)
            v=pygame.Surface((960,640));v.fill((5,4,10));v.set_alpha(int(255*(1-max(0,min(1,tiempo/.7,(3-tiempo)/.7)))));pantalla.blit(v,(0,0));return
        if paso in (1,2):
            txt('OPERACIÓN NOX  /  REGISTRO  0'+str(paso),480,130,meta,PEACH)
            txt('Universidad representante' if paso==1 else 'Ingresa tu nombre, explorador',480,215,titulo)
            panel((95,275,770,72))
            if paso==1:
                txt('<',120,310,medio,GOLD);txt('>',840,310,medio,GOLD)
                f=medio
                if f.size(universidad)[0]>670: f=pequeno
                txt(universidad,480,310,f)
                txt(('API en línea' if estadoApi==APIClient.EN_LINEA else 'Consultando API...' if estadoApi==APIClient.CARGANDO else 'Lista local / sin conexión')+f' · {totalUniversidades} universidades',480,375,pequeno,(112,207,194))
                txt('FLECHAS / ELEGIR',480,420,meta,PEACH)
            else:
                txt((nombre or marcador)+(' |' if cursorVisible else ''),480,310,medio)
                txt(f'Máximo {maxNombre} caracteres',480,375,pequeno,PEACH)
            txt('ENTER / CONFIRMAR',480,510,meta,GOLD);return
        txt('NOCTIS IV  /  OPERACIÓN NOX',270,30,meta,PEACH)
        txt('MISIÓN EN MARTE',310,80,titulo,GOLD)
        txt('Recolecta combustible, sobrevive a las tormentas',310,128,pequeno)
        txt('y escapa con los minerales de Nox.',310,151,pequeno)
        panel((45,180,535,54));txt('ENTER  /  INICIAR MISIÓN',312,207,medio,GOLD)
        for i,(k,v) in enumerate([('WASD / FLECHAS','Mover'),('ESPACIO','Construir · 3 minerales'),('F','Ofrecer 1 mineral'),('P / ESC','Pausa / salir')]):
            y=252+i*34;panel((45,y,155,28));txt(k,122,y+14,meta,GOLD);txt(v,355,y+14,pequeno)
        txt('Cuidado: radiación (verde), meteoritos (rojo) y arena (ralentiza).',310,405,pequeno,(220,50,50))
        pygame.draw.circle(pantalla,(52,29,52),(760,230),155)
        pygame.draw.circle(pantalla,EDGE,(760,230),155,2)
        from pathlib import Path
        img=pygame.image.load(str(config.RAIZ/'assets'/'aster_comic_0.png'))
        w,h=img.get_size();img=pygame.transform.scale(img,(int(w*300/h),300));pantalla.blit(img,img.get_rect(center=(760,230)))
        txt(nombre or marcador,760,398,meta,GOLD)
        panel((45,430,870,170));self.dibujarRanking(pantalla,top5,480,449)
        txt('TAB / CAMBIAR PILOTO Y UNIVERSIDAD     ·     ESC / SALIR',480,620,pequeno,PEACH)

    def __dibujarCampoNombre(self, pantalla: pygame.Surface, nombre: str, marcador: str,
                             enfocado: bool, cursorVisible: bool, centro: Tuple[int, int]) -> None:
        caja = pygame.Rect(0, 0, 300, 34)
        caja.center = centro
        pygame.draw.rect(pantalla, (30, 20, 26), caja)
        pygame.draw.rect(pantalla, (255, 230, 120) if enfocado else (160, 160, 160), caja, 2)
        if nombre:
            self.__texto(pantalla, nombre, self.__fuenteMedia, (255, 255, 255), centro)
            ancho = self.__fuenteMedia.size(nombre)[0]
        else:
            self.__texto(pantalla, marcador, self.__fuenteMedia, (120, 120, 120), centro)
            ancho = 0
        if enfocado and cursorVisible:
            x = centro[0] + ancho // 2 + 3
            pygame.draw.rect(pantalla, (255, 230, 120), (x, centro[1] - 11, 2, 22))

    def dibujarRanking(self, pantalla: pygame.Surface, registros: Sequence[RegistroPuntaje],
                       cx: int, yInicial: int) -> None:
        self.__texto(pantalla, "TOP 5 HISTÓRICO", self.__fuenteMedia, (255, 230, 120), (cx, yInicial))
        if not registros:
            self.__texto(pantalla, "Aún no hay puntajes: ¡sé el primero!", self.__fuentePeque,
                         (255, 255, 255), (cx, yInicial + 30))
            return
        for i, r in enumerate(registros[:config.MAX_PUNTAJES]):
            linea = (f"{i + 1}.  {r.puntaje:>5}   {self.__recortar(r.jugador, 14)}  ·  "
                     f"{self.__recortar(r.universidad, 34)} ({r.pais})")
            self.__texto(pantalla, linea, self.__fuentePeque, (255, 255, 255), (cx, yInicial + 28 + i * 22))

    # ------------------------------------------------------------------
    # HUD, pausa y overlays
    # ------------------------------------------------------------------
    def dibujarHUD(self, pantalla: pygame.Surface, nivel: Nivel, puntaje: int) -> None:
        e = nivel.getExplorador()
        pygame.draw.rect(pantalla, (13,10,23), (0,0,config.ANCHO,config.HUD_ALTO))
        pygame.draw.line(pantalla,(111,68,105),(0,51),(960,51),2)
        for x,w in ((10,105),(125,230),(365,175),(550,165),(725,225)):
            pygame.draw.rect(pantalla,(34,24,47),(x,4,w,23),border_radius=4)
        self.__texto(pantalla,f"NIVEL {nivel.getNumero():02}",self.__fuentePeque,(255,203,133),(62,15))
        self.__texto(pantalla,"VIDA",self.__fuentePeque,(250,220,181),(150,15))
        ratio=max(0,min(1,e.getSalud()/e.getSaludMaxima()))
        pygame.draw.rect(pantalla,(72,35,55),(181,9,163,12),border_radius=3)
        pygame.draw.rect(pantalla,(100,216,174) if ratio>.3 else (236,101,112),(181,9,int(163*ratio),12),border_radius=3)
        self.__texto(pantalla,f"NOX: {e.getInventarioMinerales()}",self.__fuentePeque,(140,235,220),(452,15))
        self.__texto(pantalla,f"TIEMPO: {int(nivel.getTiempo())} s",self.__fuentePeque,(246,160,139),(632,15))
        self.__texto(pantalla,f"PUNTAJE: {puntaje}",self.__fuentePeque,(255,203,133),(837,15))
        self.__texto(pantalla,nivel.descripcionObjetivo(),self.__fuentePeque,(250,220,181),(480,39))

    def dibujarPausa(self, pantalla: pygame.Surface) -> None:
        self.dibujarOverlay(pantalla, "PAUSA", "P para continuar · ESC para salir", (140, 220, 255))

    def dibujarOverlay(self, pantalla: pygame.Surface, titulo: str, subtitulo: str, color: Color,
                       lineas: Optional[List[str]] = None,
                       ranking: Optional[Sequence[RegistroPuntaje]] = None) -> None:
        velo = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        velo.fill((8,7,16,205)); pantalla.blit(velo,(0,0))
        cx=480
        panel=pygame.Rect(75,75,810,490) if ranking is not None else pygame.Rect(105,185,750,260)
        pygame.draw.rect(pantalla,(30,23,43),panel,border_radius=12)
        pygame.draw.rect(pantalla,(111,68,105),panel,2,border_radius=12)
        fuente=pygame.font.SysFont('georgia,cambria,serif',42,bold=True)
        self.__texto(pantalla,'OPERACIÓN NOX / INFORME DE MISIÓN',self.__fuentePeque,(246,160,139),(cx,panel.y+32))
        for tam in (38,34,30,26,22):
            if fuente.size(titulo)[0] <= panel.width-40: break
            fuente=pygame.font.SysFont("georgia,cambria,serif",tam,bold=True)
        self.__texto(pantalla,titulo,fuente,(255,203,133),(cx,panel.y+92))
        if titulo == "MISIÓN FALLIDA":
            pulso = (1 + math.sin(pygame.time.get_ticks() / 280.0)) / 2
            boton = pygame.Rect(cx-220, panel.y+126, 440, 44)
            pygame.draw.rect(pantalla, (52,33,57), boton, border_radius=6)
            borde = tuple(int(a+(b-a)*pulso) for a,b in zip((117,70,110),(255,203,133)))
            pygame.draw.rect(pantalla, borde, boton, 2, border_radius=6)
            subtitulo = "ENTER / REINTENTAR NIVEL"
        self.__texto(pantalla,subtitulo,self.__fuenteMedia,(250,220,181),(cx,panel.y+148))
        y=panel.y+190
        for linea in lineas or []:
            self.__texto(pantalla,linea,self.__fuente,(250,220,181),(cx,y));y+=28
        if ranking is not None: self.dibujarRanking(pantalla,ranking,cx,y+40)

    # ------------------------------------------------------------------
    # Pantalla narrativa (prólogo, conexiones entre niveles y epílogo)
    # ------------------------------------------------------------------
    def dibujarNarrativa(self, pantalla: pygame.Surface, titulo: str, subtitulo: str, texto: str,
                         visibles: int, terminado: bool, tiempo: float,
                         progreso: Optional[float] = None) -> None:
        """Dibuja la escena narrativa: ``visibles`` es la cantidad de caracteres ya "tecleados"."""
        cx = config.ANCHO // 2
        pantalla.blit(self.__fondoNarrativa, (0, 0))
        self.__texto(pantalla, titulo, self.__fuenteGrande, (255, 220, 120), (cx, 62))
        self.__texto(pantalla, subtitulo, self.__fuentePeque, (140, 230, 255), (cx, 110))

        # indicador de recepción
        panel = self.__panelRect
        pulso = int(tiempo * 3) % 2 == 0
        if not terminado:
            if pulso:
                pygame.draw.circle(pantalla, (255, 80, 80), (panel.x + 8, panel.y - 15), 5)
            etiqueta = "RECIBIENDO TRANSMISIÓN"
        else:
            pygame.draw.circle(pantalla, (120, 255, 150), (panel.x + 8, panel.y - 15), 5)
            etiqueta = "TRANSMISIÓN COMPLETA"
        self.__textoIzquierda(pantalla, etiqueta, self.__fuentePeque, (200, 200, 200),
                              (panel.x + 22, panel.y - 24))

        # panel + texto con efecto máquina de escribir
        pantalla.blit(self.__panelSuperficie, panel.topleft)
        pygame.draw.rect(pantalla, (140, 230, 255), panel, 2)
        lineas = self.__envolver(texto, panel.width - 56)
        x0, y = panel.x + 28, panel.y + 26
        restante = visibles
        ultimaX = x0
        for linea in lineas:
            parte = linea[:max(0, restante)]
            if parte:
                self.__textoIzquierda(pantalla, parte, self.__fuenteMedia, (200, 255, 220), (x0, y))
            ultimaX = x0 + self.__fuenteMedia.size(parte)[0]
            restante -= len(linea) + 1
            if restante < 0:
                break
            y += 36
        if int(tiempo * 3) % 2 == 0:                 # cursor parpadeante
            pygame.draw.rect(pantalla, (200, 255, 220), (ultimaX + 3, y + 4, 12, 22))

        # barra de progreso (solo pantalla de carga del prólogo)
        if progreso is not None:
            progreso = max(0.0, min(1.0, progreso))
            etiquetaCarga = ("Cargando misión... " + f"{int(progreso * 100)}%") if progreso < 1.0 \
                else "Carga completa · sistemas listos"
            self.__texto(pantalla, etiquetaCarga, self.__fuentePeque, (140, 230, 255),
                         (cx, config.ALTO - 110))
            barra = pygame.Rect(0, 0, 480, 16)
            barra.center = (cx, config.ALTO - 86)
            pygame.draw.rect(pantalla, (40, 25, 30), barra)
            relleno = barra.copy()
            relleno.width = int(barra.width * progreso)
            pygame.draw.rect(pantalla, (60, 220, 100), relleno)
            if 6 < relleno.width and progreso < 1.0:   # destello que recorre la barra
                x = relleno.x + int((tiempo * 240) % relleno.width)
                ancho = min(26, relleno.right - x)
                pygame.draw.rect(pantalla, (170, 255, 190), (x, relleno.y, ancho, relleno.height))
            pygame.draw.rect(pantalla, (255, 255, 255), barra, 2)

        # ayuda de control
        if terminado:
            color = (120, 255, 150) if int(tiempo * 2) % 2 == 0 else (70, 170, 100)
            self.__texto(pantalla, "ENTER / ESPACIO para continuar", self.__fuenteMedia, color,
                         (cx, config.ALTO - 40))
        else:
            self.__texto(pantalla, "ENTER / ESPACIO: completar el texto", self.__fuentePeque,
                         (170, 170, 170), (cx, config.ALTO - 40))

    def __envolver(self, texto: str, ancho: int) -> List[str]:
        """Divide ``texto`` en líneas que caben en ``ancho`` (conserva los saltos de párrafo)."""
        if texto == self.__cacheTexto:
            return self.__cacheLineas
        lineas: List[str] = []
        for parrafo in texto.split("\n"):
            if not parrafo.strip():
                lineas.append("")
                continue
            actual = ""
            for palabra in parrafo.split(" "):
                prueba = palabra if not actual else actual + " " + palabra
                if not actual or self.__fuenteMedia.size(prueba)[0] <= ancho:
                    actual = prueba
                else:
                    lineas.append(actual)
                    actual = palabra
            lineas.append(actual)
        self.__cacheTexto, self.__cacheLineas = texto, lineas
        return lineas

    # ------------------------------------------------------------------
    def __crearFondo(self) -> pygame.Surface:
        # Terreno decorativo a resolución nativa de pixel art (3x).
        sup = pygame.Surface((320,214))
        sup.fill((103,54,66))
        rng = random.Random(71)
        for _ in range(120):
            x,y=rng.randrange(320),rng.randrange(214)
            w,h=rng.randint(12,65),rng.randint(5,25)
            c=rng.choice([(109,57,68),(99,51,65),(115,61,69),(106,55,63)])
            pygame.draw.polygon(sup,c,[(x,y),(x+w//3,y-h//3),(x+w,y),(x+w-5,y+h),(x+5,y+h)])
        for _ in range(25):
            x,y=rng.randrange(320),rng.randrange(214)
            w=rng.randint(10,34); h=max(6,w//2)
            pygame.draw.ellipse(sup,(137,75,77),(x-1,y-1,w+2,h+3))
            pygame.draw.ellipse(sup,(73,39,55),(x,y,w,h))
            pygame.draw.ellipse(sup,(89,45,60),(x+2,y+3,w-4,h-4))
            pygame.draw.line(sup,(151,83,82),(x+w//4,y+h),(x+3*w//4,y+h))
        for _ in range(650):
            x,y=rng.randrange(320),rng.randrange(214)
            sup.set_at((x,y),rng.choice([(130,70,75),(83,44,58),(119,63,70)]))
        for _ in range(75):
            x,y=rng.randrange(320),rng.randrange(214); r=rng.randint(2,5)
            pygame.draw.rect(sup,(67,36,51),(x,y+2,r+2,3))
            pygame.draw.polygon(sup,(145,81,81),[(x,y+2),(x+1,y-1),(x+r,y),(x+r+1,y+2)])
            pygame.draw.line(sup,(103,51,65),(x+1,y+2),(x+r,y+2))
        return pygame.transform.scale(sup,(config.ANCHO,config.ALTO))

    def __crearFondoNarrativa(self) -> pygame.Surface:
        """Espacio profundo con estrellas, el planeta rojo al fondo y líneas de escaneo."""
        sup = pygame.Surface((config.ANCHO, config.ALTO))
        sup.fill((8, 6, 20))
        rng = random.Random(11)
        for _ in range(150):
            brillo = rng.randint(110, 255)
            pygame.draw.circle(sup, (brillo, brillo, brillo),
                               (rng.randint(0, config.ANCHO), rng.randint(0, config.ALTO)),
                               rng.choice((1, 1, 1, 2)))
        pygame.draw.circle(sup, (92, 38, 26), (config.ANCHO - 100, config.ALTO + 60), 250)
        pygame.draw.circle(sup, (140, 66, 42), (config.ANCHO - 90, config.ALTO + 70), 225)
        escaneo = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        for y in range(0, config.ALTO, 3):
            pygame.draw.line(escaneo, (0, 0, 0, 55), (0, y), (config.ANCHO, y))
        sup.blit(escaneo, (0, 0))
        return sup
