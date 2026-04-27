# 🤖 gradient-agent-starter

> Plantilla mínima para hablar con un agente de IA gestionado en
> [DigitalOcean Gradient AI](https://www.digitalocean.com/products/gradient).
> Hecha para que un dev backend junior pueda hacer `git clone`, pegar dos credenciales y
> tener un agente respondiendo en **menos de 5 minutos**.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![DigitalOcean Gradient AI](https://img.shields.io/badge/DO-Gradient%20AI-0080FF.svg)](https://docs.digitalocean.com/products/gradient-ai-platform/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> 💡 **DigitalOcean da $200 USD de crédito gratis** a cuentas nuevas (válido 60 días).
> [Crea tu cuenta aquí](https://www.digitalocean.com/try/free-tier-credit) — alcanza
> de sobra para correr este starter durante semanas. Una conversación de 10 turnos cuesta
> del orden de centavos.

---

## Qué hace este repo

Te entrega tres formas de hablar con tu agente de DO desde Python:

1. **Demo en una sola llamada** — `python -m src.client`
2. **Chat interactivo (REPL)** con historial — `python -m src.chat`
3. **Clasificador de sentimientos sobre CSV** (ejemplo de uso real) — `python -m src.sentiment`

Y una idea principal: **el comportamiento del agente vive en archivos del repo** (en
`prompts/`), no en la UI de DO. Eso significa que para cambiar la personalidad del agente
solo cambias un archivo `.md` y haces `git commit`. Cero re-deploy.

## Empezar en 5 minutos

### Paso 1 — Clona e instala

```bash
git clone https://github.com/juliomario11/gradient-agent-starter.git
cd gradient-agent-starter

python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Paso 2 — Crea tu `.env`

```bash
cp .env.example .env
```

Edita `.env` y pon tus dos credenciales:

```env
DO_AGENT_ENDPOINT=https://TU_SUBDOMINIO.agents.do-ai.run
DO_AGENT_ACCESS_KEY=tu_endpoint_access_key
DO_AGENT_MODEL=n/a
```

¿No tienes esas credenciales? Sigue una de las dos guías de abajo:

- **Por la web** (más fácil para empezar): [Cómo crear el agente desde cero](#cómo-crear-el-agente-desde-cero) y [Cómo obtener las credenciales](#cómo-obtener-las-credenciales-del-env).
- **Por terminal** (con `doctl`): [Setup con doctl](#setup-con-doctl-cli-de-digitalocean).

### Paso 3 — Corre el demo más vistoso: clasificador de sentimientos

```bash
python -m src.sentiment
```

El script lee `data/comentarios_codigo.csv` (40 comentarios pre-etiquetados), le pide al agente
que los clasifique en `positivo` / `neutral` / `negativo`, y reporta accuracy:

```
Total clasificado: 40
Con etiqueta esperada: 40
Aciertos: 40 (100.0%)
```

Si ves esto, **ya tienes el agente funcionando**. Felicidades.

### Paso 4 — Abre el chat interactivo

```bash
python -m src.chat
```

Te abre un REPL. Escribes y el agente te responde con streaming. Comandos disponibles:

| Comando   | Para qué                                                    |
| --------- | ----------------------------------------------------------- |
| `/reset`  | Borra el historial y arranca conversación nueva             |
| `/reload` | Recarga el system prompt desde disco (sin perder historial) |
| `/tokens` | Muestra cuántos mensajes acumulados llevas                  |
| `/exit`   | Sale (también `Ctrl+C`)                                     |

## Los 3 comandos del repo

### `python -m src.client` — Demo de una sola llamada

**Para qué.** Verificar rápido que tus credenciales funcionan. Carga el system prompt desde
archivo, manda un saludo "preséntate en una frase", imprime la respuesta, sale.

**Ejemplo de salida:**

```
📤 Enviando al agente (https://...agents.do-ai.run)
   System prompt: prompts/system_prompt.md

📥 Respuesta:
Soy un asistente digital diseñado para proporcionar información útil y precisa.
```

### `python -m src.chat` — REPL con streaming

**Para qué.** Conversar con el agente con historial completo (cada turno ve los anteriores).
Lo que usarías día a día.

**Tip:** el REPL recuerda toda la conversación. Si quieres "olvidar" y empezar fresco
(porque el contexto se ensució o quieres probar algo distinto), usa `/reset`.

### `python -m src.sentiment` — Clasificador sobre CSV

**Para qué.** Clasificar comentarios de un CSV en `positivo` / `neutral` / `negativo` y
medir accuracy contra etiquetas esperadas. Ejemplo de cómo usar al agente como **componente
de un pipeline**, no solo como chatbot.

**Variantes útiles:**

```bash
# Usa el dataset por defecto (data/comentarios_codigo.csv) y solo imprime el reporte
python -m src.sentiment

# Usa tu propio CSV (solo necesita la columna `texto`)
python -m src.sentiment ruta/a/mi.csv

# Guarda las predicciones a un CSV de salida — útil si quieres revisar fila por fila
python -m src.sentiment --out resultados.csv

# Combinado: tu CSV de entrada + tu CSV de salida
python -m src.sentiment ruta/a/mi.csv --out resultados.csv
```

El CSV de salida queda con las columnas originales **+** dos columnas extra:

- `sentimiento_predicho` — la etiqueta normalizada (`positivo`, `neutral`, `negativo` o
  `desconocido` si la respuesta del modelo no coincidió con ninguna).
- `respuesta_bruta` — la respuesta literal del modelo, útil para depurar cuando el modelo
  responde algo no esperado.

## Cómo cambiar el comportamiento del agente

Esta es la parte cool del repo. **No tienes que tocar nada en la UI de DO** para cambiar cómo
responde el agente. Solo cambias el archivo `.md` que define su personalidad.

### Opción A — Editar el prompt por defecto

Edita `prompts/system_prompt.md`, salva, y lanza `python -m src.chat` otra vez. (Si el REPL
ya estaba abierto, usa `/reload` y aplica al próximo turno.)

### Opción B — Usar uno de los ejemplos incluidos

```bash
# Asistente de soporte técnico
SYSTEM_PROMPT_FILE=prompts/examples/customer_support.md python -m src.chat

# Clasificador de sentimientos (mismo que usa src.sentiment)
SYSTEM_PROMPT_FILE=prompts/examples/sentiment_classifier.md python -m src.chat
```

### Opción C — Crear el tuyo

```bash
echo "Eres un poeta. Responde solo en haikus." > prompts/examples/poeta.md
SYSTEM_PROMPT_FILE=prompts/examples/poeta.md python -m src.chat
```

Más ideas de qué puedes construir cambiando solo el prompt:
[`Documentacion_Actual_Futura/mas_ejemplos.md`](./Documentacion_Actual_Futura/mas_ejemplos.md).

## Cómo crear el agente desde cero

Si no tienes un agente todavía, esta es la guía visual paso a paso. Las capturas viven en
[`docs/imagenes/`](docs/imagenes/).

### Paso 1 — Abre Agent Platform

Inicia sesión en [`cloud.digitalocean.com`](https://cloud.digitalocean.com/) y entra a
[**Agent Platform → Agent workspaces**](https://cloud.digitalocean.com/gen-ai/workspaces).

![Listado de Agent workspaces](docs/imagenes/06-agent-platform-listado.png)

### Paso 2 — Abre "Create an agent"

Desde un workspace, haz clic en **Create Agent**.

![Formulario Create an agent vacío](docs/imagenes/07-crear-agente-form.png)

### Paso 3 — Pon nombre e instrucciones

- **Agent name:** kebab-case (ej: `gradient-agent-starter`). Este nombre se usa también como
  subdominio del endpoint público.
- **Agent instructions:** **deja un placeholder neutro** ("See repo for system prompt").
  Como en este repo el prompt vive en `prompts/system_prompt.md` y se manda desde el código,
  si pones instrucciones aquí también van a entrar en conflicto.

![Formulario con nombre e instrucciones llenas](docs/imagenes/08-form-nombre-instrucciones.png)

### Paso 4 — Selecciona modelo

Despliega **Model provider**. Recomiendo **Meta Llama 3.3 Instruct (70B)**: balance bueno
calidad/latencia/costo y disponible en el tier de prueba.

![Selector de Model provider](docs/imagenes/09-selector-modelo.png)

![Modelos disponibles bajo Meta Llama](docs/imagenes/10-modelos-disponibles.png)

![Llama 3.3 Instruct (70B) seleccionado](docs/imagenes/11-llama-3-3-70b-seleccionado.png)

### Paso 5 — Workspace y proyecto, y crear

Elige el **workspace** y el **project** y confirma con **Create Agent**.

![Final del formulario antes de crear](docs/imagenes/12-final-details-create-agent.png)

### Paso 6 — Espera el deploy

Toma 1–3 minutos. Cuando termine, el estado pasa a **Running** y aparece el endpoint público.

![Pantalla de Agent deployment in progress](docs/imagenes/13-agente-creado-deploying.png)

Ahora toca obtener las credenciales que van en el `.env` — sigue la siguiente sección.

## Cómo obtener las credenciales del `.env`

Necesitas **dos** valores: el **Endpoint URL** y un **Endpoint Access Key**.

> **OJO:** estos son distintos del Personal Access Token (`dop_v1_…`) que usa `doctl`. Ese
> está en la siguiente sección.

### Paso 1 — Abre tu agente en el panel

En el listado de agentes, haz clic en el nombre del agente.

![Panel del proyecto con el agente listado](docs/imagenes/01-panel-proyecto.png)

### Paso 2 — Copia el Endpoint URL desde Overview

En la pestaña **Overview**, sección **Agent Essentials → Endpoint**: ese campo
(`https://…agents.do-ai.run`) es el valor de `DO_AGENT_ENDPOINT` en tu `.env`.

![Overview del agente con Endpoint URL](docs/imagenes/02-agente-overview.png)

### Paso 3 — Ve a Settings → Endpoint Access Keys

![Sección Endpoint Access Keys](docs/imagenes/03-settings-access-keys.png)

### Paso 4 — Crea una key nueva

Haz clic en **Create Key**, dale un nombre descriptivo (ej: `vscode-local-dev`) y confirma.

![Modal de creación de Access Key](docs/imagenes/04-modal-crear-key.png)

### Paso 5 — Copia el secreto **antes** de cerrar el aviso

El valor real **solo se muestra una vez**. Cópialo a tu `.env` como `DO_AGENT_ACCESS_KEY`. En
la imagen aparece tachado por seguridad — el tuyo será visible.

![Aviso con la secret key recién creada (valor redactado)](docs/imagenes/05-key-creada.png)

Si pierdes el valor antes de copiarlo, usa el menú `…` de esa key → **Regenerate** (rota el
valor) o **Delete** + crear nueva.

## Setup con `doctl` (CLI de DigitalOcean)

Si prefieres operar todo desde la terminal, esta sección te lleva de cero a poder
listar/crear/borrar agentes desde la CLI.

> **Las dos credenciales son distintas:**
>
> - **Personal Access Token (PAT)** — formato `dop_v1_…`. Para `doctl` y la API REST de DO.
>   Para gestionar **toda** la infraestructura. Vive en
>   [`account/api/tokens`](https://cloud.digitalocean.com/account/api/tokens).
> - **Endpoint Access Key** — para que tu cliente Python hable al endpoint del **agente**
>   específico. La de la sección anterior.

### Paso 1 — Instala `doctl`

```bash
# macOS
brew install doctl

# Linux (snap)
sudo snap install doctl

# Windows (Scoop)
scoop install doctl
```

Verifica:

```bash
doctl version
```

Documentación oficial: [Install doctl](https://docs.digitalocean.com/reference/doctl/how-to/install/).

### Paso 2 — Crea un Personal Access Token

Ve a [`account/api/tokens`](https://cloud.digitalocean.com/account/api/tokens).

![Página de Personal Access Tokens](docs/imagenes/14-pat-tokens-page.png)

Haz clic en **Generate New Token**:

![Formulario Create Personal Access Token vacío](docs/imagenes/15-pat-form-vacio.png)

Llena el form (nombre descriptivo + expiration de 30/60/90 días + Full Access mientras
aprendes):

![Formulario Create Personal Access Token completo](docs/imagenes/16-pat-form-completo.png)

DO te muestra el token **una sola vez** con formato `dop_v1_…`. **Cópialo de inmediato**:

![Token generado, valor redactado](docs/imagenes/17-pat-creado-redactado.png)

### Paso 3 — Autentica `doctl`

```bash
doctl auth init --context default
# Pega el dop_v1_… cuando lo pida

doctl account get   # verifica que está autenticado
```

### Paso 4 — Comandos útiles de Gradient AI

```bash
# Listar agentes
doctl genai agent list

# Detalle de un agente
doctl genai agent get <agent-id>

# Listar modelos disponibles
doctl genai model list

# Crear un agente nuevo
doctl genai agent create \
  --name gradient-agent-starter \
  --model-uuid <model-uuid> \
  --instruction "See repo for system prompt" \
  --project-id <project-id> \
  --region tor1

# Listar las endpoint access keys de un agente
doctl genai agent endpoint-key list <agent-id>

# Crear una endpoint access key (la usas como DO_AGENT_ACCESS_KEY)
doctl genai agent endpoint-key create <agent-id> --name vscode-local-dev

# Borrar un agente
doctl genai agent delete <agent-id>
```

Referencia completa: [`doctl genai`](https://docs.digitalocean.com/reference/doctl/reference/genai/).

## Estructura del proyecto

```
gradient-agent-starter/
├── .env.example                  # Plantilla de credenciales (copia a .env)
├── README.md                     # Estás aquí
├── requirements.txt
├── data/
│   └── comentarios_codigo.csv    # Dataset de ejemplo (40 filas etiquetadas)
├── docs/
│   └── imagenes/                 # Capturas para las guías visuales
├── prompts/
│   ├── system_prompt.md          # Prompt por defecto (asistente genérico)
│   └── examples/
│       ├── customer_support.md
│       └── sentiment_classifier.md
├── src/
│   ├── client.py                 # Cliente OpenAI-compatible + ask() one-shot
│   ├── chat.py                   # REPL interactivo con streaming
│   └── sentiment.py              # Pipeline de clasificación sobre CSV
└── Documentacion_Actual_Futura/  # Material para profundizar
    ├── README.md                 # Índice
    ├── tendencias_2026.md
    ├── agentes_vs_mcp.md
    ├── mas_ejemplos.md
    ├── fine_tuning.md
    └── preguntas_para_explorar.md
```

## ¿Y ahora qué? — Para profundizar

Cuando este starter te quede chico, abre la carpeta
[`Documentacion_Actual_Futura/`](./Documentacion_Actual_Futura/). Encuentras:

- 🆚 [`agentes_vs_mcp.md`](./Documentacion_Actual_Futura/agentes_vs_mcp.md) — qué es un agente,
  qué es un MCP server, cuándo uso cada uno y cómo se combinan.
- 💡 [`mas_ejemplos.md`](./Documentacion_Actual_Futura/mas_ejemplos.md) — 10 ideas de cosas
  que puedes construir cambiando solo el prompt (revisor de PRs, traductor de logs, generador
  de SQL desde lenguaje natural, coach de entrevistas, etc.).
- 🔬 [`fine_tuning.md`](./Documentacion_Actual_Futura/fine_tuning.md) — cuándo conviene
  fine-tunear, alternativas a DO Gradient y caso de estudio Plan-and-Act.
- 📈 [`tendencias_2026.md`](./Documentacion_Actual_Futura/tendencias_2026.md) — qué hay de
  nuevo en agentes a abril 2026, con fuentes y fechas.
- ❓ [`preguntas_para_explorar.md`](./Documentacion_Actual_Futura/preguntas_para_explorar.md) —
  preguntas curiosas para tirar del hilo (¿prompt vs RAG vs fine-tuning?, ¿cómo evito
  alucinaciones?, ¿qué es prompt injection?, etc.).

## Solución de problemas comunes

| Síntoma                                                              | Causa probable                                                     | Qué hacer                                                                                            |
| -------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| `AuthenticationError: Invalid API key`                                | Pusiste el PAT (`dop_v1_…`) en `DO_AGENT_ACCESS_KEY`                | Usa la **Endpoint Access Key** del agente, no el PAT. Son dos cosas distintas.                      |
| `APIConnectionError: Connection error`                                | URL del endpoint mal escrita o agente no en estado `Running`        | Revisa el panel de DO; espera a que el agente termine de deployar.                                  |
| El agente responde con un tono raro / temas equivocados              | Las "Agent instructions" en la UI de DO están sobrescribiendo el prompt del repo | Vacía el campo Instructions en la UI (o pon un placeholder neutro). El prompt real va en `prompts/`. |
| `python: No module named src`                                         | Estás corriendo desde otra carpeta                                  | `cd` a la raíz del repo. Los comandos son `python -m src.<algo>` desde ahí.                          |
| Te pide instalar `openai`, `dotenv`, `rich` aunque ya hiciste `pip install` | El venv no está activado                                       | `source .venv/bin/activate` (Linux/macOS) o `.\.venv\Scripts\Activate.ps1` (Windows).                |

## Stack técnico

- **Python 3.10+**
- **[OpenAI Python SDK](https://github.com/openai/openai-python)** — usado como cliente
  genérico porque DO Gradient AI expone una API compatible con OpenAI.
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** para `.env`.
- **[rich](https://github.com/Textualize/rich)** para formato en terminal.
- **DigitalOcean Gradient AI Platform** para hostear el agente.

## Licencia

MIT — ver [LICENSE](LICENSE).
