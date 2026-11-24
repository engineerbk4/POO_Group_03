"""Módulo APIClient — tabla de puntuaciones con fallback local JSON.

Arquitectura:
  - Encapsulamiento estricto: todos los atributos son privados (__).
  - Manejo de excepciones: ningún error de red llega al Game Loop.
  - Fallback local: si la API no responde, opera sobre scores_local.json.
  - El contrato público se expresa con métodos get_*/enviar_*.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import List, Optional

# ---------------------------------------------------------------------------
# Tipo de dato para una entrada del ranking
# ---------------------------------------------------------------------------
# { "jugador": str, "puntaje": int, "fecha": str }
Entrada = dict


# ---------------------------------------------------------------------------
# Clase principal
# ---------------------------------------------------------------------------
class APIClient:
    """Gestiona el envío y la consulta del Top de puntuaciones.

    Flujo:
        1. Intenta operar contra la API remota (URL configurable).
        2. Si falla (timeout, sin red, servidor caído) → lee/escribe el
           archivo JSON local sin relanzar la excepción.
        3. Nunca lanza excepciones al código que lo usa.
    """

    # Constantes de clase (accesibles sin instancia)
    _TOP_N: int = 10
    _TIMEOUT_SEG: int = 3
    _NOMBRE_FALLBACK: str = "scores_local.json"

    def __init__(
        self,
        url_base: str = "",
        jugador: str = "Jugador",
        ruta_fallback: Optional[str] = None,
    ) -> None:
        """
        Args:
            url_base: URL raíz de la API REST (p. ej. "https://api.mision-marte.io").
                      Puede quedar vacía; en ese caso siempre usa el fallback.
            jugador:  Nombre del jugador activo para los envíos.
            ruta_fallback: Ruta absoluta al JSON local. Si es None, se
                           coloca junto al ejecutable.
        """
        self.__url_base: str = url_base.rstrip("/")
        self.__jugador: str = jugador or "Jugador"
        self.__ultimo_error: str = ""
        self.__ranking_cache: List[Entrada] = []

        if ruta_fallback is None:
            directorio = os.path.dirname(os.path.abspath(__file__))
            ruta_fallback = os.path.join(directorio, self._NOMBRE_FALLBACK)
        self.__ruta_fallback: str = ruta_fallback

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def enviar_puntaje(self, puntaje: int) -> bool:
        """Envía el puntaje del jugador actual.

        Returns:
            True si se guardó (remoto o local), False si hubo un error
            inesperado que impidió incluso el guardado local.
        """
        if puntaje < 0:
            self.__ultimo_error = "Puntaje negativo ignorado."
            return False

        entrada: Entrada = {
            "jugador": self.__jugador,
            "puntaje": puntaje,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        # Intento remoto
        if self.__url_base:
            if self.__post_remoto(entrada):
                return True  # éxito remoto → no es necesario tocar el local

        # Fallback local
        return self.__guardar_local(entrada)

    def get_ranking(self) -> List[Entrada]:
        """Devuelve el Top-N de puntuaciones (caché → remoto → local).

        Siempre devuelve una lista (vacía si todo falla).
        """
        # Intento remoto
        if self.__url_base:
            remoto = self.__get_remoto()
            if remoto is not None:
                self.__ranking_cache = remoto
                return list(self.__ranking_cache)

        # Fallback local
        local = self.__leer_local()
        self.__ranking_cache = local
        return list(self.__ranking_cache)

    def get_ultimo_error(self) -> str:
        """Devuelve el último mensaje de error registrado (vacío si no hubo)."""
        return self.__ultimo_error

    def get_jugador(self) -> str:
        return self.__jugador

    def set_jugador(self, nombre: str) -> None:
        if nombre:
            self.__jugador = nombre

    # ------------------------------------------------------------------
    # Métodos privados — capa remota
    # ------------------------------------------------------------------
    def __post_remoto(self, entrada: Entrada) -> bool:
        """POST /scores con la entrada.  Captura toda excepción de red."""
        try:
            datos = json.dumps(entrada).encode("utf-8")
            req = urllib.request.Request(
                f"{self.__url_base}/scores",
                data=datos,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._TIMEOUT_SEG) as resp:
                ok = 200 <= resp.status < 300
                if not ok:
                    self.__ultimo_error = f"API respondió {resp.status}"
                return ok
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            self.__ultimo_error = f"[red] Sin conexión a API: {exc}"
            return False
        except Exception as exc:  # noqa: BLE001
            self.__ultimo_error = f"[red] Error inesperado en POST: {exc}"
            return False

    def __get_remoto(self) -> Optional[List[Entrada]]:
        """GET /scores?top=N.  Devuelve None si falla."""
        try:
            params = urllib.parse.urlencode({"top": self._TOP_N})
            url = f"{self.__url_base}/scores?{params}"
            with urllib.request.urlopen(url, timeout=self._TIMEOUT_SEG) as resp:
                if resp.status == 200:
                    datos = json.loads(resp.read().decode("utf-8"))
                    if isinstance(datos, list):
                        return datos[: self._TOP_N]
                self.__ultimo_error = f"API respondió {resp.status} en GET"
                return None
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            self.__ultimo_error = f"Sin conexión a API: {exc}"
            return None
        except Exception as exc:  # noqa: BLE001
            self.__ultimo_error = f"Error inesperado en GET: {exc}"
            return None

    # ------------------------------------------------------------------
    # Métodos privados — capa local (fallback JSON)
    # ------------------------------------------------------------------
    def __leer_local(self) -> List[Entrada]:
        """Lee el JSON local; devuelve lista vacía si no existe o está corrupto."""
        try:
            if not os.path.exists(self.__ruta_fallback):
                return []
            with open(self.__ruta_fallback, "r", encoding="utf-8") as f:
                datos = json.load(f)
            if not isinstance(datos, list):
                return []
            # Ordenar por puntaje descendente y limitar
            validos = [
                e for e in datos
                if isinstance(e, dict)
                and "jugador" in e
                and "puntaje" in e
                and isinstance(e["puntaje"], int)
            ]
            return sorted(validos, key=lambda e: e["puntaje"], reverse=True)[: self._TOP_N]
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            self.__ultimo_error = f"[fallback] No se pudo leer scores_local.json: {exc}"
            return []

    def __guardar_local(self, nueva: Entrada) -> bool:
        """Agrega la entrada al JSON local, reordena y limita al Top-N."""
        try:
            existentes = self.__leer_local()
            # Leer todos sin límite para no perder entradas
            try:
                if os.path.exists(self.__ruta_fallback):
                    with open(self.__ruta_fallback, "r", encoding="utf-8") as f:
                        todos = json.load(f)
                    if not isinstance(todos, list):
                        todos = []
                else:
                    todos = []
            except (json.JSONDecodeError, OSError):
                todos = []

            todos.append(nueva)
            todos = sorted(
                [
                    e for e in todos
                    if isinstance(e, dict) and "puntaje" in e
                ],
                key=lambda e: e["puntaje"],
                reverse=True,
            )
            # Guardamos todos (sin truncar) para no borrar historial
            with open(self.__ruta_fallback, "w", encoding="utf-8") as f:
                json.dump(todos, f, ensure_ascii=False, indent=2)
            self.__ranking_cache = todos[: self._TOP_N]
            return True
        except (OSError, TypeError, ValueError) as exc:
            self.__ultimo_error = f"[fallback] No se pudo guardar scores_local.json: {exc}"
            return False
