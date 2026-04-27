# Fine-tuning: cuándo conviene, alternativas a DO Gradient AI, caso Plan-and-Act

## Realidad de DO Gradient AI hoy

**DO Gradient AI no expone hoy fine-tuning custom de foundation models.** La plataforma te
deja escoger entre modelos pre-entrenados (Llama, Mistral, DeepSeek, Claude, GPT…) y
configurar instrucciones, knowledge bases (RAG) y guardrails.

Si tu caso de uso necesita literalmente *cambiar los pesos* de un modelo, hoy en día tienes
que salir de la consola de Gradient.

## ¿Cuándo conviene fine-tunear?

Antes de meterte en fine-tuning, considera el orden:

1. **Mejor prompt.** El 80% de los casos donde alguien dice "necesito fine-tuning" se
   resuelven con un system prompt mejor + few-shot examples.
2. **RAG.** Si el problema es "el modelo no conoce mis docs", la respuesta casi siempre es
   RAG (vector store + retrieval), no fine-tuning.
3. **MCP / tools.** Si el problema es "el modelo no puede ejecutar acciones", la respuesta
   es darle herramientas vía MCP, no fine-tuning.
4. **Fine-tuning** queda para casos muy específicos:
   - Estilo / tono muy particular que no se logra con prompt.
   - Formato de salida estricto que el modelo base no respeta consistentemente.
   - Tarea con muchos casos de borde donde el few-shot no cabe en contexto.
   - Latencia / costo: un modelo pequeño fine-tuneado puede reemplazar a uno grande genérico.

Ver [`agentes_vs_mcp.md`](./agentes_vs_mcp.md) para distinguir agente (prompt) vs. capacidades
(MCP), y [`tendencias_2026.md`](./tendencias_2026.md) §3 para la postura "los tres se combinan,
no se eligen".

## Rutas reales para fine-tuning, ordenadas por costo/control

### A. GPU Droplet de DO + Unsloth/Axolotl (autogestionado)

DO ofrece [GPU Droplets](https://www.digitalocean.com/products/gpu-droplets) con H100/A100/L40S
on-demand. Sobre eso corres un stack open-source:

- **[Unsloth](https://github.com/unslothai/unsloth)** — librería con kernels Triton hechos a
  mano. ~1.5x más rápido y ~60% menos VRAM que FA2 base. Hace fine-tuning de modelos pequeños
  (Gemma 4 E2B/E4B) viable hasta con **8GB VRAM**.
- **[Axolotl](https://github.com/axolotl-ai-cloud/axolotl)** — wrapper config-driven sobre
  HuggingFace TRL/PEFT. Define el run completo en un YAML.
- **LoRA / QLoRA** — método PEFT estándar, entrena solo adapters de bajo rango. Mantiene los
  pesos base intactos y produce un adapter pequeño (~50–500 MB) que aplicas sobre el modelo
  base en inference.

**Pros:** máximo control, paga por GPU/hora.
**Contras:** tú gestionas el stack (CUDA, drivers, dataset pipeline, eval, deployment).

### B. Plataformas de fine-tuning gestionado

Si no quieres pelear con CUDA:

- **[Together AI](https://www.together.ai/)** — fine-tuning sobre Llama, Mistral, etc. Pricing por token entrenado.
- **[Fireworks AI](https://fireworks.ai/)** — similar, fuerte en deployment de bajo latency.
- **[Modal](https://modal.com/)** — runtime serverless de GPU; ejecutas tu script de Unsloth/Axolotl como Function.
- **[OpenAI fine-tuning API](https://platform.openai.com/docs/guides/fine-tuning)** y
  **[Anthropic Workbench](https://www.anthropic.com/news/fine-tune-claude-3-haiku)** — si tu
  modelo base es propietario y aceptas el lock-in.

**Pros:** configuras el run, te entregan un endpoint listo.
**Contras:** lock-in del proveedor, menos control sobre el stack de entrenamiento.

## Caso de estudio: Plan-and-Act (ICML 2025)

[Plan-and-Act](https://arxiv.org/abs/2503.09572) es un buen ejemplo de fine-tuning con
propósito claro y por qué importa para agentes.

### Idea central

Separa **Planner** de **Executor**:

- **Planner** — recibe la meta del usuario y produce un plan estructurado de alto nivel
  (lista de pasos en lenguaje natural).
- **Executor** — recibe cada paso del plan y lo traduce a acciones concretas en el entorno
  (clics, llamadas a API, modificaciones de archivos).

El cuello de botella es el Planner: los LLMs no están entrenados nativamente para producir
planes ejecutables. Por eso lo fine-tunean.

### Cómo lo entrenan

Generan dataset sintético anotando trayectorias ground-truth con planes "factibles". Aumentan
los datos para mejorar generalización a entornos no vistos.

### Resultados (web navigation)

- SOTA en **WebArena-Lite**: **57.58%** success rate.
- Mejor resultado **text-only** en **WebVoyager**: **81.36%**.
- Publicado en ICML 2025.

### Pesos disponibles

- Planner 70B: [`xTRam1/plan-and-act-planner-70b`](https://huggingface.co/xTRam1/plan-and-act-planner-70b)
- Documentación:
  - [Paper en arXiv](https://arxiv.org/abs/2503.09572)
  - [OpenReview](https://openreview.net/forum?id=ybA4EcMmUZ)
  - [PDF](https://openreview.net/pdf?id=ybA4EcMmUZ)

### Por qué importa para tu starter

Hoy `gradient-agent-starter` deja la "planeación" implícita en el system prompt. El siguiente
nivel — para tareas largas y multi-step — es separar Planner y Executor en dos requests al
mismo (o a dos) agentes, posiblemente con un Planner fine-tuneado tipo Plan-and-Act y un
Executor genérico.

## Esqueleto de un run de fine-tuning local con LoRA + Unsloth

Para que sirva de ancla mental — **no incluido en el repo todavía, es referencia**:

```python
from unsloth import FastLanguageModel
from trl import SFTTrainer
from datasets import load_dataset

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="meta-llama/Llama-3.3-70B-Instruct",
    max_seq_length=4096,
    load_in_4bit=True,    # QLoRA
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    lora_dropout=0.0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)

ds = load_dataset("json", data_files="my_dataset.jsonl", split="train")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=ds,
    # ... config de entrenamiento ...
)
trainer.train()
model.save_pretrained_merged("./adapter")  # o push_to_hub
```

## Flujo end-to-end recomendado

1. **Empieza con prompting.** Si tu prompt en `prompts/system_prompt.md` no resuelve, pasa a 2.
2. **Agrega RAG.** DO Gradient AI ya soporta [Knowledge Bases](https://docs.digitalocean.com/products/genai-platform/concepts/knowledge-bases/).
3. **Agrega tools vía MCP.** Si lo que falta es ejecución, no conocimiento.
4. **Solo entonces, fine-tuning.** Y empieza con LoRA sobre un modelo pequeño. Si funciona,
   escalas.

Más material práctico: [Fine-Tuning Local LLMs with Unsloth + LoRA — CraftRigs (abr 2026)](https://craftrigs.com/guides/fine-tuning-unsloth-lora-gpu).
