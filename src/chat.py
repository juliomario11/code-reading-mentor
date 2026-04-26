"""
REPL conversacional para hablar con el agente code-reading-mentor.

Mantiene historial de mensajes en memoria durante la sesión, así el
agente recuerda el contexto previo. Usa `rich` para render de markdown
en consola.

Uso:
    python -m src.chat

Comandos durante la sesión:
    /reset   → borra el historial y empieza una nueva conversación
    /exit    → sale del REPL (también funciona Ctrl+C)
    /tokens  → muestra cuántos mensajes acumulados van
"""

from __future__ import annotations

import sys
from typing import TypedDict

from openai import APIError, APIConnectionError, AuthenticationError
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from src.client import AgentConfig, build_client


class Message(TypedDict):
    role: str
    content: str


WELCOME = """
# 🧠 code-reading-mentor

Pega código y te lo explico. Comandos:

- `/reset`  → empieza nueva conversación
- `/tokens` → muestra mensajes acumulados
- `/exit`   → salir
"""


def stream_response(client, model: str, history: list[Message], console: Console) -> str:
    """
    Envía el historial al agente y stream-ea la respuesta token por token.
    Devuelve el texto completo para añadirlo al historial.
    """
    full_text = ""
    with console.status("[dim]pensando…[/dim]", spinner="dots"):
        stream = client.chat.completions.create(
            model=model,
            messages=history,
            stream=True,
        )

    # Una vez tengamos el stream, imprimimos token por token sin el spinner.
    console.print("\n[bold cyan]agente[/bold cyan] ", end="")
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            console.print(delta, end="", soft_wrap=True)
            full_text += delta
    console.print("\n")
    return full_text


def run_repl() -> int:
    console = Console()

    try:
        config = AgentConfig.from_env()
    except RuntimeError as e:
        console.print(f"[bold red]❌ {e}[/bold red]")
        return 1

    client = build_client(config)
    history: list[Message] = []

    console.print(Panel(Markdown(WELCOME), border_style="cyan"))

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
            history = []
            console.print("[yellow]🧹 historial limpio.[/yellow]\n")
            continue

        if user_input == "/tokens":
            console.print(f"[dim]mensajes en historial: {len(history)}[/dim]\n")
            continue

        # --- Turno normal ---
        history.append({"role": "user", "content": user_input})

        try:
            answer = stream_response(client, config.model, history, console)
        except AuthenticationError:
            console.print("[bold red]❌ access key inválida.[/bold red]")
            return 2
        except APIConnectionError as e:
            console.print(f"[bold red]❌ sin conexión: {e}[/bold red]")
            # Quitamos el último user message porque no obtuvimos respuesta.
            history.pop()
            continue
        except APIError as e:
            console.print(f"[bold red]❌ API error: {e}[/bold red]")
            history.pop()
            continue

        # Render del markdown completo de forma bonita al final.
        # (Lo de arriba imprimió tokens en bruto; esto lo "rehace" formateado.)
        console.rule(style="dim")
        console.print(Markdown(answer))
        console.rule(style="dim")

        history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    sys.exit(run_repl())