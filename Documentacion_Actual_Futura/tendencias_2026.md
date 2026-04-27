# Tendencias 2025–2026 en agentes de IA

Resumen de lo que se está haciendo a marzo–abril 2026 en r/LocalLLaMA, r/MachineLearning,
X y blogs de ingeniería. Cada punto enlaza la fuente con su fecha.

> **Para qué leer esto.** Para saber por dónde extender este starter más allá de "un agente
> con system prompt". Cada sección termina con una **idea concreta** de qué se podría agregar
> al repo.

## 1. El "agent harness" se estandarizó

Anthropic, OpenAI y Google convergieron en una misma arquitectura para agentes autónomos:

- **Brain** — modelo + bucle de razonamiento.
- **Hands** — ejecución sandboxed (filesystem, shell, browser).
- **Session** — memoria persistente entre runs.

Lo que antes era "chatbot" pasó a ser "agente que controla tu computadora". Anthropic shipeó
un desktop agent con remote control desde móvil; OpenAI convirtió Codex en una plataforma de
computer-use; Google publicó un stack de 6 protocolos de interoperabilidad.

📎 Fuente: [Komissarov — The Month AI Agents Took the Wheel (abr 2026)](https://medium.com/@olegkomissarov/the-month-ai-agents-took-the-wheel-everything-that-matters-from-march-april-2026-512934123559)

**Idea para extender el starter:** agregar un módulo que le dé al agente acceso controlado a
herramientas (filesystem read-only, shell sandbox, browser headless) detrás de un sandbox
explícito y memoria persistente entre sesiones (SQLite local, por ejemplo).

## 2. MCP (Model Context Protocol) como estándar de tooling

MCP cruzó **97 millones de instalaciones** al 25 mar 2026 — la curva de adopción más rápida
en historia de infra de IA. Kubernetes tomó 4 años para llegar a algo comparable; MCP lo hizo
en ~16 meses.

- Anthropic donó MCP a la **Linux Foundation / Agentic AI Foundation** el 9 dic 2025.
- OpenAI, Google, AWS, Microsoft, Cloudflare y Bloomberg están como co-founders / platinum.
- Tres primitives: **Tools** (funciones invocables), **Resources** (datos), **Prompts** (templates).
- Sobre JSON-RPC 2.0. Soporta STDIO local y HTTP+SSE remoto.
- Resuelve el problema **N×M** de integraciones: 1 MCP server = funciona con todos los agentes
  compatibles. Pasa de N×M a N+M.

📎 Fuentes:
- [byteiota — MCP hits 97M installs (abr 2026)](https://byteiota.com/model-context-protocol-97m-installs-standard-wins-2/)
- [Sitepoint — MCP developer integration guide (abr 2026)](https://www.sitepoint.com/mcp-model-context-protocol-complete-developer-integration-guide/)

**Idea para extender el starter:** agregar `src/mcp_server.py` que exponga las funciones de
este repo (clasificador de sentimientos, etc.) como un MCP server, y configurar el agente
para que las consuma. Con eso pasas de "agente que solo habla" a "agente que puede invocar
funciones de tu código". Ver [`agentes_vs_mcp.md`](./agentes_vs_mcp.md) para la diferencia
entre los dos.

## 3. Híbrido RAG + fine-tuning + multi-agent (no son rivales)

La narrativa de "RAG vs fine-tuning" murió en 2026. El estándar enterprise actual es:

- **Multi-agent workflows** para routing.
- **RAG** para grounding factual.
- **Fine-tuning** sólo para especialización profunda de estilo o lógica.

Reportes de reducción de hallucinations de hasta **~85%** vs baseline cuando RAG está bien
diseñado.

📎 Fuente: [dev.to / endevsols — RAG vs Fine-Tuning vs Prompting 2026 strategic guide (abr 2026)](https://dev.to/muzammil_endevsols/rag-vs-fine-tuning-vs-prompting-2026-strategic-guide-169l)

**Idea para extender el starter:** DO Gradient AI ya cubre el lado RAG con
[Knowledge Bases](https://docs.digitalocean.com/products/genai-platform/concepts/knowledge-bases/).
Subir documentación tuya, attacharla al agente, y comparar respuestas con/sin la KB es un
ejercicio de bajo costo y alto impacto.

## 4. Fine-tuning local como "edge competitiva"

Tesis dominante en r/LocalLLaMA: modelos pequeños bien especializados (LoRA + Unsloth) superan
en la práctica a generalistas grandes para casos concretos.

Stack de moda en los hilos:

- **Unsloth** — kernels Triton hechos a mano. Para Gemma 4 E2B/E4B fine-tunea con **8GB VRAM**,
  ~1.5x más rápido y 60% menos VRAM que setups FA2 base.
- **Axolotl** — config-driven, reproducible.
- **LoRA / QLoRA** — método PEFT estándar, entrena solo adapters de bajo rango.

Caveat realista del top comment del thread: si puedes generar tu dataset sintético es porque
ya tienes un modelo que hace lo que querías → muchas veces es mejor usar ese modelo
directamente que destilarlo. Aplica salvo destilación legítima.

📎 Fuentes:
- [r/LocalLLaMA — local fine-tuning thread (mar 2026)](https://www.reddit.com/r/LocalLLaMA/comments/1rwj60g/local_finetuning_will_be_the_biggest_competitive/)
- [insights.marvin-42 — Gemma 4 fine-tuning con 8GB VRAM (abr 2026)](https://insights.marvin-42.com/articles/rlocalllama-pushes-gemma-4-local-fine-tuning-with-an-8gb-vram-guide-and-bug-fixes)

**Idea para extender el starter:** en este repo no fine-tuneamos, pero
[`fine_tuning.md`](./fine_tuning.md) documenta cuándo conviene y qué stack usar.

## 5. Multi-agentes en producción para operaciones

Caso real: 17 semanas operando un negocio entero con 7 agentes Claude autónomos.

- 1,053 emails personalizados enviados solos.
- 192 ciclos de dispatch.
- $220/mes total de costo.
- **Cero fallos catastróficos** porque hubo human-in-the-loop gates en los pasos riesgosos.

Hallazgo no programado: los agentes empezaron a corregirse entre sí. El finance flagea
overclaims del marketing, el research corrige targeting de sales, el content cross-referencia
research antes de redactar.

📎 Fuente: [prodSens — 17 weeks running 7 autonomous agents (abr 2026)](https://prodsens.live/2026/04/15/17-weeks-running-7-autonomous-ai-agents-in-production-real-lessons-and-real-numbers/)

**Idea para extender el starter:** la siguiente versión natural del repo es un orquestador
mínimo de 2–3 agentes con roles distintos (cada uno con su system prompt) y un human-in-the-loop
gate antes de acciones irreversibles.

## 6. Plan-and-Act y planning explícito

[Plan-and-Act](https://arxiv.org/abs/2503.09572) (ICML 2025) propone separar **Planner**
(planes estructurados de alto nivel) de **Executor** (acciones concretas). SOTA en WebArena-Lite
(57.58%) y best text-only en WebVoyager (81.36%).

📎 Fuente: [arXiv 2503.09572](https://arxiv.org/abs/2503.09572) ·
[HF model](https://huggingface.co/xTRam1/plan-and-act-planner-70b)

**Idea para extender el starter:** dividir el agente en dos modos — uno que devuelve un plan
estructurado (JSON con pasos) y otro que ejecuta cada paso. Encaja con el "agent harness"
como subsistema de planeación dentro del *brain*. Ver detalles en [`fine_tuning.md`](./fine_tuning.md).

## Tabla de fuentes (orden de utilidad)

| Tema                          | Lectura                                                                                                                                       | Fecha    |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| Estado del arte de agentes    | [Komissarov: agents took the wheel](https://medium.com/@olegkomissarov/the-month-ai-agents-took-the-wheel-everything-that-matters-from-march-april-2026-512934123559) | abr 2026 |
| MCP adoption                  | [byteiota: 97M installs](https://byteiota.com/model-context-protocol-97m-installs-standard-wins-2/)                                          | abr 2026 |
| MCP integración               | [Sitepoint: developer guide](https://www.sitepoint.com/mcp-model-context-protocol-complete-developer-integration-guide/)                     | abr 2026 |
| Multi-agent en prod           | [prodSens: 17 weeks running 7 agents](https://prodsens.live/2026/04/15/17-weeks-running-7-autonomous-ai-agents-in-production-real-lessons-and-real-numbers/) | abr 2026 |
| RAG vs fine-tuning vs prompt  | [endevsols: 2026 strategic guide](https://dev.to/muzammil_endevsols/rag-vs-fine-tuning-vs-prompting-2026-strategic-guide-169l)               | abr 2026 |
| Fine-tuning local stack       | [r/LocalLLaMA: local fine-tuning thread](https://www.reddit.com/r/LocalLLaMA/comments/1rwj60g/local_finetuning_will_be_the_biggest_competitive/) | mar 2026 |
| Plan-and-Act                  | [arXiv 2503.09572](https://arxiv.org/abs/2503.09572) · [HF model](https://huggingface.co/xTRam1/plan-and-act-planner-70b)                   | 2025     |
