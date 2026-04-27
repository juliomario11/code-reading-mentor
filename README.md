# 🧠 code-reading-mentor

> Un agente de IA especializado en ayudar a desarrolladores a **leer y entender código escrito por otras personas**.
> Construido sobre la [DigitalOcean Gradient AI Platform](https://www.digitalocean.com/products/gradient) usando Meta Llama 3.3 70B Instruct.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![DigitalOcean Gradient AI](https://img.shields.io/badge/DO-Gradient%20AI-0080FF.svg)](https://docs.digitalocean.com/products/gradient-ai-platform/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## Qué es esto

Un agente de IA enfocado que te ayuda a leer código que no escribiste tú. Pegas un fragmento
y te lo explica como lo haría un ingeniero senior: primero el lenguaje y la intención,
luego la estructura, después la lógica, y al final lo no obvio (modismos, efectos secundarios, posibles bugs).

Lo más importante: cuando le entregas un fragmento sin contexto suficiente, **hace preguntas
de seguimiento en vez de inventar una explicación** — un comportamiento defensivo que está
incorporado directamente en el system prompt.

## Por qué lo construí

Quería aprender el ciclo de vida completo de construir, desplegar y consumir un agente
de IA gestionado de punta a punta, sin quedar atado a un solo proveedor de LLM:

- **Provisionar** un agente en una plataforma gestionada (DO Gradient AI).
- **Iterar** el system prompt con versionado y casos de prueba concretos.
- **Consumirlo** desde Python local usando un API portable compatible con OpenAI.
- **Documentarlo** lo suficientemente limpio para que cualquiera lo reproduzca en 5 minutos.

## Arquitectura

```
                  +-------------------------------+
                  |   DigitalOcean Gradient AI    |
   +--------+     |   ┌─────────────────────┐     |
   |   tú   | →   |   │ Agente: code-mentor │     |
   | (REPL) |     |   │  - System prompt    │     |
   +--------+     |   │  - Llama 3.3 70B    │     |
        ↑         |   └─────────────────────┘     |
        |         +-------------------------------+
        +---- respuesta en streaming (token a token)
```

El endpoint del agente es compatible con OpenAI, así que el cliente usa el SDK oficial
de `openai` en Python — solo cambia el `base_url`. Esto significa que el mismo código
puede apuntar a OpenAI, Anthropic, Groq, vLLM, etc., con un cambio de una sola línea
en la configuración.

## Inicio rápido

### Requisitos previos

- Python 3.10+
- Una [cuenta de DigitalOcean](https://cloud.digitalocean.com/registrations/new) con acceso a Gradient AI
- Un agente creado en DO Gradient AI Platform (ver [Configuración del agente](#configuración-del-agente-en-do-gradient-ai))

### Instalación

```bash
git clone https://github.com/juliomario11/code-reading-mentor.git
cd code-reading-mentor

python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

cp .env.example .env
# Edita .env con el endpoint y el access key de tu agente (ver abajo)
```

### Configuración

Edita `.env`:

```env
DO_AGENT_ENDPOINT=https://TU_SUBDOMINIO.agents.do-ai.run
DO_AGENT_ACCESS_KEY=tu_endpoint_access_key
DO_AGENT_MODEL=n/a   # El agente ya tiene un modelo configurado del lado del servidor
```

Para sacar estos dos valores desde el panel de DO, sigue la [**guía visual paso a paso**](#cómo-obtener-las-credenciales-del-env) más abajo.

### Ejecución

Demo de una sola interacción:

```bash
python -m src.client
```

REPL interactivo con streaming e historial:

```bash
python -m src.chat
```

Dentro del REPL:

| Comando   | Qué hace                               |
| --------- | -------------------------------------- |
| `/reset`  | Limpia el historial de la conversación |
| `/tokens` | Muestra los mensajes acumulados        |
| `/exit`   | Sale del REPL (también `Ctrl+C`)       |

### Analizador de sentimientos sobre comentarios de código

El repo incluye un dataset de ejemplo y un script que usa al mismo agente como clasificador
de sentimientos sobre comentarios de revisión de código en español.

- Dataset: [`data/comentarios_codigo.csv`](data/comentarios_codigo.csv) con columnas
  `id, texto, sentimiento_esperado` (etiquetas: `positivo`, `neutral`, `negativo`).
- Script: [`src/sentiment.py`](src/sentiment.py).

Para correrlo:

```bash
# Clasifica el dataset por defecto e imprime un reporte de accuracy
python -m src.sentiment

# Usa tu propio CSV (sólo necesita la columna `texto`)
python -m src.sentiment ruta/a/mi.csv

# Guarda las predicciones a un CSV de salida
python -m src.sentiment --out resultados.csv
```

El script le pide al agente que responda con una sola palabra (`positivo`, `neutral` o `negativo`)
por comentario y, si el CSV trae la columna `sentimiento_esperado`, compara y muestra errores.

## Cómo obtener las credenciales del `.env`

Para usar el agente desde tu máquina local necesitas dos valores que viven en el panel
de DigitalOcean: el **Endpoint URL** (a qué dirección hablarle al agente) y un
**Endpoint Access Key** (con qué credencial autenticarte). Esta sección muestra el
flujo completo en la UI actual de DO. Las capturas viven en [`docs/imagenes/`](docs/imagenes/).

> **Aviso de seguridad.** El Endpoint Access Key sólo se muestra **una vez**, justo
> después de crearlo. Cópialo de inmediato a tu `.env` local. Nunca lo subas al repo
> (el `.gitignore` ya excluye `.env`). Si se filtra, bórralo y crea uno nuevo.

### Paso 1 — Abre tu proyecto en el panel

Inicia sesión en [cloud.digitalocean.com](https://cloud.digitalocean.com/) y entra a tu
proyecto. En la sección **Agents** vas a ver tu agente listado, con su estado
(`Running`) y el endpoint público a la derecha.

![Panel del proyecto con el agente listado](docs/imagenes/01-panel-proyecto.png)

### Paso 2 — Copia el Endpoint URL desde el Overview del agente

Haz clic en el nombre del agente. En la pestaña **Overview** verás la tarjeta
**Agent Essentials** con la sección **Endpoint**: ese campo (`https://…agents.do-ai.run`)
es el valor de `DO_AGENT_ENDPOINT` en tu `.env`. Cópialo con el botón a la derecha.

![Overview del agente con Endpoint URL](docs/imagenes/02-agente-overview.png)

### Paso 3 — Ve a Settings → Endpoint Access Keys

Cambia a la pestaña **Settings** y desplázate hasta la sección **Endpoint Access Keys**.
Aquí gestionas las credenciales que permiten que apps externas (como este repo) hablen
con el endpoint privado de tu agente sin tener que ponerlo en modo público.

![Sección Endpoint Access Keys](docs/imagenes/03-settings-access-keys.png)

### Paso 4 — Crea una key nueva

Haz clic en **Create Key**, dale un nombre descriptivo (por ejemplo
`vscode-local-dev` o `doc-screenshot-demo`) y confirma con **Create**. Usa un nombre
distinto por entorno/máquina para poder revocar uno sin afectar a los demás.

![Modal de creación de Access Key](docs/imagenes/04-modal-crear-key.png)

### Paso 5 — Copia el secreto **antes** de cerrar el aviso

Después de crear la key aparece un aviso _"Don't forget to copy your secret key"_ con el
valor real (en la imagen aparece tachado por seguridad). **Cópialo ahora**: en cuanto
recargues la página o cierres el aviso, ya no podrás verlo otra vez. Pégalo en tu
`.env` local como `DO_AGENT_ACCESS_KEY`.

![Aviso con la secret key recién creada (valor redactado)](docs/imagenes/05-key-creada.png)

Si pierdes el valor antes de copiarlo, no pasa nada: usa el menú `…` de esa key para
**Regenerate** (rota el valor) o **Delete** (la borra) y crea una nueva.

### Resultado: tu `.env` local

Con los dos valores de arriba, tu `.env` queda así:

```env
DO_AGENT_ENDPOINT=https://TU_SUBDOMINIO.agents.do-ai.run
DO_AGENT_ACCESS_KEY=el_valor_que_copiaste_en_el_paso_5
DO_AGENT_MODEL=n/a
```

Documentación oficial de DO sobre access keys:
[Manage Endpoint Access Keys](https://docs.digitalocean.com/products/genai-platform/how-to/manage-endpoint-access-keys/).

## Configuración del agente en DO Gradient AI

Si quieres recrear el agente tú mismo (recomendado para aprender):

1. Crea un proyecto en DO y un Personal Access Token con los scopes `genai` (CRUD completo)
   y `project` (lectura).
2. Crea un agente en **Agent Platform**:
   - **Nombre:** `code-reading-mentor`
   - **Modelo:** `Meta Llama 3.3 Instruct (70B)` (los modelos open-source están
     disponibles incluso en el tier de prueba; los modelos comerciales como Claude
     o GPT pueden requerir un tier pago).
   - **Región:** `tor1`
   - **Instrucciones:** ver [`prompts/system_prompt_v2.md`](prompts/system_prompt_v2.md).
3. Genera un Endpoint Access Key desde los ajustes del agente.

## Notas sobre el system prompt

Las instrucciones evolucionaron a través de iteraciones:

- **v1** — protocolo básico de 5 pasos. Fallaba cuando recibía fragmentos sin contexto:
  inventaba explicaciones plausibles-pero-incorrectas sobre métodos que nunca había visto.
- **v2 (actual)** — agrega un **Paso 0: Verificación de Contexto** obligatorio antes de
  cualquier análisis. Si el fragmento tiene identificadores no definidos y no hay contexto
  alrededor, el agente detiene el protocolo y hace 1–3 preguntas puntuales en lugar de adivinar.

Este patrón (un "guard de retorno temprano" dentro de un prompt procedural) generaliza bien
a otros agentes: las instrucciones expresadas como **pasos numerados que pueden cortar el flujo**
se siguen de manera más confiable que las mismas reglas expresadas como bullets de restricciones.

## Stack técnico

- **Python 3.10+**
- **[OpenAI Python SDK](https://github.com/openai/openai-python)** — usado como cliente
  genérico porque DO Gradient AI expone una API compatible con OpenAI.
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** — cargador de `.env`.
- **[rich](https://github.com/Textualize/rich)** — formato en la terminal.
- **DO Gradient AI Platform** — hosting gestionado del agente.

## Estructura del proyecto

```
code-reading-mentor/
├── .env.example                   # Plantilla de variables de entorno (se commitea)
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   └── comentarios_codigo.csv     # Dataset de ejemplo para el analizador de sentimientos
├── prompts/
│   └── system_prompt_v2.md        # System prompt versionado
└── src/
    ├── __init__.py
    ├── client.py                  # Cliente de una sola interacción
    ├── chat.py                    # REPL interactivo con streaming
    └── sentiment.py               # Analizador de sentimientos sobre CSV
```

## Lecciones aprendidas

- **Los system prompts son código.** Tienen bugs, se versionan, merecen casos de prueba.
- **Las restricciones operativas moldean el diseño.** El tier de prueba bloqueaba Claude/GPT;
  el código lee `model` desde env para que cambiar de proveedor sea cambio de config,
  no refactor.
- **La compatibilidad con OpenAI importa más que cualquier proveedor individual.** DO, Groq,
  Together, vLLM y otros exponen la misma forma. Programa contra la forma, no contra la marca.
- **El comportamiento defensivo le gana a la utilidad aparente.** Un agente que pide contexto
  que falta genera demos menos impresionantes, pero respuestas más correctas.

## Licencia

MIT — ver [LICENSE](LICENSE).
