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
    # zona de refugio (curación)
    circulo_alpha(pantalla, (120, 200, 255), (cx, cy), zonaRefugio, 22)
    pygame.draw.circle(pantalla, (150, 215, 255), (cx, cy), int(zonaRefugio), 1)

    elipse_alpha(pantalla, (0, 0, 0), (cx - radio, cy + radio - 8, radio * 2, 14), 80)   # sombra
    pygame.draw.circle(pantalla, (62, 66, 78), (cx, cy), radio + 4)                      # plataforma
    pygame.draw.circle(pantalla, (95, 100, 112), (cx, cy), radio + 4, 2)

    # domo: círculos concéntricos desplazados hacia la luz (degradado metálico)
    pasos = 7
    for i in range(pasos):
        frac = i / (pasos - 1)
        r = int(radio * (1 - 0.72 * frac))
        gris = int(105 + 120 * frac)
        pygame.draw.circle(pantalla, (gris, gris + 4, gris + 14),
                           (int(cx - 6 * frac), int(cy - 7 * frac)), r)
    pygame.draw.circle(pantalla, (80, 85, 98), (cx, cy), radio, 3)
    for k in range(6):                                                                    # paneles
        ang = k * math.pi / 3 + 0.5
        pygame.draw.line(pantalla, (112, 118, 132), (cx, cy),
                         (cx + math.cos(ang) * radio, cy + math.sin(ang) * radio), 1)
    pygame.draw.ellipse(pantalla, (240, 246, 255), (cx - 12, cy - 15, 12, 7))             # reflejo
    pygame.draw.rect(pantalla, (60, 70, 90), (cx - 5, cy + 7, 10, 10), border_radius=3)   # puerta
    luz = (80, 255, 120) if int(t * 2) % 2 == 0 else (30, 100, 50)
    pygame.draw.circle(pantalla, luz, (cx + int(radio * 0.62), cy - int(radio * 0.2)), 3)

    if escudoActivo:
        pulso = 0.5 + 0.5 * math.sin(t * 3)
        rs = radio + 8 + 2 * pulso
        circulo_alpha(pantalla, (80, 170, 255), (cx, cy), rs, int(55 + 35 * pulso))
        pygame.draw.circle(pantalla, (150, 215, 255), (cx, cy), int(rs), 2)
        rect = pygame.Rect(cx - int(rs) - 3, cy - int(rs) - 3, int(rs) * 2 + 6, int(rs) * 2 + 6)
        for k in range(3):                                   # arcos de energía que giran
            ini = t * 1.8 + k * 2 * math.pi / 3
            pygame.draw.arc(pantalla, (230, 250, 255), rect, ini, ini + 0.7, 3)


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

    pata = (225, 55, 55) if furiosa else (190, 40, 45)
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
        pygame.draw.line(pantalla, pata, cadera, rodilla, 3)
        pygame.draw.line(pantalla, sombrear(pata, 0.75), rodilla, pie, 3)
        pygame.draw.circle(pantalla, (255, 210, 190), (int(pie[0]), int(pie[1])), 2)

    cuerpo = (200, 35, 55) if furiosa else (160, 28, 45)
    pygame.draw.circle(pantalla, cuerpo, (cx, cy), radio)
    pygame.draw.circle(pantalla, sombrear(cuerpo, 0.6), (cx, cy), radio, 2)
    pygame.draw.circle(pantalla, sombrear(cuerpo, 1.3), (cx - 4, cy - 6), radio // 3)
    for k in range(-1, 2):                                   # púas dorsales
        px = cx + k * 7
        pygame.draw.polygon(pantalla, (95, 15, 30), [(px - 3, cy - radio + 3), (px + 3, cy - radio + 3),
                                                      (px, cy - radio - 5)])
    # ojos con pupila vertical y ceño fruncido
    for lado in (-1, 1):
        ox = cx + lado * 6
        pygame.draw.circle(pantalla, (255, 230, 60), (ox, cy - 2), 4)
        pygame.draw.line(pantalla, (0, 0, 0), (ox, cy - 5), (ox, cy + 1), 2)
        pygame.draw.line(pantalla, (60, 0, 10), (ox - lado * 5, cy - 9 + (0 if lado < 0 else 0)),
                         (ox + lado * 1, cy - 6), 2)
    # colmillos
    pygame.draw.polygon(pantalla, (245, 245, 240), [(cx - 5, cy + 6), (cx - 2, cy + 6), (cx - 3.5, cy + 11)])
    pygame.draw.polygon(pantalla, (245, 245, 240), [(cx + 2, cy + 6), (cx + 5, cy + 6), (cx + 3.5, cy + 11)])


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
    img = sprite_v9("aster", 1+int(t*7)%4 if moviendo else 0, 64, orientacion[0]<0)
    pantalla.blit(img, img.get_rect(midbottom=(int(x),int(y+radio))))

def dibujar_marciano(pantalla, x, y, radio, t, color, expresion):
    img = sprite_v9("ally" if expresion=="feliz" else "scared", int(t*5)%5, 64)
    pantalla.blit(img, img.get_rect(midbottom=(int(x),int(y+radio))))
