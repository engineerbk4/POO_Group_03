"""Punto de entrada de 'Misión en Marte'.  Ejecutar desde la raíz:  python main.py

``main.py`` es la *raíz de composición*: aquí se crean y se conectan todas las
piezas (inyección de dependencias). Ninguna clase del juego construye a sus
colaboradores por su cuenta.
"""
from src import config
from src.juego import Juego
from src.niveles.defensa import NivelDefensa
from src.niveles.escape import NivelEscape
from src.niveles.supervivencia import NivelSupervivencia
from src.patrones.observer import ObservadorAudio, ObservadorHUD, ObservadorLogger
from src.servicios.api_client import APIClient
from src.servicios.gestor_audio import GestorAudio
from src.servicios.repositorio_puntajes import RepositorioPuntajes
from src.tormentas.arena import TormentaArena
from src.tormentas.fabrica import TormentaFactory
from src.tormentas.meteoritos import TormentaMeteoritos
from src.tormentas.radiacion import TormentaRadiacion
from src.vista.interfaz import InterfazJuego


def main() -> None:
    # fábrica con registro dinámico (Open/Closed): una tormenta nueva
    # = una línea aquí, sin tocar TormentaFactory ni los niveles.
    fabrica = TormentaFactory()
    fabrica.registrarTormenta("radiacion", TormentaRadiacion)
    fabrica.registrarTormenta("meteoritos", TormentaMeteoritos)
    fabrica.registrarTormenta("arena", TormentaArena)

    niveles = [NivelSupervivencia(fabrica), NivelDefensa(fabrica), NivelEscape(fabrica)]

    # Servicios
    audio = GestorAudio()
    api = APIClient()
    api.iniciarCargaAsincrona()              # no bloquea: la ventana abre de inmediato
    repositorio = RepositorioPuntajes(config.RUTA_PUNTAJES)

    # Patrón Observer: los observadores se suscriben a cada nivel
    observadorHUD = ObservadorHUD()
    observadores = [observadorHUD, ObservadorLogger(config.RUTA_LOG), ObservadorAudio(audio)]
    for nivel in niveles:
        for observador in observadores:
            nivel.suscribir(observador)

    interfaz = InterfazJuego(observadorHUD)
    Juego(niveles, api, repositorio, interfaz, audio).gameLoop()


if __name__ == "__main__":
    main()
