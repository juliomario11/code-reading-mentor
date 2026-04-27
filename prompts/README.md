# `prompts/`

System prompts del agente, cargados desde el código en runtime.

## Cómo se usan

`src.client` lee el archivo apuntado por la variable de entorno `SYSTEM_PROMPT_FILE`
(o `prompts/system_prompt.md` por defecto) y lo inyecta como mensaje
`role: system` al inicio de cada conversación.

Esto significa que **el comportamiento del agente vive en este repo, no en el
panel de DigitalOcean**. Para cambiar cómo responde el agente, edita uno de
estos archivos y vuelve a correr el cliente — no toques las "Agent
instructions" en la UI de DO.

Ventajas:

- Las instrucciones quedan versionadas en `git`.
- Puedes A/B-testear prompts cambiando una variable de entorno (`SYSTEM_PROMPT_FILE=prompts/examples/sentiment_classifier.md`).
- El mismo agente sirve múltiples casos de uso sin re-deploy.

## Archivos

- [`system_prompt.md`](./system_prompt.md) — prompt por defecto, genérico.
- [`examples/`](./examples) — prompts de ejemplo para casos de uso concretos.
  - [`sentiment_classifier.md`](./examples/sentiment_classifier.md) — clasificador de sentimientos para CSV.
  - [`customer_support.md`](./examples/customer_support.md) — agente de soporte técnico de primer nivel.

Para usar uno de los ejemplos:

```bash
SYSTEM_PROMPT_FILE=prompts/examples/customer_support.md python -m src.chat
```
