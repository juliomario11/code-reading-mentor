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

import sys
from typing import TypedDict

from openai import APIError, APIConnectionError, AuthenticationError
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from src.client import AgentConfig, build_client, load_system_prompt


class Message(TypedDict):
    role: str
    content: str


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
            answer = stream_response(client, config.model, history, console)
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

        history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    sys.exit(run_repl())
