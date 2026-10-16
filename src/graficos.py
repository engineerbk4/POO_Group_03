"""Utilidades de dibujo compartidas (sin lógica de juego)."""
from typing import Tuple

import pygame

Color = Tuple[int, int, int]


def circulo_alpha(pantalla: pygame.Surface, color: Color,
                  centro: Tuple[float, float], radio: float, alpha: int) -> None:
    """Dibuja un círculo semitransparente."""
    r = max(1, int(radio))
    capa = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(capa, (*color, max(0, min(255, alpha))), (r, r), r)
    pantalla.blit(capa, (int(centro[0]) - r, int(centro[1]) - r))
