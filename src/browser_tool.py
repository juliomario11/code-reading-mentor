"""
Herramienta de navegación web con Playwright (headless Chromium).

Expone una función `browse_url(url)` que abre la URL en un Chromium
headless, extrae el texto visible de la página y lo devuelve truncado para
no saturar el contexto del LLM.

Pensada para ser llamada como *tool* por el agente de DO Gradient AI desde
`src/chat.py` — ver `src/tools.py` para el schema de la tool.
"""

from __future__ import annotations

from playwright.sync_api import sync_playwright

# Límite de caracteres devuelto al LLM. Suficiente para precios, titulares,
# tablas simples — sin reventar el contexto.
MAX_CHARS = 3000
PAGE_TIMEOUT_MS = 15000


def browse_url(url: str) -> str:
    """Visita una URL y retorna el texto visible de la página."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            page = browser.new_page()
            page.set_extra_http_headers({"Accept-Language": "es-CO,es;q=0.9"})
            page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
            text = page.evaluate("document.body.innerText")
            browser.close()
            return text[:MAX_CHARS]
    except Exception as e:
        return f"Error navegando {url}: {e}"
