# Guía Completa de Programación Orientada a Objetos (Sesiones 1 a 13) y Plan de Refactorización para *Misión en Marte*

**Curso:** Programación Orientada a Objetos — Ingeniería Informática (UPCH)  
**Proyecto analizado:** `POO_Group_03-main` (*Misión en Marte*)

---

## Parte I: Compendio Detallado de las Sesiones 1 a 13

### Sesión 1: Paradigma Orientado a Objetos y Abstracción
* **Objetivo:** Comprender el cambio de enfoque desde la programación estructurada (funciones y datos separados) hacia el modelado basado en objetos que integran estado y comportamiento.
* **Conceptos clave:**
  * **Abstracción:** Extraer únicamente las características esenciales de un elemento del dominio ignorando detalles irrelevantes.
  * **Clase:** Molde o plantilla que define la estructura (atributos) y el comportamiento (métodos) de un tipo de entidad.
  * **Objeto:** Instancia concreta de una clase en memoria. Posee **identidad** (referencia única), **estado** (valores actuales de sus atributos) y **comportamiento** (operaciones que ejecuta).
* **Aplicación en videojuegos:** Cada elemento activo del mundo (explorador, marciano, mineral, meteorito, tormenta) se modela como un objeto con responsabilidades claras en lugar de variables sueltas.

---

### Sesión 2: Clases, Objetos y Ciclo de Vida en Código
* **Objetivo:** Implementar clases en lenguajes orientados a objetos (Python, C++, Java), gestionando la inicialización y destrucción de instancias.
* **Conceptos clave:**
  * **Constructor (`__init__`):** Método especial que inicializa el estado válido de un objeto al momento de instanciarlo.
  * **Referencia propia (`self` / `this`):** Permite a cada instancia acceder a sus propios atributos y métodos.
  * **Destructor (`__del__` / `~Clase()`):** Libera recursos asociados cuando el objeto deja de existir.
  * **Métodos especiales:** `__str__` y `__repr__` para representación legible y depuración.
  * **Atributos de instancia vs. atributos de clase:** Los de instancia pertenecen a cada objeto; los de clase se comparten entre todas las instancias (útiles para constantes o contadores globales).

---

### Sesión 3: Encapsulamiento y Control de Acceso
* **Objetivo:** Proteger la integridad del estado interno de los objetos evitando modificaciones arbitrarias desde el exterior.
* **Conceptos clave:**
  * **Ocultamiento de información (*Information Hiding*):** Separar la interfaz pública (qué hace el objeto) de su implementación interna (cómo lo hace).
  * **Niveles de visibilidad en Python:**
    * Público (`atributo`): accesible desde cualquier parte.
    * Protegido (`_atributo`): convención de uso interno o para subclases.
    * Privado (`__atributo`): aplica *name mangling* (`_Clase__atributo`) para restringir acceso externo directo.
  * **Getters, Setters y `@property`:** Permiten validar reglas de negocio antes de alterar un atributo (por ejemplo, impedir que la vida o el oxígeno sean negativos o superen el máximo permitido).

---

### Sesión 4: Relaciones entre Clases (UML y Código)
* **Objetivo:** Modelar cómo colaboran las clases entre sí y traducir diagramas UML a estructuras de código fieles al ciclo de vida de los objetos.
* **Tipos de relación:**
  1. **Dependencia (`- - ->`):** Uso temporal de otra clase (como parámetro o variable local en un método).
  2. **Asociación (`———`):** Relación estructural estable (unidireccional o bidireccional) con multiplicidades (`1..1`, `1..*`, `*..*`).
  3. **Agregación (`◇———`, "tiene un" débil):** El contenedor almacena referencias a objetos creados fuera de él (ej. `Inventario` contiene `Mineral`es); si el contenedor desaparece, los elementos pueden seguir existiendo.
  4. **Composición (`◆———`, "es parte de" fuerte):** El contenedor crea y controla el ciclo de vida completo de sus partes (ej. `Nivel` se compone de su `Mapa` o `SistemaTormentas`); si el contenedor se destruye, sus partes también.

---

### Sesión 5: Herencia y Reutilización de Código
* **Objetivo:** Construir jerarquías de clases que eviten duplicación de código mediante la relación **"es un" (*is-a*)**.
* **Conceptos clave:**
  * **Superclase (clase base) y Subclase (clase derivada):** La subclase hereda atributos y métodos de la superclase y añade especializaciones propias.
  * **Uso de `super()`:** Invoca el constructor o métodos de la clase padre para reutilizar la inicialización y lógica común.
  * **Beneficio:** Centraliza cambios comunes en un único punto de la jerarquía.

---

### Sesión 6: Polimorfismo y Sobrescritura (*Overriding*)
* **Objetivo:** Lograr que objetos de distintas subclases respondan de forma particular ante un mismo mensaje.
* **Conceptos clave:**
  * **Sobrescritura (*Overriding*):** Una subclase redefine un método de la superclase manteniendo su firma para adaptar su comportamiento (ej. `actualizar()` o `recibir_daño()`).
  * **Despacho dinámico (*Dynamic Dispatch*):** En tiempo de ejecución se invoca el método correspondiente al tipo real del objeto, permitiendo recorrer colecciones heterogéneas sin preguntar por el tipo (`isinstance` / `if/elif`).

---

### Sesión 7: Abstracción Avanzada — Clases Abstractas e Interfaces
* **Objetivo:** Definir contratos obligatorios que las subclases deben implementar sin permitir instanciar conceptos incompletos.
* **Conceptos clave:**
  * **Clases Abstractas (`ABC` y `@abstractmethod` en Python):** Combinan estado/métodos concretos compartidos con métodos abstractos obligatorios.
  * **Interfaces (clases `ABC` con solo métodos abstractos en Python, `interface` en Java, virtuales puros `= 0` en C++):** Definen capacidades transversales (ej. `Colisionable`, `Renderizable`, `Observador`).
  * **Regla de oro:** *Programar contra interfaces/abstracciones, no contra implementaciones concretas.*

---

### Sesión 8: Principios GRASP de Asignación de Responsabilidades
* **Objetivo:** Decidir con criterio técnico qué clase debe asumir cada responsabilidad en el diseño.
* **Principios fundamentales:**
  * **Experto en Información (*Information Expert*):** Asignar la responsabilidad a la clase que posee los datos necesarios para cumplirla.
  * **Creador (*Creator*):** Asignar la creación de una instancia `B` a la clase `A` que la contiene, agrega o registra estrechamente.
  * **Controlador (*Controller*):** Objeto no visual que coordina los eventos del sistema y delega el trabajo a las entidades del dominio.
  * **Alta Cohesión (*High Cohesion*) y Bajo Acoplamiento (*Low Coupling*):** Mantener clases enfocadas y con mínimas dependencias directas.
  * **Polimorfismo y Variaciones Protegidas:** Encapsular puntos de cambio detrás de interfaces estables.

---

### Sesión 9: Modelado UML Integral y Auditoría Arquitectónica
* **Objetivo:** Consolidar los diagramas de clases antes de escalar el proyecto, verificando consistencia entre atributos, métodos, visibilidad (`+`, `-`, `#`), multiplicidades y dirección de dependencias.
* **Criterios de revisión:**
  * Eliminar dependencias circulares innecesarias.
  * Verificar que ninguna entidad de dominio gestione directamente entrada/salida de disco o renderizado si existe una capa dedicada.

---

### Sesión 10: Persistencia y Manejo de Excepciones
* **Objetivo:** Garantizar que los datos del programa sobrevivan entre ejecuciones y que los errores en tiempo de ejecución se gestionen sin colapsar la aplicación.
* **Persistencia de datos:**
  * **Memoria vs. Disco:** Las variables en RAM desaparecen al cerrar el proceso; la persistencia guarda el estado en disco o red.
  * **Formatos principales:**
    * *Texto plano / CSV:* Legible, útil para logs o tablas simples.
    * *Binario / Serialización nativa (`pickle` en Python):* Compacto y rápido, pero acoplado al lenguaje y versión.
    * *JSON (`json.dump` / `json.load`):* Estructurado, legible e interoperable entre lenguajes y APIs web.
    * *Bases de datos:* Consultas, integridad y concurrencia.
  * **Serialización y Deserialización:** Transformar un objeto en memoria a una representación transferible/almacenable (JSON/bytes) y reconstruirlo después.
* **Manejo de excepciones:**
  * Diferencia entre **errores de sintaxis**, **excepciones en tiempo de ejecución** (`FileNotFoundError`, `ValueError`, `OSError`, `json.JSONDecodeError`) y **errores lógicos**.
  * Estructura `try / except / else / finally` y uso obligatorio de administradores de contexto (`with open(...)`) para liberar recursos.
  * **Excepciones personalizadas:** Crear clases propias heredando de `Exception` (ej. `ArchivoCorruptoError`, `ErrorConexionAPI`) y encadenar causas con `raise ... from e`.
  * **6 prácticas de robustez:** (1) Validar antes de usar, (2) Capturar excepciones específicas, (3) Liberar recursos siempre, (4) Escritura atómica (archivo temporal + renombrado), (5) Versionar el formato guardado, (6) Registrar errores en log y informar sin cerrar abruptamente.

---

### Sesión 11: Principios de Diseño Orientado a Objetos (Cohesión, Acoplamiento y SOLID)
* **Objetivo:** Evaluar y mejorar la calidad estructural del código mediante métricas conceptuales y los cinco principios SOLID.
* **Cohesión (de mayor a menor calidad):**
  * *Funcional* (Alta — ideal) $\rightarrow$ *Secuencial* $\rightarrow$ *Comunicacional* $\rightarrow$ *Procedural* $\rightarrow$ *Temporal* $\rightarrow$ *Lógica* $\rightarrow$ *Coincidental* (Muy baja — antipatrón tipo `Utils`).
* **Acoplamiento (de mejor a peor calidad):**
  * *Por interfaz* (Muy bajo — ideal) $\rightarrow$ *De datos* $\rightarrow$ *De control* $\rightarrow$ *Común* (variables globales) $\rightarrow$ *De contenido* (acceso a internos privados).
* **Principios SOLID:**
  * **S — Single Responsibility Principle (SRP):** Una clase debe tener una única razón para cambiar (separar datos, reglas de negocio, persistencia y renderizado).
  * **O — Open/Closed Principle (OCP):** Abierto a extensión, cerrado a modificación. Agregar un nuevo enemigo o nivel debe hacerse creando una nueva subclase, no editando cadenas `if/elif`.
  * **L — Liskov Substitution Principle (LSP):** Toda subclase debe poder sustituir a su clase base sin romper el comportamiento esperado.
  * **I — Interface Segregation Principle (ISP):** Preferir interfaces pequeñas y específicas antes que una interfaz gigante.
  * **D — Dependency Inversion Principle (DIP):** Los módulos de alto nivel no deben depender de detalles de bajo nivel; ambos deben depender de abstracciones (inyección de dependencias).
* **Lecciones del caso de estudio (Super Mario Bros):**
  * El jugador no guarda partidas (`GameRepository`), no carga niveles (`GameController`) ni crea enemigos (`EnemyFactory`).
  * El tablero no se dibuja (`Renderer`) ni calcula colisiones (`CollisionSystem`).
  * Los efectos de ítems se modelan con una interfaz (`ItemEffect`) en lugar de strings o condicionales.

---

### Sesión 12: Patrones de Diseño (GoF) y Fundamentos de Pygame
* **Objetivo:** Aplicar soluciones arquitectónicas probadas a problemas recurrentes e introducir el motor 2D Pygame.
* **Patrones de diseño clave:**
  1. **Factory Method (Creacional):** Define una interfaz para crear objetos dejando que las subclases/fábricas decidan qué clase concreta instanciar. Elimina `if/elif` de creación.
  2. **Singleton (Creacional):** Garantiza una única instancia global (ej. gestor de recursos o configuración) con control de creación (`__new__` + `threading.Lock`).
  3. **Strategy (Comportamiento):** Encapsula algoritmos intercambiables (ej. patrones de movimiento de marcianos o comportamiento de tormentas) para cambiarlos dinámicamente en ejecución.
  4. **Observer (Comportamiento):** Define una suscripción `1..*` donde un sujeto (`Explorador` o `Juego`) notifica automáticamente a sus observadores (`HUD`, `SistemaSonido`, `GestorPuntuacion`) cuando cambia su estado.
* **Fundamentos de Pygame (Parte 1):**
  * `pygame.Surface`, `blit()`, `fill()`, `pygame.time.Clock().tick(60)`.
  * Bucle de eventos (`pygame.event.get()`), teclado (`KEYDOWN`, `key.get_pressed()`) y mouse (`MOUSEBUTTONDOWN`).
  * Colisiones con `pygame.Rect` (`colliderect`, `collidepoint`).
  * Renderizado de fuentes (`pygame.font.Font.render`) y audio (`pygame.mixer.Sound` para efectos cortos, `pygame.mixer.music` para música de fondo).

---

### Sesión 13: POO Aplicada a Videojuegos (Pygame Parte 2), Bases de Datos y APIs/Servicios
* **Objetivo:** Integrar todos los pilares y patrones en una arquitectura completa de videojuego conectada con servicios externos y persistencia.
* **Pygame Orientado a Objetos (Parte 2):**
  * **`pygame.sprite.Sprite` y `Group`:** Cada entidad hereda de `Sprite`, encapsula su `self.image` y `self.rect`, y concentra su lógica en `update()` y `.kill()`.
  * **Composición vs. Herencia:** Usar herencia para taxonomía ("un `MarcianoCazador` es un `Marciano`") y composición para capacidades ("una entidad tiene un componente de arma, escudo o movimiento").
  * **Patrón State para el flujo del juego:** Reemplazar banderas booleanas e `if/elif` gigantes en el *Game Loop* por clases de estado (`EstadoMenu`, `EstadoInstrucciones`, `EstadoJugando`, `EstadoPausa`, `EstadoGameOver`) con métodos polimórficos `manejar_eventos()`, `actualizar()` y `dibujar()`.
* **Bases de Datos, APIs y Servicios:**
  * **Desajuste Objeto-Relacional y Patrón Repository / DAO:** Aislar la persistencia detrás de una interfaz (`RepositorioPuntuaciones`) para poder guardar puntajes en una API REST o en un archivo JSON local sin alterar la lógica del juego.
  * **Arquitectura en Capas y DTOs:** Separar `Cliente/Vista` $\rightarrow$ `Controller/Estado` $\rightarrow$ `Service` $\rightarrow$ `Repository/APIClient`, intercambiando objetos simples de transferencia de datos (`DTO`).
  * **Inyección de Dependencias por constructor:** Pasar el `APIClient` o `RepositorioPuntuaciones` al controlador/estado del juego desde fuera para facilitar pruebas y tolerancia a fallos.

---

## Parte II: Diagnóstico de tu Proyecto (`POO_Group_03-main`) frente a las Sesiones 1–13

> **Nota técnica importante sobre el archivo `.zip`:** Al subir un archivo `.zip`, el entorno permite inspeccionar el **árbol completo de carpetas y el tamaño exacto en bytes de los 51 archivos**, pero no extrae automáticamente el texto interno de los `.py`. A partir del análisis estructural de tu repositorio `POO_Group_03-main`, ya se identifican hallazgos arquitectónicos exactos. Cuando subas o pegues directamente los archivos `.py` con contenido, aplicaremos estos cambios línea por línea sobre tu código actual sin rehacer el juego.

### 1. Radiografía Actual del Repositorio
Tu repositorio ya tiene diseñada una carpeta objetivo limpia, pero el código funcional actual está concentrado en módulos monolíticos mientras los archivos modulares están en `0 bytes`:

| Estado | Archivos en tu ZIP (`POO_Group_03-main`) | Diagnóstico POO (Sesiones 1–13) |
| :--- | :--- | :--- |
| **Código activo actual** | `main.py` (704 B)<br>`src/config.py` (265 B)<br>`src/graficos.py` (549 B)<br>`src/juego.py` (8,561 B)<br>`src/entidades/__init__.py` (17,366 B)<br>`src/niveles/__init__.py` (13,117 B)<br>`src/tormentas/__init__.py` (6,642 B) | **Baja cohesión / Archivos sobrecargados (Sesión 11 - SRP):** Toda la jerarquía de entidades está dentro de `src/entidades/__init__.py` (17.3 KB) y todos los niveles dentro de `src/niveles/__init__.py` (13.1 KB). |
| **Esqueletos listos (0 bytes)** | `src/api/api_client.py` (0 B)<br>`src/entities/base.py`, `entidad_juego.py`, `explorador.py`, `marciano.py`, `mineral.py` (0 B)<br>`src/levels/nivel.py`, `nivel_defensa.py`, `nivel_escape.py`, `nivel_supervivencia.py` (0 B)<br>`src/patterns/factory.py`, `observer.py`, `state.py` (0 B)<br>`src/game.py` (0 B) | **Arquitectura objetivo sin implementar:** Ya definieron exactamente los módulos de **Sesión 11, 12 y 13** (`entities`, `levels`, `patterns`, `api_client`), pero aún falta migrar/refactorizar la lógica desde `entidades/`, `niveles/` y `juego.py` hacia ellos. |
| **Recursos multimedia** | `assets/.gitkeep` (0 B) | **Sesión 12/13 (Pygame):** Aún no existen sprites `.png` ni efectos `.wav`/`.mp3`, por lo que el renderizado depende solo de formas primitivas en `graficos.py`. |

### 2. Mapa de Mejoras POO (Sin rehacer tu videojuego)
1. **Refactorización incremental sin romper compatibilidad (Sesiones 3, 5, 6, 7 y 11):**
   * Mover cada clase de `src/entidades/__init__.py` a su módulo correspondiente en `src/entities/` (`EntidadJuego` como clase base `ABC` heredando de `pygame.sprite.Sprite`, `Explorador`, `Marciano`, `Mineral`) y mantener en `src/entidades/__init__.py` las importaciones de re-exportación (`from src.entities import ...`) para que nada se rompa durante la transición.
   * Hacer lo mismo con `src/niveles/__init__.py` $\rightarrow$ `src/levels/nivel.py` (`ABC`), `nivel_supervivencia.py`, `nivel_defensa.py`, `nivel_escape.py` y los nuevos niveles.
   * Asegurar **encapsulamiento** (`_salud`, `_oxigeno`, `_energia`, `_puntaje` con `@property` y métodos `recibir_daño()`, `recolectar_mineral()`).
2. **Patrones de Diseño en `src/patterns/` (Sesiones 12 y 13):**
   * `state.py`: Descomponer `src/juego.py` (8.5 KB) en estados polimórficos (`EstadoMenu`, `EstadoInstrucciones`, `EstadoJugando`, `EstadoPausa`, `EstadoGameOver`, `EstadoTablaPuntuaciones`).
   * `factory.py`: Centralizar la creación de marcianos, meteoritos, zonas de radiación y minerales según la dificultad/nivel (cumpliendo **OCP**).
   * `observer.py`: Desacoplar el `Explorador` y el `Nivel` del HUD, el audio y el registro de puntos.

---

## Parte III: Diseño Técnico de las 4 Mejoras Solicitadas

### Mejora 1: `APIClient` para la Tabla de Puntuaciones (`src/api/api_client.py`)
Aplicando **Sesión 10 (Persistencia JSON + Excepciones propias)** y **Sesión 13 (Repository, DTO e Inyección de Dependencias)**:
* Se define un DTO (`RegistroPuntuacion` con `jugador`, `puntaje`, `nivel_alcanzado`, `fecha`) y una interfaz `RepositorioPuntuaciones(ABC)` con `guardar_puntuacion(registro)` y `obtener_top(limite=10)`.
* `APIClient` implementa la comunicación HTTP (`GET` y `POST` en JSON) con `timeout` controlado y excepciones propias (`ErrorConexionAPI`, `RespuestaInvalidaAPI`).
* **Tolerancia a fallos (Patrón Proxy / Fallback Local):** Si el servidor no responde o no hay internet, un repositorio compuesto guarda y lee automáticamente desde `data/puntuaciones_local.json` con escritura atómica, evitando que el juego se congele o cierre.

### Mejora 2: Sprites y Sonido (Sesiones 12 y 13 — Pygame)
Aplicando **Sesión 12 (`Singleton`, `pygame.mixer`, `image.load`)** y **Sesión 13 (`pygame.sprite.Sprite`)**:
* Crear un `GestorRecursos` (`src/utils/recursos.py`) que cargue imágenes desde `assets/sprites/` con `.convert_alpha()` y sonidos desde `assets/sonidos/` (`pygame.mixer.Sound` para recolección de mineral, impacto de meteorito, daño por radiación y alerta de tormenta; `pygame.mixer.music` para ambiente marciano).
* **Fallback visual seguro:** Si un archivo `.png` aún no existe en `assets/`, `GestorRecursos` genera automáticamente una `pygame.Surface` con el dibujo geométrico actual de `graficos.py`, garantizando que el juego siempre sea jugable mientras el equipo incorpora el arte final.

### Mejora 3: Balanceo y Más Niveles (Sesión 11 OCP + Sesión 12 Factory/Strategy)
Aplicando **Principio Abierto/Cerrado (OCP)** y **Patrón Strategy / Factory**:
* Extraer los parámetros de balanceo a una estructura declarativa (`ConfiguracionNivel` en `src/config.py`) para ajustar sin tocar lógica interna:
  * Velocidad base y aceleración de meteoritos (aros rojos).
  * Daño por segundo y radio de expansión de la radiación (zonas verdes).
  * Tiempo de supervivencia / cuota de minerales requerida y cadencia de marcianos.
* **Expansión de niveles en `src/levels/`** heredando de la clase abstracta `Nivel`:
  1. `NivelSupervivencia` (Nivel 1 — Recolección básica y tormentas leves).
  2. `NivelDefensa` (Nivel 2 — Oleadas de marcianos y mayor densidad de meteoritos).
  3. `NivelEscape` (Nivel 3 — Extracción contrarreloj con zonas de radiación dinámicas).
  4. `NivelTormentaMagnetica` (Nivel 4 — Nuevo: tormentas periódicas que reducen visibilidad e invierten/alteran controles brevemente).
  5. `NivelNucleoCrater` (Nivel 5 — Nuevo: combinación de radiación expansiva, lluvia intensa de meteoritos y marcianos de élite).

### Mejora 4: Resaltado en Rojo en la Pantalla de Instrucciones
En el estado/pantalla de instrucciones (`EstadoInstrucciones` o método de dibujado de instrucciones en `juego.py` / `graficos.py`), en lugar de renderizar toda la línea con un solo `font.render(..., color_blanco)`, se divide el renderizado por segmentos horizontales usando `surface.get_width()` para alinear exactamente las palabras sin solapamientos:
* Texto normal en blanco/gris claro, y el fragmento exacto **`"Cuidado: radiación (zona verde) y meteoritos (aros rojos)"`** renderizado con color rojo de alerta `(235, 50, 50)` (e incluso destacando visualmente el contraste del aviso).

```python
# Helper reutilizable para renderizar líneas con segmentos resaltados en rojo
def dibujar_linea_resaltada(superficie, fuente, segmentos, x_inicial, y):
    """
    segmentos: lista de tuplas (texto, color_rgb)
    Ejemplo:
    [
        ("Importante - ", (230, 230, 230)),
        ("Cuidado: radiación (zona verde) y meteoritos (aros rojos)", (235, 45, 45)),
    ]
    """
    x_actual = x_inicial
    for texto, color in segmentos:
        render_texto = fuente.render(texto, True, color)
        superficie.blit(render_texto, (x_actual, y))
        x_actual += render_texto.get_width()
```