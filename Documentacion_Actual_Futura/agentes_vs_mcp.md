# Agentes vs. MCP: ¿qué es cada uno y cuándo uso qué?

Una de las confusiones más comunes para alguien que recién entra al espacio de IA aplicada en
2026 es no saber dónde termina un "agente" y dónde empieza un "MCP server". Spoiler:
**no compiten, se complementan**. Esta página explica las dos piezas, sus diferencias y cómo
encajan.

## TL;DR

> Un **agente** es la parte que **decide qué hacer**. Un **MCP server** es la parte que
> **expone capacidades** que el agente puede usar.

Si lo piensas como un humano sentado en una computadora:

- El **agente** es el cerebro: razona, decide, planifica.
- Los **MCP servers** son las herramientas a su alcance: el navegador, el terminal, el
  CRM, la base de datos.

Sin agente, las herramientas no se usan solas. Sin herramientas, el agente solo puede hablar.

## Definiciones

### Agente

Un programa que combina:

1. Un **modelo de lenguaje** (Llama, Claude, GPT-4, etc.).
2. Un **system prompt** que define personalidad, objetivos y reglas.
3. Un **bucle de control** que recibe input del usuario, decide qué responder, y opcionalmente
   invoca herramientas externas.

Este repo hoy es exactamente eso: un agente conversacional sobre DigitalOcean Gradient AI,
con el system prompt en `prompts/system_prompt.md` y el bucle de control en `src/chat.py`.

### MCP server

**MCP** (Model Context Protocol) es un **estándar abierto** publicado por Anthropic en 2024
y donado a la Linux Foundation en diciembre 2025. Un MCP server es un proceso (local o remoto)
que expone tres tipos de capacidades a cualquier agente compatible:

- **Tools** — funciones que el agente puede invocar (`buscar_cliente(id)`, `enviar_email(...)`).
- **Resources** — datos que el agente puede leer (un archivo, un endpoint, una colección).
- **Prompts** — templates reutilizables.

El protocolo subyacente es **JSON-RPC 2.0** sobre STDIO (local) o HTTP+SSE (remoto). Lo que
hace MCP poderoso no es la tecnología — JSON-RPC existe desde 2010 — sino que **todos los
agentes grandes ya lo soportan**: Claude, ChatGPT, Gemini, Cursor, Windsurf, etc. Eso resuelve
el problema **N×M** de integraciones (cada agente hablándole a cada herramienta) y lo convierte
en **N+M**.

Para abril 2026, MCP cruzó **97 millones de instalaciones** — más rápido que cualquier infra
de IA en historia.

## La diferencia, en una tabla

| Aspecto              | Agente                                              | MCP server                                            |
| -------------------- | --------------------------------------------------- | ----------------------------------------------------- |
| **Qué es**           | Un programa que toma decisiones con un LLM.         | Un proceso que expone funciones/datos a agentes.      |
| **Quién lo invoca**  | El usuario (humano o sistema).                      | El agente, dinámicamente, durante la conversación.    |
| **Stateful**         | Sí — mantiene historial de conversación.            | Generalmente no — request → response.                 |
| **Razona**           | Sí. Es la parte "lista".                            | No. Solo expone capacidades.                          |
| **Standalone útil**  | Sí — sirve solo para chatear.                       | No — necesita un agente que lo use.                   |
| **Estandarización**  | Cada framework define su propio formato.            | Estándar abierto (Linux Foundation).                  |
| **Cambia con el LLM**| Sí — cambia el modelo, cambia el agente.            | No — el server es agnóstico al LLM.                   |
| **Intercambiable**   | Difícil — está acoplado al stack.                   | Trivial — un server sirve para todos los agentes.     |

## Cuándo necesitas cada uno

### Solo necesitas un **agente** si...

- Tu caso de uso es 100% texto: clasificación, resumen, generación, conversación.
- No hay acciones que el agente tenga que ejecutar en el mundo real.
- Los datos que el agente necesita caben en el contexto (o se pueden meter via RAG).

Ejemplo: el clasificador de sentimientos de este repo. No necesita herramientas — solo recibe
texto, devuelve etiqueta.

### Necesitas un **MCP server** además del agente si...

- El agente debe **ejecutar acciones**: enviar email, crear ticket, modificar archivo,
  consultar base de datos.
- El agente debe **leer datos en vivo** que cambian todo el tiempo (precios, inventario,
  estado de servicios).
- Quieres que **otros agentes** (Claude Desktop, Cursor, etc.) puedan usar las mismas
  capacidades sin re-implementarlas.

Ejemplo: un agente de soporte técnico que tiene que mirar el ticket del usuario en Zendesk.
El agente decide cuándo mirar; el MCP server lo expone.

## Cómo se ven juntos

```
┌──────────┐                                ┌────────────────────┐
│  user    │ ── 1. mensaje texto ──>        │   Agent harness    │
└──────────┘ <── 5. respuesta texto ──      │  ┌──────────────┐  │
                                            │  │  Brain (LLM) │  │
                                            │  │  + prompt    │  │
                                            │  └──────────────┘  │
                                            │         │          │
                                            │  2. ¿necesito tool?│
                                            │         ▼          │
                                            │  3. tool_call(...) │
                                            └─────────┬──────────┘
                                                      │
                                                      ▼
                                            ┌────────────────────┐
                                            │  MCP server        │
                                            │  (tu base de datos,│
                                            │   tu CRM, lo que   │
                                            │   sea)             │
                                            └─────────┬──────────┘
                                                      │
                                                      ▼
                                                4. tool_result
                                                  (de vuelta al
                                                   brain como
                                                   contexto extra)
```

El bucle 2→3→4 puede repetirse varias veces antes de que el agente responda al usuario.

## Para este repo

Hoy, `gradient-agent-starter` es **solo un agente**. La extensión natural es:

1. Crear un MCP server con una capacidad simple (por ejemplo, "consultar la fila N del CSV
   de comentarios").
2. Configurar el agente de DO para que lo use vía un `Tool` que invoque ese MCP.
3. Comparar: el agente solo (sin MCP) tiene que pegar el CSV en el prompt; con MCP puede
   pedir filas individuales.

**Recurso para arrancar:** [Sitepoint — MCP Developer Integration Guide (abr 2026)](https://www.sitepoint.com/mcp-model-context-protocol-complete-developer-integration-guide/)
muestra cómo armar un MCP server en Python con SDK oficial, conectarlo a un cliente Node.js
y consumirlo desde un frontend React.

## Mitos rápidos

- **"MCP reemplaza function calling de OpenAI."** — No. MCP es **una manera** de exponer
  funciones; function calling de OpenAI es el mecanismo del lado del modelo. Son capas
  distintas.
- **"Si tengo agente no necesito MCP."** — Cierto, si no necesitas tools. Falso, si necesitas
  conectarte a sistemas externos.
- **"MCP es solo para Claude."** — Falso desde 2025. ChatGPT, Gemini, Cursor, Windsurf y
  decenas más ya lo hablan.
- **"Un MCP server es un microservicio."** — Más o menos. Conceptualmente sí, pero con un
  contrato declarado y estandarizado.

## Lecturas recomendadas

- [byteiota — MCP hits 97M installs (abr 2026)](https://byteiota.com/model-context-protocol-97m-installs-standard-wins-2/) — contexto de adopción.
- [Sitepoint — MCP developer integration guide (abr 2026)](https://www.sitepoint.com/mcp-model-context-protocol-complete-developer-integration-guide/) — tutorial práctico.
- [arya.ai — Comparing LLM fine-tuning, RAG, and MCP (jul 2025)](https://arya.ai/blog/llm-fine-tuning-vs-rag-vs-mcp) — cómo encaja MCP frente a las otras dos técnicas.
