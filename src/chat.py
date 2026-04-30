"""
REPL conversacional para hablar con un agente desplegado en DigitalOcean
Gradient AI.

Mantiene historial de mensajes en memoria durante la sesión, así el agente
recuerda el contexto previo. El system prompt se carga desde el archivo
indicado en `SYSTEM_PROMPT_FILE` (o `prompts/system_prompt.md` por defecto)
y se prepende al historial como mensaje `role: system`.

Uso:
    python -m src.chat

    # Con un system prompt distinto:
    SYSTEM_PROMPT_FILE=prompts/examples/customer_support.md python -m src.chat

Comandos durante la sesión:
    /reset    → borra el historial y empieza una nueva conversación
                (vuelve a inyectar el system prompt actual)
    /reload   → recarga el system prompt desde disco sin perder el historial
    /tokens   → muestra cuántos mensajes acumulados van
    /exit     → sale del REPL (también funciona Ctrl+C)
"""

from __future__ import annotations

import json
import sys
from typing import Any

from openai import APIError, APIConnectionError, AuthenticationError
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from src.client import AgentConfig, build_client, load_system_prompt
from src.tools import TOOLS, dispatch_tool

# Límite de iteraciones consecutivas de tool-calling por turno. Evita que una
# tool-loop se vaya en bucle si el modelo insiste en llamar tools sin parar.
MAX_TOOL_ROUNDS = 5


# Un mensaje del historial puede llevar role/content, y además, cuando el
# assistant pide tools, `tool_calls`; cuando es una respuesta de tool,
# `tool_call_id`. Mantenemos el tipo laxo (`dict[str, Any]`) para no pelearnos
# con TypedDict opcional en todas las ramas.
Message = dict[str, Any]


WELCOME = """
# 🤖 gradient-agent-starter — REPL

Plantilla para hablar con un agente de DigitalOcean Gradient AI.
El system prompt se carga desde un archivo en `prompts/`.

Comandos:

- `/reset`  → empieza nueva conversación (re-inyecta el system prompt)
- `/reload` → recarga el system prompt desde disco
- `/tokens` → muestra mensajes acumulados
- `/exit`   → salir
"""


def initial_history(system_prompt: str) -> list[Message]:
    """Crea un historial nuevo con el system prompt al inicio (si lo hay)."""
    if system_prompt:
        return [{"role": "system", "content": system_prompt}]
    return []


def _tool_calls_to_dicts(tool_calls) -> list[dict[str, Any]]:
    """Convierte los tool_calls del SDK a dicts serializables para el historial."""
    return [
        {
            "id": tc.id,
            "type": "function",
            "function": {
                "name": tc.function.name,
                "arguments": tc.function.arguments or "",
            },
        }
        for tc in tool_calls
    ]


def agent_turn(
    client,
    model: str,
    history: list[Message],
    console: Console,
) -> str:
    """
    Ejecuta un turno completo del agente, resolviendo cualquier tool-call que
    pida el modelo antes de devolver la respuesta final de texto.

    No hace streaming (el SDK también soporta stream + tools, pero acumular
    los deltas de `tool_calls` es bastante más código y este REPL prioriza
    claridad). Mostramos un spinner mientras el modelo piensa.
    """
    for _ in range(MAX_TOOL_ROUNDS):
        with console.status("[dim]pensando…[/dim]", spinner="dots"):
            resp = client.chat.completions.create(
                model=model,
                messages=history,
                tools=TOOLS,
                tool_choice="auto",
            )
        msg = resp.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        assistant_entry: Message = {
            "role": "assistant",
            "content": msg.content or "",
        }
        if tool_calls:
            assistant_entry["tool_calls"] = _tool_calls_to_dicts(tool_calls)
        history.append(assistant_entry)

        if not tool_calls:
            return msg.content or ""

        # Ejecuta cada tool-call y deja su resultado en el historial como
        # role="tool" para que el próximo turno del modelo lo pueda leer.
        for tc in tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            console.print(
                f"[dim]🔧 {tc.function.name}({json.dumps(args, ensure_ascii=False)})[/dim]"
            )
            result = dispatch_tool(tc.function.name, args)
            history.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
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
    system_prompt = load_system_prompt(config.system_prompt_path)
    history: list[Message] = initial_history(system_prompt)

    console.print(Panel(Markdown(WELCOME), border_style="cyan"))
    console.print(
        f"[dim]system prompt: {config.system_prompt_path} "
        f"({len(system_prompt)} chars)[/dim]\n"
    )
    if not system_prompt:
        console.print(
            "[yellow]⚠️  No se encontró system prompt; el agente usa sus defaults.[/yellow]\n"
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
            console.print("[yellow]🧹 historial limpio (system prompt re-inyectado).[/yellow]\n")
            continue

        if user_input == "/reload":
            system_prompt = load_system_prompt(config.system_prompt_path)
            # También parcheamos el system message que vive en `history` —
            # si no, el cambio sólo aplica tras /reset, que es justo lo que
            # /reload intenta evitar.
            if history and history[0]["role"] == "system":
                if system_prompt:
                    history[0] = {"role": "system", "content": system_prompt}
                else:
                    history.pop(0)
            elif system_prompt:
                history.insert(0, {"role": "system", "content": system_prompt})
            console.print(
                f"[yellow]🔄 system prompt recargado ({len(system_prompt)} chars). "
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
