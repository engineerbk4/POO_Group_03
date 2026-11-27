"""Escucha las siete pistas originales. Ejecutar: python escuchar_soundtrack.py"""
from pathlib import Path
import pygame
PISTAS = [('menu','Noctis IV'),('historia','The Last Light'),('nivel1','Unknown Territory'),('nivel2','Against the Storm'),('nivel3','Leaving Mars'),('victoria','A New Dawn'),('derrota','Lost Signal')]
def main():
    pygame.mixer.init()
    try:
        while True:
            for i, (_, nombre) in enumerate(PISTAS, 1): print(f'{i}. {nombre}')
            opcion = input('Elige una pista (0 para salir): ').strip()
            if opcion == '0': break
            if not opcion.isdigit() or not 1 <= int(opcion) <= len(PISTAS): continue
            pista, nombre = PISTAS[int(opcion)-1]
            pygame.mixer.music.load(str(Path(__file__).resolve().parent / 'assets' / 'musica' / (pista+'.ogg')))
            pygame.mixer.music.set_volume(.45)
            pygame.mixer.music.play(-1)
            print('Reproduciendo:', nombre)
    finally: pygame.mixer.quit()
if __name__ == '__main__': main()
