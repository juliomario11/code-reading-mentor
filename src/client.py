"""
Cliente para hablar con el agente code-reading-mentor en DO Gradient AI.

DO Agent Platform expone una API compatible con OpenAI Chat Completions,
así que usamos el SDK oficial de OpenAI apuntando a la URL del agente.
Esto hace el código portable: cambiar de proveedor = cambiar base_url.
"""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, AuthenticationError


@dataclass
class AgentConfig:
    """Configuración leída de variables de entorno."""

    endpoint: str
    access_key: str
    model: str

    @classmethod
    def from_env(cls) -> "AgentConfig":
        load_dotenv()
        endpoint = os.getenv("DO_AGENT_ENDPOINT")
        access_key = os.getenv("DO_AGENT_ACCESS_KEY")
        model = os.getenv("DO_AGENT_MODEL", "n/a")

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

        # type: ignore  → ya validamos que no son None
        return cls(endpoint=endpoint, access_key=access_key, model=model)


def build_client(config: AgentConfig) -> OpenAI:
    """
    Construye un cliente OpenAI apuntando al endpoint del agente de DO.

    El base_url debe terminar en /api/v1/ — ese es el path que DO expone
    como compatible con la API de OpenAI Chat Completions.
    """
    base_url = config.endpoint.rstrip("/") + "/api/v1/"
    return OpenAI(base_url=base_url, api_key=config.access_key)


def ask(client: OpenAI, model: str, user_message: str) -> str:
    """Envía un único mensaje al agente y devuelve el texto de la respuesta."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.choices[0].message.content or ""


def main() -> int:
    try:
        config = AgentConfig.from_env()
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    client = build_client(config)

    prompt = (
        "Hola. Como prueba inicial, explícame qué hace este código:\n\n"
        "```python\n"
        "def squares(n):\n"
        "    return [x * x for x in range(n)]\n"
        "```"
    )

    print(f"📤 Enviando al agente ({config.endpoint})...\n")

    try:
        answer = ask(client, config.model, prompt)
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