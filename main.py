"""Punto de entrada de 'Misión en Marte'.  Ejecutar desde la raíz:  python main.py"""
from src.juego import Juego
from src.niveles.defensa import NivelDefensa
from src.niveles.escape import NivelEscape
from src.niveles.supervivencia import NivelSupervivencia
from src.tormentas.fabrica import TormentaFactory
from src.tormentas.meteoritos import TormentaMeteoritos
from src.tormentas.radiacion import TormentaRadiacion


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
