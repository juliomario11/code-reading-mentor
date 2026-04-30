"""
Dispatch de *tools* ejecutadas del lado del cliente.

DO Gradient AI **no** respeta el parámetro `tools=[...]` de la API compatible
con OpenAI (las "Functions" de DO se configuran en la consola del agente, no
inline). Por eso `src/chat.py` usa un protocolo basado en prompt: el modelo
emite un bloque ```tool_call con `{"name": ..., "arguments": {...}}` y este
módulo lo ejecuta.

Ver `prompts/tool_protocol.md` para el contrato que ve el modelo.

Para añadir una tool nueva:
  1. Implementa la función Python (en otro archivo dentro de `src/`).
  2. Añade su despacho en `dispatch_tool`.
  3. Describe la tool en `prompts/tool_protocol.md` para que el modelo la conozca.
"""

from __future__ import annotations

from typing import Any

from src.browser_tool import browse_url


def dispatch_tool(name: str, args: dict[str, Any]) -> str:
    """Ejecuta una tool por nombre y devuelve su resultado como string."""
    if name == "browse_url":
        url = args.get("url")
        if not isinstance(url, str) or not url:
            return "Error: browse_url requiere el argumento 'url' (string)."
        return browse_url(url)
    return f"Tool desconocida: {name}"
