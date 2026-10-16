# 🚀 Misión en Marte

Videojuego 2D en **Python + Pygame** desarrollado por el **Equipo 03** (Ingeniería Informática, UPCH) como proyecto final del curso de **Programación Orientada a Objetos** (ciclo 2026-2).

El jugador controla a un **Explorador** que recolecta combustible, construye bases de refugio, convierte a marcianos asustados en aliados y sobrevive a tormentas de radiación, lluvias de meteoritos y criaturas hostiles hasta escapar del planeta.

## ▶️ Cómo ejecutarlo

```bash
git clone <URL_DEL_REPOSITORIO>
cd POO_Group_03
pip install -r requirements.txt
python main.py
```

Requiere Python 3.10 o superior.

## 🎮 Controles

| Tecla | Acción |
|-------|--------|
| `W A S D` / flechas | Mover al explorador |
| `ESPACIO` | Construir una base (cuesta 3 minerales; protege y cura) |
| `F` | Dar 1 mineral a un marciano asustado para volverlo aliado |
| `ENTER` | Continuar / reintentar |
| `ESC` | Salir |

## 🗺️ Niveles

1. **Supervivencia:** reunir 10 de combustible.
2. **Defensa:** mantener 3 bases en pie durante 40 s.
3. **Escape:** reunir 6 de combustible y llegar al cohete.

## 🧱 Estructura del proyecto

```
POO_Group_03/
├── main.py                  # punto de entrada
├── requirements.txt
├── src/
│   ├── config.py            # constantes
│   ├── graficos.py          # utilidades de dibujo
│   ├── juego.py             # Juego: Game Loop, fases, HUD
│   ├── entidades/           # EntidadJuego y sus subclases
│   │   ├── entidad_juego.py   (abstracta)
│   │   ├── mineral.py, explorador.py, base.py
│   │   ├── estados.py         (patrón State)
│   │   ├── marciano.py, criatura.py
│   ├── tormentas/
│   │   ├── tormenta.py        (abstracta)
│   │   ├── radiacion.py, meteoritos.py
│   │   └── fabrica.py         (patrón Factory Method)
│   └── niveles/
│       ├── nivel.py           (abstracta)
│       └── supervivencia.py, defensa.py, escape.py
├── assets/                  # capturas, sprites y sonidos
└── docs/                    # informe, diagrama de clases, guía del equipo
```

## 🧠 Conceptos de POO aplicados

- **Encapsulamiento:** atributos críticos privados (`__salud`), sin setters destructivos.
- **Herencia y polimorfismo:** `EntidadJuego` abstracta; el Game Loop llama a `update()` sin conocer el tipo concreto.
- **Composición:** `Nivel` crea y destruye sus entidades. **Agregación:** `Juego` recibe sus niveles; `Marciano` recibe su estado.
- **Asociación:** `Base → Explorador`, `CriaturaMarciana → Explorador`.
- **Patrones:** Factory Method (`TormentaFactory`, registro dinámico) y State (`Marciano`).

## 👥 Equipo 03

| Integrante | Módulos a cargo |
|------------|-----------------|
| (nombre) | Núcleo y entidades base: `entidad_juego`, `mineral`, `explorador`, `base` |
| (nombre) | Marcianos y patrón State: `estados`, `marciano`, `criatura` |
| (nombre) | Tormentas, Factory y Game Loop: `tormentas/`, `juego.py` |
| (nombre) | Niveles y documentación: `niveles/`, `docs/` |

## 🔀 Flujo de trabajo con Git

- La rama `main` siempre contiene código que funciona.
- Cada tarea se hace en una rama propia: `feature/<tarea>`.
- Los cambios entran a `main` solo mediante **Pull Request** revisado por otro integrante.
- Mensajes de commit en español, claros y en presente: `Agrega ...`, `Corrige ...`.

Detalle del reparto y pasos: [`docs/GUIA_EQUIPO.md`](docs/GUIA_EQUIPO.md).

## 📄 Licencia

MIT. Ver `LICENSE`.
