"""
Analizador de sentimientos: ejemplo de uso del agente como clasificador.

Lee un CSV con columnas (id, texto, sentimiento_esperado), le pide al agente
que clasifique cada `texto` como positivo / neutral / negativo, y compara el
resultado con la etiqueta esperada del dataset.

El prompt de clasificación se carga desde
`prompts/examples/sentiment_classifier.md` y se inyecta como mensaje
`role: system`. Esto demuestra el patrón general del repo: el comportamiento
del agente para una tarea concreta vive en un archivo del repo, no en la UI
de DigitalOcean.

Uso:
    python -m src.sentiment                         # usa data/comentarios_codigo.csv
    python -m src.sentiment path/al/otro.csv        # CSV alternativo
    python -m src.sentiment --out resultados.csv    # guarda predicciones

El CSV de entrada debe tener al menos la columna `texto`. Si además tiene
`sentimiento_esperado`, se imprime un pequeño reporte de accuracy.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable

from openai import APIConnectionError, APIError, AuthenticationError

from src.client import AgentConfig, build_client, load_system_prompt

ETIQUETAS = ("positivo", "neutral", "negativo")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "data" / "comentarios_codigo.csv"
CLASSIFIER_PROMPT_PATH = REPO_ROOT / "prompts" / "examples" / "sentiment_classifier.md"


def leer_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalizar_etiqueta(respuesta: str) -> str:
    """Extrae la primera etiqueta válida que aparezca en la respuesta del agente."""
    limpio = respuesta.strip().lower()
    for etiqueta in ETIQUETAS:
        if etiqueta in limpio:
            return etiqueta
    return "desconocido"


def clasificar(
    client,
    model: str,
    filas: Iterable[dict[str, str]],
    system_prompt: str,
) -> list[dict[str, str]]:
    resultados: list[dict[str, str]] = []
    for fila in filas:
        texto = fila.get("texto", "").strip()
        if not texto:
            continue

        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": texto})

        respuesta = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
        bruto = respuesta.choices[0].message.content or ""
        prediccion = normalizar_etiqueta(bruto)

        resultados.append(
            {
                "id": fila.get("id", ""),
                "texto": texto,
                "sentimiento_esperado": fila.get("sentimiento_esperado", ""),
                "sentimiento_predicho": prediccion,
                "respuesta_bruta": bruto.strip(),
            }
        )
    return resultados


def imprimir_reporte(resultados: list[dict[str, str]]) -> None:
    total = len(resultados)
    if total == 0:
        print("No hay filas para reportar.")
        return

    con_esperado = [r for r in resultados if r["sentimiento_esperado"]]
    aciertos = sum(
        1
        for r in con_esperado
        if r["sentimiento_predicho"] == r["sentimiento_esperado"]
    )

    print(f"\nTotal clasificado: {total}")
    if con_esperado:
        accuracy = aciertos / len(con_esperado) * 100
        print(f"Con etiqueta esperada: {len(con_esperado)}")
        print(f"Aciertos: {aciertos} ({accuracy:.1f}%)")

        errores = [
            r for r in con_esperado
            if r["sentimiento_predicho"] != r["sentimiento_esperado"]
        ]
        if errores:
            print("\nErrores:")
            for r in errores:
                print(
                    f"  - [{r['id']}] esperado={r['sentimiento_esperado']} "
                    f"predicho={r['sentimiento_predicho']} :: {r['texto'][:80]}"
                )


def guardar_csv(resultados: list[dict[str, str]], salida: Path) -> None:
    if not resultados:
        return
    with salida.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(resultados[0].keys()))
        writer.writeheader()
        writer.writerows(resultados)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv",
        nargs="?",
        default=str(DEFAULT_CSV),
        help="Ruta al CSV con comentarios (default: data/comentarios_codigo.csv)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Ruta opcional donde guardar las predicciones en CSV.",
    )
    args = parser.parse_args(argv)

    entrada = Path(args.csv)
    if not entrada.exists():
        print(f"❌ No encontré el archivo {entrada}", file=sys.stderr)
        return 1

    try:
        config = AgentConfig.from_env()
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    client = build_client(config)
    system_prompt = load_system_prompt(CLASSIFIER_PROMPT_PATH)
    if not system_prompt:
        print(
            f"❌ No se encontró el prompt de clasificación en {CLASSIFIER_PROMPT_PATH}",
            file=sys.stderr,
        )
        return 1

    filas = leer_csv(entrada)
    print(f"📥 Cargadas {len(filas)} filas desde {entrada}")
    print(f"   Prompt: {CLASSIFIER_PROMPT_PATH}")

    try:
        resultados = clasificar(client, config.model, filas, system_prompt)
    except AuthenticationError:
        print("❌ Access key inválida. Verifica DO_AGENT_ACCESS_KEY.", file=sys.stderr)
        return 2
    except APIConnectionError as e:
        print(f"❌ Sin conexión al agente: {e}", file=sys.stderr)
        return 3
    except APIError as e:
        print(f"❌ Error del API: {e}", file=sys.stderr)
        return 4

    imprimir_reporte(resultados)

    if args.out:
        guardar_csv(resultados, Path(args.out))
        print(f"\n💾 Predicciones guardadas en {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
