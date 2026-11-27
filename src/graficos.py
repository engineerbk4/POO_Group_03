"""Sprites procedurales: todo se dibuja por código (sin imágenes externas).

Son funciones puras de dibujo: reciben posición, tiempo de animación y el
estado visual mínimo, y pintan sobre la pantalla. No contienen lógica de juego,
así las entidades solo delegan aquí su ``_dibujarCuerpo``.
"""
from __future__ import annotations

import math
from functools import lru_cache
from typing import Tuple

import pygame

Color = Tuple[int, int, int]


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def circulo_alpha(pantalla: pygame.Surface, color: Color,
                  centro: Tuple[float, float], radio: float, alpha: int) -> None:
    """Dibuja un círculo semitransparente."""
    r = max(1, int(radio))
    capa = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(capa, (*color, max(0, min(255, alpha))), (r, r), r)
    pantalla.blit(capa, (int(centro[0]) - r, int(centro[1]) - r))


def elipse_alpha(pantalla: pygame.Surface, color: Color, rect: Tuple[int, int, int, int],
                 alpha: int) -> None:
    capa = pygame.Surface((max(1, rect[2]), max(1, rect[3])), pygame.SRCALPHA)
    pygame.draw.ellipse(capa, (*color, max(0, min(255, alpha))), capa.get_rect())
    pantalla.blit(capa, (rect[0], rect[1]))


def sombrear(color: Color, factor: float) -> Color:
    """Oscurece (<1) o aclara (>1) un color."""
    return (max(0, min(255, int(color[0] * factor))),
            max(0, min(255, int(color[1] * factor))),
            max(0, min(255, int(color[2] * factor))))


@lru_cache(maxsize=8)
def _fuente(tamano: int) -> pygame.font.Font:
    pygame.font.init()
    return pygame.font.Font(None, tamano)


# ----------------------------------------------------------------------
# Explorador: traje blanco, casco con visor reflejante y propulsores
# ----------------------------------------------------------------------
def dibujar_explorador(pantalla: pygame.Surface, x: float, y: float, radio: int, t: float,
                       moviendo: bool, orientacion: Tuple[float, float]) -> None:
    cx, cy = int(x), int(y)
    fx, fy = orientacion
    px, py = -fy, fx                                    # perpendicular a la orientación

    elipse_alpha(pantalla, (0, 0, 0), (cx - radio, cy + radio - 6, radio * 2, 10), 70)  # sombra

    # propulsores de la mochila (solo al moverse): llama que parpadea
    if moviendo:
        for lado in (-1, 1):
            bx = cx - fx * radio * 0.85 + px * lado * radio * 0.55
            by = cy - fy * radio * 0.85 + py * lado * radio * 0.55
            largo = 12 + 6 * math.sin(t * 45 + lado * 1.7)
            punta = (bx - fx * largo, by - fy * largo)
            ancho = 5
            exterior = [(bx + px * ancho, by + py * ancho), (bx - px * ancho, by - py * ancho), punta]
            interior = [(bx + px * 2.5, by + py * 2.5), (bx - px * 2.5, by - py * 2.5),
                        (bx - fx * largo * 0.55, by - fy * largo * 0.55)]
            pygame.draw.polygon(pantalla, (255, 140, 40), exterior)
            pygame.draw.polygon(pantalla, (255, 235, 130), interior)

    # mochila (detrás del cuerpo)
    mx, my = cx - fx * radio * 0.55, cy - fy * radio * 0.55
    pygame.draw.circle(pantalla, (150, 155, 170), (int(mx), int(my)), int(radio * 0.8))
    pygame.draw.circle(pantalla, (95, 100, 115), (int(mx), int(my)), int(radio * 0.8), 2)

    # traje
    pygame.draw.circle(pantalla, (236, 238, 246), (cx, cy), radio)
    pygame.draw.circle(pantalla, (40, 60, 90), (cx, cy), radio, 2)
    pygame.draw.circle(pantalla, (255, 255, 255), (cx - 5, cy - 6), radio // 3)   # brillo del traje

    # casco con visor
    vx, vy = cx + fx * radio * 0.38, cy + fy * radio * 0.38 - 2
    rv = int(radio * 0.62)
    pygame.draw.circle(pantalla, (25, 45, 85), (int(vx), int(vy)), rv + 2)
    pygame.draw.circle(pantalla, (45, 110, 190), (int(vx), int(vy)), rv)
    pygame.draw.circle(pantalla, (95, 175, 235), (int(vx - 1), int(vy - 1)), int(rv * 0.65))
    # reflejos que se deslizan lentamente sobre el cristal
    desliz = math.sin(t * 1.6) * rv * 0.25
    pygame.draw.ellipse(pantalla, (235, 248, 255),
                        (int(vx - rv * 0.55 + desliz), int(vy - rv * 0.65), int(rv * 0.7), int(rv * 0.38)))
    pygame.draw.circle(pantalla, (255, 255, 255), (int(vx + rv * 0.35 + desliz * 0.5), int(vy + rv * 0.25)), 2)

    # antenita con luz
    ax, ay = cx - px * radio * 0.5 - fx * radio * 0.3, cy - py * radio * 0.5 - fy * radio * 0.3 - radio * 0.7
    pygame.draw.line(pantalla, (90, 95, 110), (int(ax), int(ay + radio * 0.4)), (int(ax), int(ay)), 2)
    luz = (255, 80, 80) if int(t * 2) % 2 == 0 else (120, 30, 30)
    pygame.draw.circle(pantalla, luz, (int(ax), int(ay)), 3)


# ----------------------------------------------------------------------
# Mineral: cristal facetado que pulsa
# ----------------------------------------------------------------------
def dibujar_mineral(pantalla: pygame.Surface, x: float, y: float, radio: int, t: float,
                    color: Color) -> None:
    cx, cy = int(x), int(y)
    pulso = 0.5 + 0.5 * math.sin(t * 4)
    circulo_alpha(pantalla, color, (cx, cy), radio * 1.6 + 2 * pulso, int(18 + 30 * pulso))   # resplandor

    r = radio + 2 * math.sin(t * 4)
    arriba, abajo = (cx, cy - r * 1.35), (cx, cy + r * 1.1)
    izq_sup, der_sup = (cx - r * 0.85, cy - r * 0.25), (cx + r * 0.85, cy - r * 0.25)
    izq_inf, der_inf = (cx - r * 0.55, cy + r * 0.55), (cx + r * 0.55, cy + r * 0.55)
    pygame.draw.polygon(pantalla, sombrear(color, 0.62), [arriba, izq_sup, izq_inf, abajo])   # cara izquierda
    pygame.draw.polygon(pantalla, sombrear(color, 1.12), [arriba, der_sup, der_inf, abajo])   # cara derecha
    pygame.draw.polygon(pantalla, sombrear(color, 0.85), [arriba, izq_sup, (cx, cy + r * 0.1), der_sup])
    contorno = [arriba, der_sup, der_inf, abajo, izq_inf, izq_sup]
    pygame.draw.polygon(pantalla, (255, 255, 255), contorno, 2)
    pygame.draw.line(pantalla, (255, 255, 255), (cx, cy - r * 1.35), (cx, cy + r * 1.1), 1)

    # destello que gira
    ang = t * 2.5
    d = 4 + 3 * pulso
    sx, sy = cx - r * 0.3, cy - r * 0.55
    pygame.draw.line(pantalla, (255, 255, 255), (sx - d, sy), (sx + d, sy), 1)
    pygame.draw.line(pantalla, (255, 255, 255), (sx, sy - d), (sx, sy + d), 1)
    pygame.draw.circle(pantalla, (255, 255, 255), (int(sx + math.cos(ang)), int(sy + math.sin(ang))), 1)


# ----------------------------------------------------------------------
# Base: domo metálico con escudo energético animado
# ----------------------------------------------------------------------
def dibujar_base(pantalla: pygame.Surface, x: float, y: float, radio: int, t: float,
                 escudoActivo: bool, zonaRefugio: float) -> None:
    cx, cy = int(x), int(y)
    luz = (112, 222, 193) if escudoActivo else (220, 135, 92)
    circulo_alpha(pantalla, luz, (cx, cy), zonaRefugio, 18 if escudoActivo else 7)
    pygame.draw.circle(pantalla, luz, (cx, cy), int(zonaRefugio), 1)
    # Refugio modular: pixel art a resolución nativa de 36 x 36.
    img = pygame.Surface((36, 36), pygame.SRCALPHA)
    def poly(color, pts):
        pygame.draw.polygon(img, color, pts)
    def rect(color, x, y, w, h):
        pygame.draw.rect(img, color, (x,y,w,h))
    poly((36,22,36,150), [(2,28),(8,24),(28,24),(34,28),(34,32),(28,35),(8,35),(2,32)])
    poly((31,22,40), [(1,17),(8,10),(28,10),(35,17),(35,29),(28,33),(8,33),(1,29)])
    poly((104,69,99), [(3,18),(9,12),(27,12),(33,18),(33,27),(27,30),(9,30),(3,27)])
    poly((224,156,118), [(7,13),(12,7),(24,7),(29,13),(29,25),(7,25)])
    poly((141,82,89), [(7,16),(29,16),(29,25),(24,28),(12,28),(7,25)])
    rect((49,32,55),12,17,12,11)
    rect((83,126,132),14,18,8,7)
    rect(luz,15,19,6,2)
    rect((255,211,151),12,8,12,2)
    for xx in (4,27):
        rect((53,37,62),xx,20,5,8)
        rect(luz,xx+1,21,3,3)
    rect((48,31,52),17,2,2,6)
    rect(luz,16,1,4,3)
    if escudoActivo:
        rect((205,255,226) if math.sin(t*3)>0 else luz,17,1,2,2)
    img = pygame.transform.scale(img,(72,72))
    pantalla.blit(img,img.get_rect(center=(cx,cy)))


# ----------------------------------------------------------------------
# Marciano: antenas oscilantes, rostro según el estado
# ----------------------------------------------------------------------
def dibujar_marciano(pantalla: pygame.Surface, x: float, y: float, radio: int, t: float,
                     color: Color, expresion: str) -> None:
    cx, cy = int(x), int(y)
    elipse_alpha(pantalla, (0, 0, 0), (cx - radio, cy + radio - 4, radio * 2, 8), 60)

    # antenas que se mecen
    for lado in (-1, 1):
        bx, by = cx + lado * 6, cy - radio + 3
        sway = math.sin(t * 3 + lado) * 5
        tx, ty = bx + lado * 4 + sway, by - 13 + math.cos(t * 3 + lado) * 2
        pygame.draw.line(pantalla, sombrear(color, 0.7), (bx, by), (tx, ty), 2)
        pygame.draw.circle(pantalla, (255, 240, 120), (int(tx), int(ty)), 3)
        pygame.draw.circle(pantalla, (255, 255, 210), (int(tx) - 1, int(ty) - 1), 1)

    # patitas
    for lado in (-1, 1):
        pygame.draw.ellipse(pantalla, sombrear(color, 0.7), (cx + lado * 6 - 4, cy + radio - 5, 8, 6))

    # cuerpo
    pygame.draw.circle(pantalla, color, (cx, cy), radio)
    pygame.draw.circle(pantalla, sombrear(color, 0.7), (cx, cy), radio, 2)
    pygame.draw.circle(pantalla, sombrear(color, 1.25), (cx - 4, cy - 6), radio // 3)

    # ojos
    asustado = expresion == "asustado"
    for lado in (-1, 1):
        ox = cx + lado * 5
        pygame.draw.circle(pantalla, (255, 255, 255), (ox, cy - 3), 5 if asustado else 4)
        pupila = 1 if asustado else 2
        pygame.draw.circle(pantalla, (20, 20, 20), (ox + (0 if asustado else lado), cy - 3), pupila + 1)
    # boca
    if asustado:
        pygame.draw.circle(pantalla, (40, 30, 30), (cx, cy + 6), 3)
    else:
        pygame.draw.arc(pantalla, (40, 30, 30), (cx - 5, cy + 1, 10, 7), math.pi, 2 * math.pi, 2)


def dibujar_indicador_tecla(pantalla: pygame.Surface, x: float, y: float, tecla: str, t: float) -> None:
    """Cartelito ``[F]`` que flota sobre la cabeza de un marciano al que se puede ofrecer un mineral."""
    cx = int(x)
    cy = int(y + math.sin(t * 5) * 2)
    texto = _fuente(22).render(tecla, True, (20, 20, 30))
    caja = pygame.Rect(0, 0, texto.get_width() + 12, texto.get_height() + 6)
    from src import config
    cx = max(caja.width // 2 + 2, min(cx, config.ANCHO - caja.width // 2 - 2))
    cy = max(config.HUD_ALTO + caja.height // 2 + 2, cy)
    caja.center = (cx, cy)
    pygame.draw.rect(pantalla, (255, 235, 130), caja, border_radius=5)
    pygame.draw.rect(pantalla, (120, 90, 20), caja, 2, border_radius=5)
    pygame.draw.polygon(pantalla, (255, 235, 130),
                        [(cx - 4, caja.bottom - 1), (cx + 4, caja.bottom - 1), (cx, caja.bottom + 5)])
    pantalla.blit(texto, texto.get_rect(center=caja.center))


def dibujar_aura_curacion(pantalla: pygame.Surface, x: float, y: float, radio: int, t: float,
                          curando: bool) -> None:
    """Aura verde del marciano aliado; si está curando, salen cruces que suben."""
    cx, cy = int(x), int(y)
    pulso = 0.5 + 0.5 * math.sin(t * 3)
    r = radio + 10 + 3 * pulso
    circulo_alpha(pantalla, (90, 255, 150), (cx, cy), r, int(30 + 28 * pulso))
    pygame.draw.circle(pantalla, (150, 255, 190), (cx, cy), int(r), 1)
    if curando:
        for k in range(3):
            fase = (t * 0.9 + k / 3) % 1.0
            px = cx + (k - 1) * 9
            py = cy - radio - 4 - fase * 22
            tam = 4
            col = (170, 255, 190)
            pygame.draw.line(pantalla, col, (px - tam, py), (px + tam, py), 2)
            pygame.draw.line(pantalla, col, (px, py - tam), (px, py + tam), 2)


# ----------------------------------------------------------------------
# Criatura marciana: patas articuladas animadas
# ----------------------------------------------------------------------
def dibujar_criatura(pantalla: pygame.Surface, x: float, y: float, radio: int, t: float,
                     furiosa: bool) -> None:
    cx, cy = int(x), int(y)
    elipse_alpha(pantalla, (0, 0, 0), (cx - radio - 4, cy + radio - 4, radio * 2 + 8, 9), 70)

    borde = (24, 24, 37)
    pata = (151, 119, 116) if furiosa else (111, 124, 145)
    for i in range(8):
        base = i * math.pi / 4
        fase = t * 7 + i * 1.3
        cadera = (cx + math.cos(base) * radio * 0.65, cy + math.sin(base) * radio * 0.65)
        rodilla_ang = base + 0.45 * math.sin(fase)
        rodilla = (cadera[0] + math.cos(rodilla_ang) * radio * 0.9,
                   cadera[1] + math.sin(rodilla_ang) * radio * 0.9)
        pie_ang = base - 0.6 * math.sin(fase)
        pie = (rodilla[0] + math.cos(pie_ang) * radio * 0.75,
               rodilla[1] + math.sin(pie_ang) * radio * 0.75)
        pygame.draw.line(pantalla, borde, cadera, rodilla, 8)
        pygame.draw.line(pantalla, borde, rodilla, pie, 7)
        pygame.draw.line(pantalla, pata, cadera, rodilla, 5)
        pygame.draw.line(pantalla, sombrear(pata, 0.78), rodilla, pie, 4)
        pygame.draw.circle(pantalla, borde, (int(rodilla[0]), int(rodilla[1])), 4)
        pygame.draw.circle(pantalla, (137, 145, 158), (int(rodilla[0]), int(rodilla[1])), 2)
        pygame.draw.line(pantalla, (190, 166, 145), rodilla, pie, 2)
        pygame.draw.rect(pantalla, (190, 166, 145), (int(pie[0])-2, int(pie[1])-2, 4, 4))

    # Caparazón facetado, dibujado en una cuadrícula de 2 píxeles.
    capa = pygame.Surface((24, 24), pygame.SRCALPHA)
    def placa(color, puntos):
        pygame.draw.polygon(capa, color, puntos)
    placa(borde, [(12,0),(16,4),(19,4),(22,9),(22,17),(18,21),(6,21),(2,17),(2,9),(5,4),(8,4)])
    placa((68,80,103), [(12,2),(16,6),(19,6),(20,10),(18,13),(6,13),(4,10),(5,6),(8,6)])
    placa((112,128,151), [(12,2),(12,10),(8,12),(5,9),(8,6)])
    placa((49,58,78), [(13,3),(17,7),(19,7),(19,10),(14,12),(13,9)])
    placa((46,49,67), [(4,12),(9,15),(15,15),(20,12),(20,17),(17,19),(7,19),(4,17)])
    placa((88,101,122), [(6,17),(10,18),(14,18),(18,17),(16,19),(8,19)])
    ojo = (224,177,99) if furiosa else (195,169,107)
    placa(borde, [(4,10),(11,13),(11,16),(7,16),(4,14)])
    placa(borde, [(20,10),(13,13),(13,16),(17,16),(20,14)])
    placa(ojo, [(5,12),(10,14),(10,15),(7,15),(5,14)])
    placa(ojo, [(19,12),(14,14),(14,15),(17,15),(19,14)])
    pygame.draw.rect(capa, (153,163,178), (11,5,2,4))
    pygame.draw.rect(capa, (25,28,40), (11,16,2,2))
    tam = int(radio * 2.75)
    img = pygame.transform.scale(capa, (tam,tam))
    pantalla.blit(img, img.get_rect(center=(cx,cy)))


# ----------------------------------------------------------------------
# Cohete con fuego de propulsión
# ----------------------------------------------------------------------
def dibujar_cohete(pantalla: pygame.Surface, x: float, y: float, t: float, propulsando: bool) -> None:
    cx, cy = int(x), int(y)
    elipse_alpha(pantalla, (0, 0, 0), (cx - 38, cy + 40, 76, 16), 80)                 # plataforma
    pygame.draw.ellipse(pantalla, (80, 84, 96), (cx - 36, cy + 36, 72, 14))
    pygame.draw.ellipse(pantalla, (120, 126, 140), (cx - 36, cy + 36, 72, 14), 2)

    if propulsando:                                                                    # fuego animado
        largo = 26 + 10 * math.sin(t * 30)
        pygame.draw.polygon(pantalla, (255, 120, 30), [(cx - 11, cy + 36), (cx + 11, cy + 36),
                                                        (cx, cy + 36 + largo)])
        pygame.draw.polygon(pantalla, (255, 220, 90), [(cx - 6, cy + 36), (cx + 6, cy + 36),
                                                        (cx, cy + 36 + largo * 0.6)])
        for k in range(5):
            fase = (t * 2.2 + k / 5) % 1.0
            px = cx + math.sin(k * 7.3) * 12
            py = cy + 36 + largo * 0.6 + fase * 22
            circulo_alpha(pantalla, (255, 190, 120), (px, py), 3 + 2 * fase, int(160 * (1 - fase)))

    # aletas
    pygame.draw.polygon(pantalla, (200, 50, 50), [(cx - 16, cy + 36), (cx - 30, cy + 50), (cx - 16, cy + 18)])
    pygame.draw.polygon(pantalla, (200, 50, 50), [(cx + 16, cy + 36), (cx + 30, cy + 50), (cx + 16, cy + 18)])
    # fuselaje y nariz
    pygame.draw.rect(pantalla, (228, 230, 240), (cx - 16, cy - 10, 32, 46))
    pygame.draw.rect(pantalla, (170, 175, 190), (cx + 6, cy - 10, 10, 46))                # sombra lateral
    pygame.draw.polygon(pantalla, (225, 60, 60), [(cx - 16, cy - 10), (cx, cy - 50), (cx + 16, cy - 10)])
    pygame.draw.rect(pantalla, (225, 60, 60), (cx - 16, cy + 22, 32, 5))                  # franja
    pygame.draw.rect(pantalla, (130, 135, 150), (cx - 16, cy - 10, 32, 46), 2)
    # ventana
    pygame.draw.circle(pantalla, (60, 160, 230), (cx, cy + 4), 8)
    pygame.draw.circle(pantalla, (255, 255, 255), (cx - 3, cy + 1), 2)
    pygame.draw.circle(pantalla, (110, 115, 130), (cx, cy + 4), 8, 2)

# Pixel art V9: lienzo constante, sin eliminar colores interiores.
@lru_cache(maxsize=64)
def sprite_v9(nombre, frame, escala, espejo=False):
    from src.config import RAIZ
    img = pygame.image.load(str(RAIZ / "assets" / "sprites" / f"{nombre}_{frame}.png"))
    img = pygame.transform.scale(img, (escala, escala))
    return pygame.transform.flip(img, espejo, False) if espejo else img

def dibujar_explorador(pantalla, x, y, radio, t, moviendo, orientacion):
    img = sprite_v9("explorador", 1+int(t*7)%4 if moviendo else 0, 64, orientacion[0]<0)
    pantalla.blit(img, img.get_rect(midbottom=(int(x),int(y+radio))))

def dibujar_marciano(pantalla, x, y, radio, t, color, expresion):
    img = sprite_v9("ally" if expresion=="feliz" else "scared", int(t*5)%5, 64)
    pantalla.blit(img, img.get_rect(midbottom=(int(x),int(y+radio))))
