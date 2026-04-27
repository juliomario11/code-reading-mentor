# Más ejemplos: 10 cosas que puedes construir con este starter

Todos estos ejemplos siguen exactamente el mismo patrón del repo: **un system prompt en
`prompts/`** + el cliente Python sin tocar nada. Cambiar el comportamiento = cambiar la env
var `SYSTEM_PROMPT_FILE`. Cero re-deploy.

Cada idea trae:
- **Para qué sirve** — caso de uso real.
- **System prompt sketch** — punto de partida (lo refinas iterando).
- **Cómo correrlo** — comando exacto.
- **Extensión natural** — por dónde seguir si te enganchas.

> **Convención.** Los archivos de prompt nuevos los pones en `prompts/examples/<nombre>.md` y
> los activas con `SYSTEM_PROMPT_FILE=prompts/examples/<nombre>.md python -m src.chat`.

---

## 1. Revisor de Pull Requests

**Para qué.** Le pegas un diff o un PR y el agente te marca: bugs probables, code smells,
inconsistencias con el estilo de la base, qué pruebas faltan.

**Prompt sketch:**

```markdown
Eres un reviewer senior de código. Cuando el usuario te pegue un diff (formato git):

1. Identifica el lenguaje y el propósito aparente del cambio.
2. Lista bugs probables, ordenados por severidad (rojo/amarillo/verde).
3. Lista code smells y por qué importan en este contexto.
4. Sugiere pruebas que falten para cubrir el cambio.
5. Si el diff usa convenciones inconsistentes con el resto del archivo, dilo.

No reescribas el código. Comenta como en un PR review.
```

**Cómo correrlo:**

```bash
SYSTEM_PROMPT_FILE=prompts/examples/pr_reviewer.md python -m src.chat
```

**Extensión natural.** Conectarlo al GitHub API (vía MCP server) para que lea PRs reales y
postee comentarios. Ver [`agentes_vs_mcp.md`](./agentes_vs_mcp.md).

---

## 2. Resumidor de Slack / Discord / WhatsApp

**Para qué.** Le pegas un export de N mensajes de un canal y te devuelve un resumen ejecutivo
con: decisiones tomadas, pendientes, quién dijo qué, links importantes.

**Prompt sketch:**

```markdown
Recibirás un log de chat. Devuelve un resumen estructurado:

## Decisiones tomadas
- ...
## Pendientes
- [pendiente] ... (asignado: nombre, si se mencionó)
## Personas y posiciones
- Nombre: posición resumida
## Links / archivos compartidos
- ...
## Tono general
(neutral / tenso / celebratorio / etc.)
```

**Cómo correrlo:**

```bash
SYSTEM_PROMPT_FILE=prompts/examples/chat_summarizer.md python -m src.chat
```

**Extensión natural.** Cron job que dispara el agente sobre un canal cada noche y postea el
resumen en otro canal de "morning digest".

---

## 3. Traductor de logs / stack traces

**Para qué.** Le pegas un stack trace o un log de error críptico y te lo traduce a "¿qué pasó,
qué probable causa, qué intentar primero?" en español plano.

**Prompt sketch:**

```markdown
Eres un debugging buddy senior. Cuando el usuario te pegue un log o stack trace:

1. Una frase: ¿qué tipo de error es?
2. Probable causa raíz (no el síntoma — la causa).
3. 3 cosas que intentaría primero, en orden, antes de pedir ayuda.
4. Qué información adicional pediría si nada funciona.

Responde en español. No moralices sobre el código.
```

**Cómo correrlo:**

```bash
SYSTEM_PROMPT_FILE=prompts/examples/log_translator.md python -m src.chat
```

---

## 4. Generador de descripciones de PRs (commit-to-PR)

**Para qué.** Le pegas el output de `git log <base>..HEAD` y te genera una descripción de PR
en el formato de tu equipo (Conventional Commits, JIRA-friendly, etc.).

**Prompt sketch:**

```markdown
Recibirás un git log. Genera una descripción de PR siguiendo el formato:

## Summary
(2-3 oraciones, qué hace este cambio en lenguaje natural)

## Changes
- bullet por cambio meaningful (no por commit individual)

## Testing notes
(qué debería probar el reviewer, basado en los archivos tocados)

No incluyas commits de "fix typo", "wip" o "merge". Consolida lo equivalente.
```

---

## 5. Clasificador de tickets de soporte

**Para qué.** Recibes tickets sin etiquetar y los clasificas en categorías (`billing`,
`bug`, `feature_request`, `account`, `other`) + severidad (`low`/`med`/`high`).

**Prompt sketch:**

```markdown
Eres un router de tickets de soporte. Para cada ticket que recibas, responde
ÚNICAMENTE con JSON válido en una sola línea:

{"categoria": "...", "severidad": "...", "razon": "<una frase>"}

Categorías permitidas: billing, bug, feature_request, account, other.
Severidades: low, med, high.

Severidad high = el usuario reporta pérdida de datos, downtime, o pago duplicado.
Severidad med = funcionalidad rota pero hay workaround.
Severidad low = todo lo demás.
```

**Cómo correrlo:**

```bash
# Adapta src/sentiment.py — la lógica es idéntica, solo cambia el parser.
python -m src.sentiment tickets.csv --out tickets_clasificados.csv
```

**Extensión natural.** Después de clasificar, dispara workflow distinto por categoría
(MCP server que crea ticket en Linear, Jira, etc.).

---

## 6. Generador de queries SQL desde lenguaje natural

**Para qué.** Le describes una pregunta de negocio + el schema de la DB y te devuelve la
query SQL.

**Prompt sketch:**

```markdown
Eres un analista de datos. Cuando el usuario te dé una pregunta:

1. Si no te dio el schema de la DB, pídelo antes de cualquier otra cosa.
2. Devuelve UNA query SQL, en bloque de código, para el dialecto Postgres por defecto.
3. Bajo la query, una explicación de 2-3 líneas de qué hace y qué supuestos tomaste.
4. Si la pregunta es ambigua (ej: "ventas del mes" sin decir cuál), pide aclaración.

NO inventes nombres de tablas o columnas que no estén en el schema.
```

**Cómo correrlo:**

```bash
SYSTEM_PROMPT_FILE=prompts/examples/sql_writer.md python -m src.chat
```

---

## 7. Asistente para escribir tests

**Para qué.** Le pegas una función Python/JS y te genera 5–10 casos de test (felices, de borde,
adversariales) en el framework que uses.

**Prompt sketch:**

```markdown
Eres un test engineer. Cuando el usuario te pegue una función:

1. Identifica el lenguaje y el framework probable de tests (pytest, jest, etc.).
2. Lista 5-10 casos de test, agrupados como:
   - Happy path (3-4)
   - Edge cases (3-4)
   - Adversarial (1-2: input malicioso, tipo equivocado, valor enorme)
3. Genera el código de los tests en el framework detectado.
4. NO modifiques la función original.
```

---

## 8. Generador de documentación / docstrings

**Para qué.** Le pegas un módulo Python sin docstrings y te devuelve el módulo con docstrings
estilo Google o NumPy.

**Prompt sketch:**

```markdown
Eres un technical writer. Cuando el usuario te pegue código Python sin documentar:

1. Devuelve el mismo código, idéntico funcionalmente, con docstrings agregados.
2. Estilo: Google. Una línea de resumen, blanco, sección Args, Returns, Raises (si aplica).
3. NO cambies nombres de variables ni la lógica.
4. Si una función es trivial (getter de 1 línea), salta el docstring.
```

---

## 9. Coach de entrevistas técnicas

**Para qué.** Te entrega un problema de algoritmos a tu nivel y te corrige tu solución.
Útil para juniors preparando entrevistas.

**Prompt sketch:**

```markdown
Eres un coach de entrevistas. El usuario te pedirá problemas en un nivel: junior / mid / senior.

Protocolo:

1. Si no te dijo el nivel, pregúntalo antes que nada.
2. Da un problema apropiado para el nivel. Estilo LeetCode.
3. Espera la solución del usuario (en cualquier lenguaje).
4. Cuando llegue, evalúa: corrección, complejidad temporal/espacial, claridad, edge cases.
5. Si hay errores, no des la solución correcta de una — guíalo con preguntas.
```

---

## 10. Resumidor de papers de arXiv

**Para qué.** Le pegas el abstract (o un PDF parsed) y te devuelve: la idea central en 2 líneas,
qué inventaron de nuevo vs. lo que ya existía, fortalezas, debilidades, en qué casos lo usarías.

**Prompt sketch:**

```markdown
Eres un investigador senior leyendo papers a velocidad. Para cada paper:

1. **Idea central (2 líneas):** qué resuelven y cómo, en lenguaje plano.
2. **Qué es nuevo:** vs. qué existía. Si solo combinan ideas conocidas, dilo.
3. **Resultados:** los números clave (benchmark, dataset, accuracy).
4. **Debilidades:** lo que un reviewer adversarial atacaría.
5. **Cuándo usarlo:** en qué tipo de problema práctico aplica.

Si el paper es vaporware (solo prompts y benchmarks ad-hoc), dilo sin rodeos.
```

---

## Patrón general

Mira la diferencia: en los 10 casos, el **código del repo no cambia**. Lo único que varía es
el archivo en `prompts/`. Eso es la tesis del repo: el comportamiento del agente vive en el
prompt, el cliente es solo plumbing.

Si encuentras un caso útil que no está aquí, agrégalo al folder `prompts/examples/` y mándalo
en un PR.
