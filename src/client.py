"""
Cliente para hablar con un agente desplegado en DigitalOcean Gradient AI.

DO Agent Platform expone una API compatible con OpenAI Chat Completions,
así que usamos el SDK oficial de OpenAI apuntando a la URL del agente.
Esto hace el código portable: cambiar de proveedor = cambiar `base_url`.

El system prompt se inyecta en runtime desde un archivo (por defecto
`prompts/system_prompt.md`). Esto deja el comportamiento del agente
versionado en git, en vez de embebido en la configuración del agente
en DO.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, AuthenticationError

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SYSTEM_PROMPT_PATH = REPO_ROOT / "prompts" / "system_prompt.md"


@dataclass
class AgentConfig:
    """Configuración leída de variables de entorno."""

    endpoint: str
    access_key: str
    model: str
    system_prompt_path: Path

    @classmethod
    def from_env(cls) -> "AgentConfig":
        load_dotenv()
        endpoint = os.getenv("DO_AGENT_ENDPOINT")
        access_key = os.getenv("DO_AGENT_ACCESS_KEY")
        model = os.getenv("DO_AGENT_MODEL", "n/a")
        prompt_path = Path(
            os.getenv("SYSTEM_PROMPT_FILE", str(DEFAULT_SYSTEM_PROMPT_PATH))
        )

        missing = [
            name
            for name, value in [
                ("DO_AGENT_ENDPOINT", endpoint),
                ("DO_AGENT_ACCESS_KEY", access_key),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Faltan variables de entorno: {', '.join(missing)}. "
                "Revisa tu archivo .env"
            )

        return cls(
            endpoint=endpoint,  # type: ignore[arg-type]
            access_key=access_key,  # type: ignore[arg-type]
            model=model,
            system_prompt_path=prompt_path,
        )


def load_system_prompt(path: Path) -> str:
    """
    Lee el system prompt desde un archivo. Si el archivo no existe, devuelve
    una cadena vacía y el cliente queda sin system prompt (comportamiento
    por defecto del modelo).
    """
    try:
        return path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, IsADirectoryError):
        # IsADirectoryError ocurre cuando SYSTEM_PROMPT_FILE="" en .env, porque
        # Path("") se resuelve a "." (el directorio actual). Mejor caer a
        # "sin system prompt" que crashear con un traceback confuso.
        return ""


def build_client(config: AgentConfig) -> OpenAI:
    """
    Construye un cliente OpenAI apuntando al endpoint del agente de DO.

    El `base_url` debe terminar en `/api/v1/` — ese es el path que DO expone
    como compatible con la API de OpenAI Chat Completions.
    """
    base_url = config.endpoint.rstrip("/") + "/api/v1/"
    return OpenAI(base_url=base_url, api_key=config.access_key)


def build_messages(system_prompt: str, user_message: str) -> list[dict]:
    """Arma el array de mensajes con el system prompt opcional al inicio."""
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})
    return messages


def ask(
    client: OpenAI,
    model: str,
    user_message: str,
    system_prompt: str = "",
) -> str:
    """Envía un único mensaje al agente y devuelve el texto de la respuesta."""
    response = client.chat.completions.create(
        model=model,
        messages=build_messages(system_prompt, user_message),
    )
    return response.choices[0].message.content or ""


def main() -> int:
    try:
        config = AgentConfig.from_env()
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    client = build_client(config)
    system_prompt = load_system_prompt(config.system_prompt_path)

    prompt = "Hola. Preséntate en una sola frase y dime para qué sirves."

    print(f"📤 Enviando al agente ({config.endpoint})")
    print(f"   System prompt: {config.system_prompt_path}")
    if not system_prompt:
        print("   ⚠️  System prompt vacío o no encontrado, usando defaults del modelo.\n")
    else:
        print()

    try:
        answer = ask(client, config.model, prompt, system_prompt=system_prompt)
    except AuthenticationError:
        print("❌ Access key inválida. Verifica DO_AGENT_ACCESS_KEY en .env", file=sys.stderr)
        return 2
    except APIConnectionError as e:
        print(f"❌ No pude conectar al endpoint: {e}", file=sys.stderr)
        return 3
    except APIError as e:
        print(f"❌ Error del API: {e}", file=sys.stderr)
        return 4

    print("📥 Respuesta:\n")
    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
