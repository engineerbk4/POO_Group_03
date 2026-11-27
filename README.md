# 🚀 Misión en Marte

Videojuego 2D en **Python + Pygame** desarrollado por el **Equipo 03** (Ingeniería Informática, UPCH) como proyecto final del curso de **Programación Orientada a Objetos** (ciclo 2026-2).

El jugador controla a un **Explorador** que recolecta combustible, construye bases de refugio, convierte a marcianos asustados en aliados y sobrevive a tormentas de radiación, lluvias de meteoritos, tormentas de arena y criaturas hostiles hasta escapar del planeta. Antes de jugar elige la **universidad que representa** (datos de una API pública) y su puntaje entra en un **Top 5 histórico**.

## ▶️ Cómo ejecutarlo

```bash
git clone <URL_DEL_REPOSITORIO>
cd POO_Group_03
pip install -r requirements.txt
python main.py
```

Requiere Python 3.10 o superior. No usa imágenes ni sonidos externos: sprites y audio se generan por código. Sin internet el juego funciona igual (lista de universidades de respaldo).

Para verificar el proyecto sin abrir ventana:

```bash
python verificar_proyecto.py
```

## 🎮 Controles

| Tecla | Acción |
|-------|--------|
| `W A S D` / flechas | Mover al explorador |
| `ESPACIO` | Construir una base (cuesta 3 minerales; protege y cura) |
| `F` | Dar 1 mineral a un marciano asustado (aparece el cartel `[F]`) para volverlo aliado |
| `P` | Pausar / reanudar |
| `U` / `Shift+U` | En el menú: siguiente / anterior universidad representante |
| `ENTER` | Comenzar / continuar / reintentar |
| `ESC` | Salir |

## 🗺️ Niveles

1. **Supervivencia:** reunir 10 de combustible.
2. **Defensa:** mantener 3 bases en pie durante 40 s.
3. **Escape:** reunir 6 de combustible y llegar al cohete.

## 🧱 Estructura del proyecto

```
POO_Group_03/
├── main.py                       # raíz de composición (inyección de dependencias)
├── verificar_proyecto.py         # pruebas automáticas sin ventana
├── data/high_scores.json         # Top 5 persistente
├── logs/partida.log              # eventos con marca de tiempo (Observer)
└── src/
    ├── config.py                 # constantes
    ├── excepciones.py            # ErrorMisionMarte > APIError, PersistenciaError
    ├── graficos.py               # sprites procedurales animados
    ├── juego.py                  # Juego: solo Game Loop + coordinación (SRP)
    ├── patrones/observer.py      # Observador, Sujeto, HUD / Logger / Audio
    ├── estados_juego/            # State del flujo: Menú, Jugando, Pausa, NivelCompleto, GameOver, Victoria
    ├── entidades/                # EntidadJuego (abstracta) y subclases + State del Marciano
    ├── tormentas/                # Tormenta (abstracta), radiación, meteoritos, arena, fábrica
    ├── niveles/                  # Nivel (abstracta) y los 3 niveles
    ├── servicios/                # api_client, repositorio_puntajes, gestor_audio
    └── vista/interfaz.py         # fondo, HUD, menú, pausa, overlays, ranking
```

## 🧠 Conceptos de POO aplicados

### Principios de diseño (SOLID, cohesión y acoplamiento)
- **SRP / alta cohesión:** `Juego` solo coordina el Game Loop. El dibujo está en `InterfazJuego`, la red en `APIClient`, el disco en `RepositorioPuntajes` y el sonido en `GestorAudio`.
- **Open/Closed:** el Game Loop llama a `update(dt)` / `render()` sin conocer el tipo concreto (cero `isinstance()` en el dominio). Nuevas tormentas, estados o observadores se agregan sin modificar las clases existentes (`TormentaArena` se registra desde `main.py`).
- **Bajo acoplamiento:** `Juego` recibe niveles, cliente API, repositorio, interfaz y audio por **inyección de dependencias** desde `main.py`. `APIClient` solo entrega `str` y `List[str]` (acoplamiento de datos), jamás respuestas HTTP ni excepciones de red.
- **Encapsulamiento estricto:** atributos críticos privados (`__salud`), sin setters destructivos.

### Relaciones UML
| Relación | Dónde |
|----------|-------|
| **Composición** | `Nivel` crea y destruye sus `EntidadJuego` y `Tormenta` |
| **Agregación** | `Juego` recibe sus `Nivel`; `Marciano` recibe su `EstadoMarciano` |
| **Asociación** | `Base → Explorador`, `CriaturaMarciana → Explorador`, `Marciano → objetivo` |
| **Dependencia** | `Explorador ..> Mineral` `<<use>>` (`recolectar(m)`: lo usa y no lo conserva), `Explorador ..> Base` `<<create>>`, `Nivel ..> TormentaFactory` |

Diagrama completo en [`docs/diagrama_clases.md`](docs/diagrama_clases.md).

### Patrones de diseño
1. **Factory Method** — `TormentaFactory` con registro dinámico (`registrarTormenta`, `crearTormenta`, `tiposDisponibles`). Tormentas: radiación, meteoritos y arena (esta última registrada solo en `main.py`).
2. **State (doble aplicación)**
   - `EstadoMarciano` → `MarcianoAsustado` / `MarcianoAliado`: conducta, color, rostro, cartel `[F]` y aura de curación.
   - `EstadoJuego` → `EstadoMenu`, `EstadoJugando`, `EstadoPausa`, `EstadoNivelCompleto`, `EstadoGameOver`, `EstadoVictoria`: reemplazan los `if/elif` de `Juego`.
3. **Observer** — `Explorador` y `Nivel` son *sujetos*; notifican `SALUD_CAMBIADA`, `MINERAL_RECOLECTADO`, `BASE_CONSTRUIDA`, `MARCIANO_ALIADO`, `NIVEL_COMPLETADO` y `JUGADOR_DERROTADO`. Observadores: `ObservadorHUD` (mensajes flotantes), `ObservadorLogger` (`logs/partida.log`) y `ObservadorAudio` (efectos de sonido).

### API externa, excepciones y persistencia
- `APIClient` consulta `http://universities.hipolabs.com/search?country=Peru` con `urllib` (timeout 3 s, en un hilo para no congelar la ventana). Captura `HTTPError`, `URLError`, `TimeoutError` y `JSONDecodeError` con `try / except / else / finally` y los convierte en `APIError`; ante cualquier fallo usa una lista offline que incluye la **Universidad Peruana Cayetano Heredia**.
- Excepciones propias: `ErrorMisionMarte` → `APIError`, `PersistenciaError`.
- `RepositorioPuntajes` guarda el Top 5 en `data/high_scores.json` (`json.dump` / `json.load` con `with open`), maneja `FileNotFoundError`, `PermissionError` y JSON corrupto (lo respalda y continúa).

## 👥 Equipo 03

| Integrante | Módulos a cargo |
|------------|-----------------|
| Yanella Salcedo | Núcleo y entidades base: `entidad_juego`, `mineral`, `explorador`, `base` |
| Josué Barzola | Marcianos y patrón State: `estados`, `marciano`, `criatura` |
| Rebeca Cerdan | Tormentas, Factory y Game Loop: `tormentas/`, `juego.py` |
| Jose Bances | Niveles y documentación: `niveles/`, `docs/` |

## 🔀 Flujo de trabajo con Git

- La rama `main` siempre contiene código que funciona.
- Cada tarea se hace en una rama propia: `feature/<tarea>`.
- Los cambios entran a `main` solo mediante **Pull Request** revisado por otro integrante.
- Mensajes de commit en español, claros y en presente: `Agrega ...`, `Corrige ...`.

Detalle del reparto y pasos: [`docs/GUIA_EQUIPO.md`](docs/GUIA_EQUIPO.md).

## 📄 Licencia

MIT. Ver `LICENSE`.
