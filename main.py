"""Punto de entrada de 'Misión en Marte'.  Ejecutar:  python main.py"""
from src.juego import Juego
from src.niveles import NivelDefensa, NivelEscape, NivelSupervivencia
from src.tormentas import TormentaFactory, TormentaMeteoritos, TormentaRadiacion


def main() -> None:
    # Registro dinámico (Open/Closed): una tormenta nueva = una línea aquí,
    # sin tocar TormentaFactory.
    fabrica = TormentaFactory()
    fabrica.registrarTormenta("radiacion", TormentaRadiacion)
    fabrica.registrarTormenta("meteoritos", TormentaMeteoritos)

    niveles = [NivelSupervivencia(fabrica), NivelDefensa(fabrica), NivelEscape(fabrica)]
    Juego(niveles).gameLoop()


if __name__ == "__main__":
    main()
