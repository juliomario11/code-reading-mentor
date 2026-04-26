# 🧠 code-reading-mentor

> An AI agent specialized in helping developers read and understand code written by others.
> Built on top of [DigitalOcean Gradient AI Platform](https://www.digitalocean.com/products/gradient) using Meta Llama 3.3 70B Instruct.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![DigitalOcean Gradient AI](https://img.shields.io/badge/DO-Gradient%20AI-0080FF.svg)](https://docs.digitalocean.com/products/gradient-ai-platform/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## What this is

A focused AI agent that helps you read code you didn't write. You paste a snippet,
and it walks you through it like a senior engineer would: language and intent first,
then structure, then logic, then the non-obvious parts (idioms, side effects, likely bugs).

Crucially, when given a snippet without enough context, **it asks follow-up questions
instead of fabricating an explanation** — a defensive behavior built into the system prompt.

## Why I built it

I wanted to learn the full lifecycle of building, deploying and consuming a managed AI
agent end-to-end, without lock-in to any single LLM provider:

- **Provision** an agent on a managed platform (DO Gradient AI).
- **Iterate** the system prompt with versioning and concrete test cases.
- **Consume** it from local Python using a portable, OpenAI-compatible API.
- **Document** it cleanly enough that anyone can reproduce in 5 minutes.

## Architecture

```
                  +-------------------------------+
                  |   DigitalOcean Gradient AI    |
   +--------+     |   ┌─────────────────────┐     |
   |   you  | →   |   │ Agent: code-mentor  │     |
   | (REPL) |     |   │  - System prompt    │     |
   +--------+     |   │  - Llama 3.3 70B    │     |
        ↑         |   └─────────────────────┘     |
        |         +-------------------------------+
        +---- streaming response (token-by-token)
```

The agent's endpoint is OpenAI-compatible, so the client uses the official
`openai` Python SDK — only the `base_url` changes. This means the same code
can target OpenAI, Anthropic, Groq, vLLM, etc., with a one-line config change.

## Quickstart

### Prerequisites

- Python 3.10+
- A [DigitalOcean account](https://cloud.digitalocean.com/registrations/new) with Gradient AI access
- An agent created in DO Gradient AI Platform (see [Setup](#setup))

### Setup

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
# Edit .env with your agent endpoint and access key (see below)
```

### Configuration

Edit `.env`:

```env
DO_AGENT_ENDPOINT=https://YOUR_AGENT_SUBDOMAIN.agents.do-ai.run
DO_AGENT_ACCESS_KEY=your_endpoint_access_key
DO_AGENT_MODEL=n/a   # The agent has its own model configured server-side
```

Get these from your DO Gradient AI agent's panel:
1. Go to your agent in [the DO control panel](https://cloud.digitalocean.com/gen-ai/agents).
2. Copy the **Endpoint URL** (top of the agent page).
3. Create an **Endpoint Access Key** in the agent settings.

### Run

One-shot demo:

```bash
python -m src.client
```

Interactive REPL with streaming and history:

```bash
python -m src.chat
```

In the REPL:

| Command  | What it does                       |
| -------- | ---------------------------------- |
| `/reset` | Clears the conversation history    |
| `/tokens`| Shows accumulated message count    |
| `/exit`  | Quits the REPL (or `Ctrl+C`)       |

## Setting up the agent on DO Gradient AI

If you want to recreate the agent yourself (recommended for learning):

1. Create a project on DO and a Personal Access Token with `genai` (full CRUD)
   and `project` (read) scopes.
2. Create an agent in **Agent Platform**:
   - **Name:** `code-reading-mentor`
   - **Model:** `Meta Llama 3.3 Instruct (70B)` (open-source models are available
     even on the trial tier; commercial models like Claude or GPT may require a
     paid subscription tier)
   - **Region:** `tor1`
   - **Instructions:** see [`prompts/system_prompt_v2.md`](prompts/system_prompt_v2.md)
3. Generate an Endpoint Access Key from the agent's settings.

## Notes on the system prompt

The instructions evolved across iterations:

- **v1** — basic 5-step protocol. Failed when given snippets without context: it would
  fabricate plausible-but-incorrect explanations of methods it had never seen.
- **v2 (current)** — adds a mandatory **Step 0: Context Check** before any analysis.
  If the snippet has undefined identifiers and no surrounding context, the agent halts
  the protocol and asks 1–3 targeted questions instead of guessing.

This pattern (an "early-return guard" inside a procedural prompt) generalizes well
to other agents: instructions framed as **numbered steps that can short-circuit**
are followed more reliably than the same rules expressed as bullet-point restrictions.

## Tech stack

- **Python 3.10+**
- **[OpenAI Python SDK](https://github.com/openai/openai-python)** — used as a generic
  client because DO Gradient AI exposes an OpenAI-compatible API.
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** — `.env` loader.
- **[rich](https://github.com/Textualize/rich)** — terminal formatting.
- **DO Gradient AI Platform** — managed agent hosting.

## Project structure

```
code-reading-mentor/
├── .env.example          # Template for env vars (committed)
├── .gitignore
├── README.md
├── requirements.txt
├── prompts/
│   └── system_prompt_v2.md   # Versioned system prompt
└── src/
    ├── __init__.py
    ├── client.py         # One-shot agent client
    └── chat.py           # Interactive REPL with streaming
```

## Lessons learned

- **System prompts are code.** They have bugs, get versioned, deserve test cases.
- **Operational constraints shape design.** Trial tier blocked Claude/GPT; the code
  reads `model` from env so swapping providers stays a config change, not a refactor.
- **OpenAI compatibility matters more than any single provider.** DO, Groq, Together,
  vLLM and others all expose the same shape. Code against the shape, not the brand.
- **Defensive behavior beats apparent helpfulness.** An agent that asks for missing
  context produces less impressive demos but more correct answers.

## License

MIT — see [LICENSE](LICENSE).