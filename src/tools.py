"""
Registro de *tools* (function calling) disponibles para el agente.

- `TOOLS` es la lista de schemas que se pasa a `client.chat.completions.create(tools=...)`.
- `dispatch_tool(name, args)` ejecuta la tool por nombre y devuelve su resultado
  como string (los resultados se inyectan en el historial con role="tool").

Para añadir una tool nueva:
  1. Implementa la función Python (en otro archivo dentro de `src/`).
  2. Define el schema OpenAI-style aquí.
  3. Añade el schema a `TOOLS` y el despacho a `dispatch_tool`.
"""

from __future__ import annotations

from typing import Any

from src.browser_tool import browse_url


BROWSE_URL_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "browse_url",
        "description": (
            "Visita una URL específica y extrae su contenido como texto plano. "
            "Úsala cuando el usuario pida información que vive en la web "
            "(precios, tasas de cambio, titulares, datos de una página concreta) "
            "o cuando te pida 'buscar en la web'. Si no sabes la URL exacta, "
            "usa una búsqueda tipo https://duckduckgo.com/?q=<consulta> o "
            "https://www.google.com/search?q=<consulta> y luego llama browse_url "
            "sobre ese resultado."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": (
                        "URL completa a visitar, incluyendo el esquema "
                        "(ej: https://www.bancolombia.com/tasas)."
                    ),
                }
            },
            "required": ["url"],
        },
    },
}


TOOLS: list[dict[str, Any]] = [BROWSE_URL_TOOL]


def dispatch_tool(name: str, args: dict[str, Any]) -> str:
    """Ejecuta una tool por nombre y devuelve su resultado como string."""
    if name == "browse_url":
        return browse_url(args["url"])
    return f"Tool desconocida: {name}"
