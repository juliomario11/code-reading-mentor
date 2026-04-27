# Preguntas para explorar

Lista curada de preguntas que vale la pena hacerse cuando sales del "hello world" de un
agente. Cada una con un punto de partida concreto.

> Esto **no** es un test. Es para que tengas hilos de los que tirar cuando el repo te quede
> chico.

## Conceptos de base

### 1. ¿Qué es exactamente el "system prompt" y por qué tiene un rol distinto al "user prompt"?

El modelo trata el `role: system` como instrucciones de mayor prioridad / mayor estabilidad
que los mensajes `role: user`. En la práctica, lo que pones en el system prompt influye
**todo** el turno: persistirá aunque el usuario diga "ignora todas las instrucciones
anteriores" — de ahí el patrón de tener instrucciones críticas (de seguridad, formato, tono)
en el system y no en el user.

📎 Mira: [`src/client.py`](../src/client.py), función `build_messages` — verás cómo se inyecta.

### 2. ¿Por qué Plan-and-Act separa Planner de Executor en lugar de usar un solo modelo?

Hipótesis del paper: los LLMs no están entrenados nativamente para producir planes
ejecutables, pero sí pueden ejecutar pasos individuales. Separar permite:

- Fine-tunear sólo al Planner (más barato).
- Cambiar el Executor sin tocar el Planner.
- Validar el plan antes de ejecutar (human-in-the-loop natural).

Pregunta retadora: **¿en qué casos un solo modelo te alcanza?** Hint: tareas donde el plan
es trivial (1-2 pasos).

📎 Mira: [`fine_tuning.md`](./fine_tuning.md) y el [paper](https://arxiv.org/abs/2503.09572).

### 3. ¿Cuándo conviene fine-tunear vs. RAG vs. mejor prompting?

| Síntoma                                       | Probable solución      |
| --------------------------------------------- | ---------------------- |
| El modelo ignora instrucciones de formato     | Mejor prompt           |
| El modelo no conoce mis docs internas         | RAG                    |
| El modelo no responde con el tono que quiero  | Few-shot en prompt → fine-tuning solo si few-shot no escala |
| El modelo es lento / caro                     | Fine-tunear modelo más pequeño |
| El modelo no puede ejecutar acciones          | MCP / tools — no fine-tuning |

**Pregunta retadora:** si fine-tunear un modelo pequeño te da el resultado del modelo grande
genérico a 1/10 del costo, ¿en qué métrica perdiste? Hint: capacidades de razonamiento
no-relacionadas al fine-tune.

📎 Mira: [`tendencias_2026.md`](./tendencias_2026.md) §3, [`fine_tuning.md`](./fine_tuning.md).

### 4. ¿Por qué un MCP server **no** es lo mismo que un microservicio normal?

Conceptualmente, un MCP server **es** un microservicio. La diferencia está en que MCP define
un **contrato declarado** que cualquier agente compatible entiende sin re-implementación. Un
microservicio convencional es opaco: cada cliente tiene que aprender su API. Un MCP server
publica:

- Lista de tools disponibles, con sus schemas.
- Lista de resources, con sus URIs.
- Lista de prompts pre-armados.

Eso lo hace **plug-and-play** para agentes, lo que un REST API tradicional no es.

📎 Mira: [`agentes_vs_mcp.md`](./agentes_vs_mcp.md).

## Diseño de prompts

### 5. ¿Cómo evalúo si un cambio en el system prompt mejoró o empeoró el agente?

El error común es probar 3 prompts manualmente y declarar ganador. Lo mínimo viable es:

1. Tener un **dataset de evaluación** (ej. el `data/comentarios_codigo.csv` para sentimientos).
2. Definir una **métrica clara** (accuracy, F1, latencia, costo).
3. Correr el dataset con cada versión del prompt.
4. Comparar.

`src/sentiment.py` es exactamente esto para clasificación. Tema avanzado: cuando la métrica
es subjetiva ("¿es la respuesta útil?"), se usa un **LLM-as-judge** — otro modelo evalúa la
salida.

### 6. ¿Cómo evito que el agente "alucine" cuando no sabe la respuesta?

Tres palancas:

1. **System prompt:** instrucción explícita "si no estás seguro, dilo en vez de inventar".
   El prompt default del repo ya tiene esto.
2. **Temperatura:** baja (0.2 o menos) para tareas factuales; alta (0.7+) solo para creativas.
3. **RAG:** dar al modelo los hechos relevantes en el contexto en vez de pedirle que los
   recuerde. Es el "cheat" más efectivo.

**Pregunta retadora:** un modelo con temperatura 0 ¿deja de alucinar? Hint: no.
Solo deja de variar — sigue alucinando, pero la misma alucinación cada vez.

## Operación de agentes

### 7. ¿Cómo hago observability de un agente en producción?

Lo mínimo que necesitas loggear:

- Cada request y cada response, con timestamps.
- El system prompt usado (útil para A/B y rollback).
- Tokens de entrada y salida (para costo).
- Tiempo de respuesta del modelo.
- IDs únicos por conversación, por turno, por usuario.

Una vez que tienes eso:

- **Dashboards** de costo/latencia/error rate (Grafana, Datadog).
- **Eval suites** que se corran nightly contra un golden dataset, para detectar regresiones.
- **Alertas** cuando el modelo cambia (los proveedores actualizan los pesos en silencio).

Herramientas modernas: [LangSmith](https://www.langchain.com/langsmith),
[Helicone](https://www.helicone.ai/), [Langfuse](https://langfuse.com/).

### 8. ¿Cuánto cuesta correr un agente sobre DO Gradient AI vs. otros proveedores?

DO Gradient AI cobra por **input + output tokens** del modelo. Para Llama 3.3 70B en abril
2026 los costos están en el rango de fracción de centavo por 1k tokens (revisa la
[página de pricing](https://www.digitalocean.com/pricing/genai) — cambia).

**$200 USD de crédito free** dan para muchísimo desarrollo si tienes prompts cortos y
respuestas concisas. Una conversación típica de 10 turnos con prompt de 500 palabras consume
del orden de cents.

Comparación rápida: OpenAI GPT-4 Turbo es ~10–20x más caro por token que Llama 70B en
proveedores tipo Together / Groq / DO Gradient — de ahí el atractivo de open-weights para
production agents de alto volumen.

### 9. ¿Cómo hago que mi agente sea seguro frente a prompt injection?

Esto es **el** problema no resuelto del campo. Lo que se puede hacer hoy:

- **Separar contextos:** nunca pongas datos no confiables (input de usuario, contenido scrapeado)
  en el `role: system`. Ponlos en `role: user`.
- **Output sanitization:** si el agente puede ejecutar acciones (vía MCP), valida cada
  acción antes de ejecutarla (allowlist de tools, parámetros tipados).
- **Defense in depth:** el agente no debe ser el único guardián. La capa de aplicación tiene
  que validar también.
- **Adversarial testing:** probar con inputs como `"Ignore previous instructions and …"`,
  `"<|im_end|>"`, prompts en otros idiomas, payloads codificados, etc.

📎 Recurso: [Simon Willison sobre prompt injection](https://simonwillison.net/series/prompt-injection/) — el principal blogger sobre esta categoría desde 2022.

## Multi-agente y orquestación

### 10. ¿Cuándo conviene un solo agente vs. múltiples agentes con roles?

- **Un solo agente.** Si la tarea cabe mentalmente en una sola "personalidad" (ej. un
  asistente conversacional). Más simple = más mantenible.
- **Múltiples agentes.** Si la tarea tiene fases con perfiles distintos (planeador / ejecutor;
  research / writer / editor) o si necesitas paralelismo real (3 agentes haciendo cosas
  distintas a la vez).

**Pregunta retadora del [caso real prodSens](https://prodsens.live/2026/04/15/17-weeks-running-7-autonomous-ai-agents-in-production-real-lessons-and-real-numbers/):**
con 7 agentes corriendo en paralelo, ¿cómo evitas explosión combinatoria de fallos? Hint:
human-in-the-loop gates en pasos irreversibles.

### 11. ¿Qué es un "agent harness" y por qué se volvió un patrón en 2026?

Tres planos que cualquier agente serio implementa hoy:

- **Brain.** Modelo + bucle de razonamiento.
- **Hands.** Ejecución sandboxed (filesystem, shell, browser).
- **Session.** Memoria persistente entre runs.

Antes de que el patrón se estandarizara, cada equipo reinventaba estos tres componentes a su
manera. Ahora se ven como capas separables — puedes cambiar el modelo (brain) sin tocar las
herramientas (hands), y viceversa.

📎 Mira: [`tendencias_2026.md`](./tendencias_2026.md) §1.

## Fronteras / preguntas abiertas

### 12. ¿Por qué los modelos siguen sin ser confiables en matemáticas básicas?

Un modelo de 70B parámetros puede escribir poesía pero falla 7+8 algunas veces. La razón es
que el modelo tokeniza dígitos de forma rara y no tiene una "calculadora" interna — predice
el siguiente token basándose en patrones estadísticos. La solución práctica es **darle una
calculadora vía tool calling**, no entrenar más matemáticas.

### 13. ¿Por qué los agentes "se olvidan" de instrucciones a mitad de una conversación larga?

El context window es finito. Cuando se llena, partes del prompt se truncan o se comprimen.
Y aún antes de truncar, los modelos tienden a **dar más peso a información reciente** ("recency
bias"). De ahí el patrón `/reset` del REPL del repo — empezar fresco cuando el contexto se
ensucia.

### 14. ¿Cómo va a cambiar todo esto en los próximos 12 meses?

Apuesta personal basada en las tendencias:

- **MCP** se vuelve invisible (parte de los SDKs de cada proveedor).
- **Agentes locales** (corriendo en tu laptop) ganan terreno frente a SaaS por privacidad y costo.
- **Modelos pequeños + fine-tuning + RAG** reemplaza a "modelo grande genérico" para casos
  enterprise.
- **Multi-agente con human-in-the-loop** se vuelve el patrón default para acciones irreversibles
  (no fully-autonomous).

Pero como decía [Komissarov](https://medium.com/@olegkomissarov/the-month-ai-agents-took-the-wheel-everything-that-matters-from-march-april-2026-512934123559):
"el ritmo de cambio en este espacio rompe cualquier roadmap a 12 meses". Aprende los
fundamentos, no los frameworks de moda.
