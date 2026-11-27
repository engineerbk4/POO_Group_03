"""GestorAudio: efectos de sonido generados por código (sin archivos .wav).

Responsabilidad única: inicializar el mezclador y reproducir efectos.
Si no hay tarjeta de sonido (o el mezclador falla) el gestor queda en modo
silencioso y el juego sigue funcionando.

Efectos de la narrativa: ``transmision`` (estática de radio al abrir una
escena) y ``tecleo`` (tic sutil de la máquina de escribir).
"""
from __future__ import annotations

import array
import math
import random
from typing import Dict, List, Sequence, Tuple

import pygame

# (frecuencia inicial Hz, frecuencia final Hz, duración s, forma de onda, volumen 0..1)
Segmento = Tuple[float, float, float, str, float]


class GestorAudio:
    FRECUENCIA: int = 44100
    VOLUMEN_MAESTRO: float = 0.55

    def __init__(self) -> None:
        self.__sonidos: Dict[str, pygame.mixer.Sound] = {}
        self.__disponible: bool = False
        self.__canales: int = 1
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.FRECUENCIA, -16, 1, 512)
            inicio = pygame.mixer.get_init()
            if inicio is None:
                raise pygame.error("el mezclador no se inicializó")
            self.__frecuencia, formato, self.__canales = inicio
            if formato != -16:                       # solo generamos PCM de 16 bits con signo
                raise pygame.error(f"formato de audio no soportado: {formato}")
            self.__generarEfectos()
            self.__disponible = True
        except (pygame.error, OSError, ValueError, NotImplementedError) as error:
            self.__sonidos.clear()
            print(f"[audio] sonido desactivado: {error}")

    # ---- API pública ----
    def estaDisponible(self) -> bool:
        return self.__disponible

    def nombres(self) -> List[str]:
        return sorted(self.__sonidos)

    def reproducir(self, nombre: str) -> None:
        """Reproduce un efecto; si no hay audio o el nombre no existe, no hace nada."""
        sonido = self.__sonidos.get(nombre)
        if sonido is None:
            return
        try:
            sonido.play()
        except pygame.error:
            pass

    # ---- síntesis ----
    def __generarEfectos(self) -> None:
        self.__registrar("mineral", [(880, 1320, 0.07, "seno", 0.5), (1320, 1760, 0.10, "seno", 0.5)])
        self.__registrar("base", [(110, 80, 0.14, "cuadrada", 0.45), (330, 495, 0.12, "seno", 0.5),
                                  (495, 660, 0.16, "seno", 0.5)])
        self.__registrar("aliado", [(523, 523, 0.09, "seno", 0.5), (659, 659, 0.09, "seno", 0.5),
                                    (784, 784, 0.09, "seno", 0.5), (1047, 1047, 0.18, "seno", 0.55)])
        self.__registrar("dano", [(0, 0, 0.09, "ruido", 0.55), (220, 70, 0.14, "cuadrada", 0.4)])
        self.__registrar("pausa", [(660, 660, 0.05, "cuadrada", 0.3), (440, 440, 0.07, "cuadrada", 0.3)])
        self.__registrar("nivel", [(523, 523, 0.12, "cuadrada", 0.35), (659, 659, 0.12, "cuadrada", 0.35),
                                   (784, 784, 0.12, "cuadrada", 0.35), (1047, 1047, 0.30, "cuadrada", 0.4)])
        self.__registrar("gameover", [(440, 392, 0.2, "cuadrada", 0.4), (349, 294, 0.2, "cuadrada", 0.4),
                                      (262, 131, 0.5, "cuadrada", 0.45)])
        # ---- narrativa: transmisión de radio y tecleo suave (volúmenes bajos a propósito) ----
        self.__registrar("transmision", [(0, 0, 0.10, "ruido", 0.16), (1500, 1100, 0.07, "seno", 0.20),
                                         (900, 1300, 0.07, "seno", 0.20)])
        self.__registrar("tecleo", [(2200, 1700, 0.022, "seno", 0.14)])

    def __registrar(self, nombre: str, segmentos: Sequence[Segmento]) -> None:
        muestras = array.array("h")
        for ini, fin, dur, forma, vol in segmentos:
            muestras.extend(self.__segmento(ini, fin, dur, forma, vol))
        if self.__canales > 1:                       # duplicar cada muestra por canal
            estereo = array.array("h")
            for m in muestras:
                estereo.extend([m] * self.__canales)
            muestras = estereo
        sonido = pygame.mixer.Sound(buffer=muestras.tobytes())
        sonido.set_volume(self.VOLUMEN_MAESTRO)
        self.__sonidos[nombre] = sonido

    def __segmento(self, fIni: float, fFin: float, dur: float, forma: str, vol: float) -> "array.array[int]":
        n = max(1, int(self.__frecuencia * dur))
        salida = array.array("h")
        fase = 0.0
        ataque = max(1, int(0.005 * self.__frecuencia))
        for i in range(n):
            frac = i / n
            freq = fIni + (fFin - fIni) * frac
            fase += 2 * math.pi * freq / self.__frecuencia
            if forma == "ruido":
                onda = random.uniform(-1.0, 1.0)
            elif forma == "cuadrada":
                onda = 1.0 if math.sin(fase) >= 0 else -1.0
            else:
                onda = math.sin(fase)
            envolvente = min(1.0, i / ataque) * (1.0 - frac) ** 0.6   # ataque corto + caída suave
            salida.append(int(max(-1.0, min(1.0, onda * envolvente * vol)) * 32767))
        return salida
