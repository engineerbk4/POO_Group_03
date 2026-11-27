# Guía del equipo: reparto de tareas y pasos con Git

## 1. Reparto (4 integrantes)

| # | Rol | Rama | Archivos que sube |
|---|-----|------|-------------------|
| 1 | Núcleo y repositorio | `feature/nucleo-entidades` | `main.py`, `README.md`, `requirements.txt`, `.gitignore`, todos los `__init__.py`, `src/config.py`, `src/graficos.py`, `entidades/entidad_juego.py`, `mineral.py`, `explorador.py`, `base.py` |
| 2 | Marcianos y State | `feature/marcianos-state` | `entidades/estados.py`, `marciano.py`, `criatura.py` |
| 3 | Tormentas, Factory y Game Loop | `feature/tormentas-factory` y luego `feature/game-loop` | `tormentas/tormenta.py`, `radiacion.py`, `meteoritos.py`, `fabrica.py`; después `src/juego.py` |
| 4 | Niveles y documentación | `feature/niveles` y luego `docs/informe-y-presentacion` | `niveles/nivel.py`, `supervivencia.py`, `defensa.py`, `escape.py`; después `docs/` y `assets/capturas/` |

**Revisión cruzada (quién aprueba el Pull Request de quién):** 2 revisa a 1, 3 revisa a 2, 4 revisa a 3, 1 revisa a 4.

## 2. Orden de integración

1. **PR 1 (integrante 1)** → se une primero; todos los demás dependen de `EntidadJuego`.
2. **PR 2 (integrante 2)** y **PR 3 (integrante 3, tormentas)** pueden ir en paralelo, partiendo de `main` ya actualizado.
3. **PR 4 (integrante 4, niveles)** necesita lo anterior ya unido.
4. **PR 5 (integrante 3, `juego.py`)** y **PR 6 (integrante 4, docs)** cierran el avance.
5. Con todo unido, cada uno ejecuta `python main.py` y verifica que el juego corre.

## 3. Pasos para cada integrante

```bash
# a) Obtener el repositorio (solo la primera vez)
git clone <URL_DEL_REPOSITORIO>
cd POO_Group_03

# b) Antes de cada tarea: actualizar main y crear tu rama
git checkout main
git pull
git checkout -b feature/nombre-de-tu-rama

# c) Copiar SOLO tus archivos desde el zip a sus carpetas, y luego:
git status
git add <tus archivos>
git commit -m "Agrega <qué hiciste>"

# d) Subir la rama
git push -u origin feature/nombre-de-tu-rama
```

Después, en GitHub: **Compare & pull request** → describir qué incluye → pedir revisión al compañero asignado → **Merge** cuando lo apruebe.

### Solo el integrante 1, antes de copiar sus archivos
Limpia el contenido anterior sin perder el historial (los commits viejos siguen disponibles):

```bash
git rm -r assets docs src main.py README.md
git commit -m "Reinicia la estructura del proyecto"
```
Se conservan `LICENSE` y `.gitignore` (este último se reemplaza por el nuevo).

## 4. Buenas prácticas

- Commits pequeños y frecuentes; cada uno con un solo propósito.
- Nunca subir `__pycache__` ni archivos del editor (el `.gitignore` ya los excluye).
- No trabajar directamente sobre `main`.
- Cada integrante debe poder explicar el código que subió: se evalúa en la exposición.

## 5. Siguientes tareas (para seguir aportando después de la integración)

| # | Tarea sugerida |
|---|----------------|
| 1 | Sprites del explorador, minerales y bases en `assets/` y su uso en `render()` |
| 2 | Sonidos (recolectar, daño, aliado) y animación de los marcianos |
| 3 | Preparar `APIClient` (clase aislada, sin integrarla al motor) para la tabla de puntuaciones |
| 4 | Balanceo de niveles y pruebas de que cada nivel se puede completar |
