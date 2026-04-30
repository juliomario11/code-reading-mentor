"""
REPL conversacional para hablar con un agente desplegado en DigitalOcean
Gradient AI.

Mantiene historial de mensajes en memoria durante la sesión, así el agente
recuerda el contexto previo. El system prompt se carga desde el archivo
indicado en `SYSTEM_PROMPT_FILE` (o `prompts/system_prompt.md` por defecto)
y se prepende al historial como mensaje `role: system`.

## Tool-calling en DO Agents

La DO Agent Platform **ignora** el parámetro `tools=[...]` de la API compatible
con OpenAI (las "Functions" de DO se configuran en la consola, no inline).
Para mantener tool-calling del lado del cliente — donde vive `browse_url` con
Playwright — usamos un protocolo basado en prompt:

1. Se inyecta en el system prompt un bloque "Herramientas disponibles" que le
   enseña al modelo a responder con un bloque:

       ```tool_call
       {"name": "browse_url", "arguments": {"url": "https://..."}}
       ```

2. `agent_turn` detecta ese bloque, ejecuta la tool vía `dispatch_tool`,
   inyecta el resultado como un mensaje `role="user"` con prefijo
   `[TOOL_RESULT ...]` y vuelve a preguntar al modelo hasta obtener texto
   normal.

Uso:
    python -m src.chat

    # Con un system prompt distinto:
    SYSTEM_PROMPT_FILE=prompts/examples/customer_support.md python -m src.chat

Comandos durante la sesión:
    /reset    → borra el historial y empieza una nueva conversación
                (vuelve a inyectar el system prompt actual + protocolo de tools)
    /reload   → recarga el system prompt desde disco sin perder el historial
    /tokens   → muestra cuántos mensajes acumulados van
    /exit     → sale del REPL (también funciona Ctrl+C)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from openai import APIError, APIConnectionError, AuthenticationError
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from src.client import AgentConfig, build_client, load_system_prompt
from src.tools import dispatch_tool

# Límite de iteraciones consecutivas de tool-calling por turno. Evita que una
# tool-loop se vaya en bucle si el modelo insiste en llamar tools sin parar.
MAX_TOOL_ROUNDS = 5

# Protocolo que se concatena al system prompt del usuario para enseñarle al
# modelo a emitir tool_calls como bloques de código que podemos parsear.
TOOL_PROTOCOL_PATH = (
    Path(__file__).resolve().parent.parent / "prompts" / "tool_protocol.md"
)


# Historial flexible: puede llevar role/content y, en el caso de tool-results,
# también lo pasamos como role="user" con prefijo identificable.
Message = dict[str, Any]


WELCOME = """
# 🤖 gradient-agent-starter — REPL

Plantilla para hablar con un agente de DigitalOcean Gradient AI.
El system prompt se carga desde un archivo en `prompts/`, y se le concatena
el protocolo de `browse_url` desde `prompts/tool_protocol.md`.

Comandos:

- `/reset`  → empieza nueva conversación (re-inyecta el system prompt)
- `/reload` → recarga el system prompt desde disco
- `/tokens` → muestra mensajes acumulados
- `/exit`   → salir
"""


def load_tool_protocol() -> str:
    """Lee el protocolo de tool-calling que se concatena al system prompt."""
    try:
        return TOOL_PROTOCOL_PATH.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, IsADirectoryError):
        return ""


def compose_system_prompt(user_prompt: str, tool_protocol: str) -> str:
    """
    Concatena el system prompt del usuario con el protocolo de tool-calling.
    Si alguno está vacío, devuelve solo el otro.
    """
    parts = [p for p in (user_prompt, tool_protocol) if p]
    return "\n\n---\n\n".join(parts)


def initial_history(system_prompt: str) -> list[Message]:
    """Crea un historial nuevo con el system prompt al inicio (si lo hay)."""
    if system_prompt:
        return [{"role": "system", "content": system_prompt}]
    return []


# Detecta bloques ```tool_call ... ``` con un JSON dentro. Tolerante a espacios
# y saltos de línea adicionales. Usa re.DOTALL para que `.` matchee newlines.
TOOL_CALL_RE = re.compile(
    r"```tool_call\s*(\{.*?\})\s*```",
    re.DOTALL,
)


def parse_tool_call(content: str) -> dict[str, Any] | None:
    """Si el contenido del asistente es una tool-call, devuelve el dict parseado."""
    match = TOOL_CALL_RE.search(content)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or "name" not in parsed:
        return None
    return parsed


def agent_turn(
    client,
    model: str,
    history: list[Message],
    console: Console,
) -> str:
    """
    Ejecuta un turno completo del agente, resolviendo tool-calls emitidos vía
    el protocolo ```tool_call hasta que el modelo responda con texto normal.
    """
    for _ in range(MAX_TOOL_ROUNDS):
        with console.status("[dim]pensando…[/dim]", spinner="dots"):
            resp = client.chat.completions.create(
                model=model,
                messages=history,
            )
        content = resp.choices[0].message.content or ""
        history.append({"role": "assistant", "content": content})

        tool_call = parse_tool_call(content)
        if tool_call is None:
            return content

        name = tool_call.get("name", "")
        args = tool_call.get("arguments", {}) or {}
        if not isinstance(args, dict):
            args = {}
        console.print(
            f"[dim]🔧 {name}({json.dumps(args, ensure_ascii=False)})[/dim]"
        )
        result = dispatch_tool(name, args)

        # DO Gradient no soporta role="tool" fiablemente; devolvemos el
        # resultado como un mensaje de usuario con un marcador claro para que
        # el modelo sepa que viene del runtime, no del humano.
        history.append(
            {
                "role": "user",
                "content": f"[TOOL_RESULT name={name}]\n{result}",
            }
        )

    return "⚠️  Se alcanzó el límite de tool-calls por turno sin respuesta final."


def run_repl() -> int:
    console = Console()

    try:
        config = AgentConfig.from_env()
    except RuntimeError as e:
        console.print(f"[bold red]❌ {e}[/bold red]")
        return 1

    client = build_client(config)
    user_prompt = load_system_prompt(config.system_prompt_path)
    tool_protocol = load_tool_protocol()
    system_prompt = compose_system_prompt(user_prompt, tool_protocol)
    history: list[Message] = initial_history(system_prompt)

    console.print(Panel(Markdown(WELCOME), border_style="cyan"))
    console.print(
        f"[dim]system prompt: {config.system_prompt_path} "
        f"({len(user_prompt)} chars) + tool protocol ({len(tool_protocol)} chars)[/dim]\n"
    )
    if not user_prompt:
        console.print(
            "[yellow]⚠️  No se encontró system prompt del usuario; "
            "solo se cargó el protocolo de tools.[/yellow]\n"
        )

    while True:
        try:
            user_input = Prompt.ask("[bold green]tú[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]hasta luego.[/dim]")
            return 0

        if not user_input:
            continue

        # --- Comandos especiales ---
        if user_input == "/exit":
            console.print("[dim]hasta luego.[/dim]")
            return 0

        if user_input == "/reset":
            history = initial_history(system_prompt)
            console.print(
                "[yellow]🧹 historial limpio (system prompt re-inyectado).[/yellow]\n"
            )
            continue

        if user_input == "/reload":
            user_prompt = load_system_prompt(config.system_prompt_path)
            tool_protocol = load_tool_protocol()
            system_prompt = compose_system_prompt(user_prompt, tool_protocol)
            if history and history[0]["role"] == "system":
                if system_prompt:
                    history[0] = {"role": "system", "content": system_prompt}
                else:
                    history.pop(0)
            elif system_prompt:
                history.insert(0, {"role": "system", "content": system_prompt})
            console.print(
                f"[yellow]🔄 system prompt recargado "
                f"({len(user_prompt)} chars usuario + {len(tool_protocol)} chars tools). "
                "Se aplicará al próximo turno.[/yellow]\n"
            )
            continue

        if user_input == "/tokens":
            console.print(f"[dim]mensajes en historial: {len(history)}[/dim]\n")
            continue

        # --- Turno normal ---
        history.append({"role": "user", "content": user_input})

        try:
            answer = agent_turn(client, config.model, history, console)
        except AuthenticationError:
            console.print("[bold red]❌ access key inválida.[/bold red]")
            return 2
        except APIConnectionError as e:
            console.print(f"[bold red]❌ sin conexión: {e}[/bold red]")
            history.pop()
            continue
        except APIError as e:
            console.print(f"[bold red]❌ API error: {e}[/bold red]")
            history.pop()
            continue

        console.rule(style="dim")
        console.print(Markdown(answer))
        console.rule(style="dim")


if __name__ == "__main__":
    sys.exit(run_repl())
