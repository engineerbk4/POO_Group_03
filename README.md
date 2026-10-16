# 🚀 Misión en Marte

We are **Team 03**, a group of four Computer Engineering students from Universidad Peruana Cayetano Heredia (UPCH). This repository contains our final project for the **Object-Oriented Programming** course (2026-2).

We are Ready!

---

## 🌌 La historia y el juego

En un futuro donde el Sol comienza a morir, un explorador emprende una misión hacia Marte en busca de minerales que puedan ayudar a prolongar la supervivencia de su planeta. Sin embargo, Marte no está vacío: al llegar, descubre comunidades marcianas divididas, criaturas hostiles y peligrosas tormentas espaciales que cambian constantemente las condiciones del planeta.

El videojuego es una aventura 2D desarrollada en **Python + Pygame** donde el jugador deberá:
- Recolectar combustible mineral.
- Construir bases de refugio para protegerse y recuperar salud.
- Sobrevivir a tormentas de radiación y lluvias de meteoritos.
- Defenderse de criaturas marcianas hostiles.
- Ganarse la confianza de marcianos asustados ofreciéndoles minerales para convertirlos en aliados.

---

## ▶️ Cómo ejecutar el juego

Requiere **Python 3.10** o superior. Ejecuta los siguientes comandos en tu terminal:

    git clone https://github.com/engineerbk4/POO_Group_03.git
    cd POO_Group_03
    pip install -r requirements.txt
    python main.py

---

## 🎮 Controles

| Tecla | Acción |
|---|---|
| **W A S D** / **Flechas** | Mover al explorador por el mapa |
| **ESPACIO** | Construir una base (cuesta 3 minerales; protege y cura al estar cerca) |
| **F** | Dar 1 mineral a un marciano asustado (verde) para volverlo aliado (azul) |
| **ENTER** | Iniciar partida / Pasar al siguiente nivel / Reintentar |
| **ESC** | Salir del juego |

---

## 🗺️ Niveles de la misión

1. **Supervivencia:** Reunir 10 unidades de combustible mineral mientras sobrevives a las amenazas.
2. **Defensa:** Construir y mantener 3 bases en pie durante 40 segundos frente a las tormentas y criaturas.
3. **Escape:** Reunir 6 unidades de combustible y llegar hasta el cohete para escapar de Marte.

---

## 🧠 Arquitectura y Conceptos de POO aplicados

El proyecto demuestra el dominio de los pilares de la Programación Orientada a Objetos mediante una arquitectura de **18 clases**, **6 pilares de POO** y **2 patrones de diseño**, evitando por completo el uso de condicionales de tipo (`isinstance`):

- **Encapsulamiento estricto:** Los atributos críticos (como `__salud`, `__inventarioMinerales` o `__registroTormentas`) utilizan *name mangling* (doble guion bajo) sin setters destructivos. El estado interno solo cambia mediante métodos validados como `recibirDano()` y `curar()`.
- **Abstracción y Polimorfismo:** Uso del módulo `abc` y `@abstractmethod` en las clases base (`EntidadJuego`, `Nivel`, `Tormenta` y la interfaz `EstadoMarciano`). El Game Loop actualiza y dibuja todas las entidades llamando a `update()` y `render()` sin conocer su tipo concreto.
- **Relaciones entre objetos:**
  - **Composición:** `Nivel` crea, contiene y destruye sus propias entidades y tormentas.
  - **Agregación:** `Juego` recibe sus instancias de `Nivel` desde afuera; `Marciano` recibe su estado.
  - **Asociación:** `Base` y `CriaturaMarciana` conocen al `Explorador` para colaborar o interactuar con él.
  - **Dependencia:** `Explorador` instancia una `Base` al construirla y `Nivel` solicita eventos a `TormentaFactory`.
- **Patrón State:** Aplicado en `Marciano`. El personaje delega su comportamiento en su estado actual (`estadoActual.ejecutarAccion(self, dt)`), pasando de `MarcianoAsustado` (huye del jugador) a `MarcianoAliado` (lo sigue y lo cura) al recibir un mineral.
- **Patrón Factory Method:** Implementado en `TormentaFactory` mediante un diccionario de registro dinámico, cumpliendo el principio *Open/Closed* para agregar nuevas tormentas en una sola línea dentro de `main.py`.

### Diagrama UML

📌 [Ver diagrama UML](docs/uml/UML_ Mision en Marte-Final-Corregido.jpg) 

---

## 🛠️ Tecnologías

| Tecnología | Uso |
|---|---|
| **Python 3** | Lenguaje principal (`abc`, `typing`, `math`, `random`) |
| **Pygame** | Ventana gráfica, Game Loop, renderizado 2D y manejo de eventos |
| **Draw.io** | Modelado del diagrama de clases UML |
| **Visual Studio Code** | Entorno de desarrollo e integración |
| **Git & GitHub** | Control de versiones con ramas `feature/` y revisión por Pull Requests |

---

## 📂 Estructura del repositorio

    POO_Group_03/
    ├── main.py                  # Punto de entrada del juego
    ├── requirements.txt         # Dependencias del proyecto (pygame)
    ├── README.md                # Documentación principal
    ├── LICENSE                  # Licencia MIT
    ├── assets/                  # Recursos gráficos y capturas
    ├── docs/                    # Informe académico, presentación y diagramas UML
    └── src/                     # Código fuente modularizado
        ├── entidades/           # EntidadJuego, Explorador, Mineral, Base, Criatura y State
        ├── niveles/             # Nivel abstracto, Supervivencia, Defensa y Escape
        ├── tormentas/           # Tormenta abstracta, Radiación, Meteoritos y Factory
        ├── juego.py             # Controlador del Game Loop, fases y HUD
        ├── config.py            # Constantes globales (resolución, FPS, colores)
        └── graficos.py          # Funciones auxiliares de dibujo y transparencias

---

## 🧑‍🚀 Tripulación (Equipo 03)

| Integrante | Módulos y responsabilidades a cargo |
|---|---|
| **Jose Junior Bances Panaque** | Arquitectura base, núcleo (`EntidadJuego`, `Explorador`, `Mineral`, `Base`), encapsulamiento e integración en Git. |
| **Yanella Stefhany Salcedo Siguas** | Relaciones entre objetos, lógica de `Marciano`, `CriaturaMarciana` e implementación del **Patrón State**. |
| **Rebeca Milagros Cerdan Dongo** | Jerarquía de `Tormenta`, **Patrón Factory Method** (`TormentaFactory`), polimorfismo y controlador `Juego`. |
| **Josue Obed Barzola Reategui** | Implementación de `Nivel` (`Supervivencia`, `Defensa`, `Escape`), pruebas de demostración y documentación en `docs/`. |

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta el archivo `LICENSE` para más detalles.
