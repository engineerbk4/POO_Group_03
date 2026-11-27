# Diagrama de clases (entrega final)

Mermaid: se visualiza directamente en GitHub o en <https://mermaid.live>.
Notación: `*--` composición · `o--` agregación · `-->` asociación · `..>` dependencia.

```mermaid
classDiagram
    direction LR

    %% ---------- Juego y colaboradores (SRP + DI) ----------
    class Juego {
        +gameLoop()
        +cambiarEstado(EstadoJuego)
        +iniciarPartida()
    }
    class EstadoJuego { <<abstract>> +manejar_eventos() +actualizar() +dibujar() }
    EstadoJuego <|-- EstadoMenu
    EstadoJuego <|-- EstadoJugando
    EstadoJuego <|-- EstadoPausa
    EstadoJuego <|-- EstadoNivelCompleto
    EstadoJuego <|-- EstadoGameOver
    EstadoJuego <|-- EstadoVictoria
    Juego --> EstadoJuego : estado actual (State)
    Juego o-- Nivel : agregación
    Juego --> InterfazJuego
    Juego --> APIClient
    Juego --> RepositorioPuntajes
    Juego --> GestorAudio

    %% ---------- Niveles ----------
    class Nivel { <<abstract>> +update(dt) +render() }
    Nivel <|-- NivelSupervivencia
    Nivel <|-- NivelDefensa
    Nivel <|-- NivelEscape
    Nivel *-- EntidadJuego : composición
    Nivel *-- Tormenta : composición
    Nivel ..> TormentaFactory : «use»

    %% ---------- Entidades ----------
    class EntidadJuego { <<abstract>> -salud +update(dt) +render() +esAfectablePorTormenta() }
    EntidadJuego <|-- Explorador
    EntidadJuego <|-- Mineral
    EntidadJuego <|-- Base
    EntidadJuego <|-- Marciano
    EntidadJuego <|-- CriaturaMarciana
    Explorador ..> Mineral : «use» recolectar(m)
    Explorador ..> Base : «create»
    Base --> Explorador : dueño
    CriaturaMarciana --> Explorador : objetivo

    %% ---------- State del Marciano ----------
    class EstadoMarciano { <<abstract>> +ejecutarAccion() +dibujarDetalles() }
    EstadoMarciano <|-- MarcianoAsustado
    EstadoMarciano <|-- MarcianoAliado
    Marciano o-- EstadoMarciano : agregación

    %% ---------- Factory Method ----------
    class TormentaFactory { +registrarTormenta() +crearTormenta() +tiposDisponibles() }
    class Tormenta { <<abstract>> }
    Tormenta <|-- TormentaRadiacion
    Tormenta <|-- TormentaMeteoritos
    Tormenta <|-- TormentaArena
    TormentaFactory ..> Tormenta : «create»

    %% ---------- Observer ----------
    class Sujeto { +suscribir() +desuscribir() +notificar() }
    class Observador { <<interface>> +actualizar(evento, datos) }
    Sujeto <|-- Explorador
    Sujeto <|-- Nivel
    Observador <|.. Nivel
    Observador <|.. ObservadorHUD
    Observador <|.. ObservadorLogger
    Observador <|.. ObservadorAudio
    Sujeto o-- Observador

    %% ---------- Servicios ----------
    APIClient ..> APIError : lanza
    RepositorioPuntajes ..> PersistenciaError : lanza
    ErrorMisionMarte <|-- APIError
    ErrorMisionMarte <|-- PersistenciaError
```
