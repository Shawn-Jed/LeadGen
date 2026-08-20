"""W5.3 Portfolio-API-Tests: GET /api/portfolio.

TDD-Reihenfolge: Tests zuerst.

Testet:
  1. Leeres Manifest → leere Einträgsliste
  2. Synthetischer Eintrag (via portfolio.add_entry in Fixture) → Eintrag erscheint in Antwort
"""
import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

# Backend-Verzeichnis für Import
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import portfolio


# ---------------------------------------------------------------------------
# Hilfsfixture: minimaler gültiger Eintrag
# ---------------------------------------------------------------------------

def _approved_entry(id_="p-001"):
    return {
        "id": id_,
        "quell_slug": "muster-apotheke-x",
        "segment": "Apotheke",
        "problemtyp": "Kein Online-Buchungssystem",
        "muster": "Terminbuchungs-Widget One-Pager",
        "artefaktpfad": "prototyp/muster-apotheke-x",
        "freigabestatus": "portfolio_approved",
        "anonymisiert": True,
        "lernnotiz": "Zeigt, dass ein einfacher CTA-Button die Konversion erhoeht.",
    }


# ---------------------------------------------------------------------------
# Hilfsfunktion: minimaler HTTP-Handler für den Portfolio-Endpunkt
# ---------------------------------------------------------------------------

def _make_handler(root: Path):
    """Erzeugt einen Request-Handler, der nur GET /api/portfolio bedient."""
    import app as app_module

    # ROOT-Patch: app_module.ROOT muss auf tmp_path zeigen
    class _PortfolioHandler(app_module.CockpitHandler):
        # Logging unterdrücken
        def log_message(self, fmt, *args):
            pass

    # Wir nutzen den echten CockpitHandler-Code, aber patchen ROOT im Handler
    original_root = app_module.ROOT

    class PatchedHandler(_PortfolioHandler):
        def do_GET(self):
            import app as _app
            _app.ROOT = root
            try:
                super().do_GET()
            finally:
                _app.ROOT = original_root

    return PatchedHandler


def _portfolio_get(root: Path) -> dict:
    """Startet einen Einweg-HTTP-Server auf einem freien Port, ruft /api/portfolio ab."""
    import app as app_module

    Handler = _make_handler(root)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        url = f"http://127.0.0.1:{port}/api/portfolio"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    finally:
        server.shutdown()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_portfolio_api_leer(tmp_path):
    """GET /api/portfolio bei leerem Manifest → leere Einträgsliste."""
    result = _portfolio_get(tmp_path)
    assert isinstance(result, dict)
    assert result.get("eintraege") == []
    assert result.get("schema_version") == 1


def test_portfolio_api_mit_eintrag(tmp_path):
    """GET /api/portfolio mit synthetischem Eintrag → Eintrag erscheint."""
    portfolio.add_entry(tmp_path, _approved_entry())
    result = _portfolio_get(tmp_path)
    assert len(result["eintraege"]) == 1
    e = result["eintraege"][0]
    assert e["id"] == "p-001"
    assert e["problemtyp"] == "Kein Online-Buchungssystem"
    assert e["muster"] == "Terminbuchungs-Widget One-Pager"
    assert e["artefaktpfad"] == "prototyp/muster-apotheke-x"
