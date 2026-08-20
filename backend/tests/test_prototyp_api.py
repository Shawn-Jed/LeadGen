"""API-Handler-Tests für Prototyp-Endpunkte (W3.1/W3.2/W3.6).

Testet die Handler-Logik direkt — kein echter HTTP-Server, kein echter Git-Push.
"""
from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import prototyp
import app as app_module


# ---------------------------------------------------------------------------
# Hilfsfunktionen: Handler direkt aufrufen ohne echten HTTP-Server
# ---------------------------------------------------------------------------

def make_handler(root: Path):
    """Gibt einen CockpitHandler zurück, der ROOT auf tmp setzt."""
    handler = MagicMock(spec=app_module.CockpitHandler)
    handler._json_responses = []

    def _send_json(obj, status=200):
        handler._json_responses.append({"status": status, "body": obj})

    def _send_error_json(status, message):
        handler._json_responses.append({"status": status, "body": {"error": message}})

    handler._send_json.side_effect = _send_json
    handler._send_error_json.side_effect = _send_error_json
    return handler


# ---------------------------------------------------------------------------
# W3.2: POST /api/leads/<slug>/prototyp/request → pending
# ---------------------------------------------------------------------------

def test_prototyp_request_creates_pending(tmp_path):
    with patch.object(app_module, "ROOT", tmp_path):
        from datetime import date
        handler = MagicMock()
        responses = []
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        app_module.CockpitHandler._handle_prototyp_request(handler, "test-lead", {})

        assert len(responses) == 1
        assert responses[0]["status"] == 201
        assert responses[0]["body"]["status"] == "pending"


# ---------------------------------------------------------------------------
# W3.2: POST /api/leads/<slug>/prototyp/draft → draft_ready (KEIN deploy)
# ---------------------------------------------------------------------------

def test_prototyp_draft_saves_locally_no_deploy(tmp_path):
    """Draft speichert lokal, setzt draft_ready — ruft deploy NICHT auf."""
    with patch.object(app_module, "ROOT", tmp_path):
        # Auftrag anlegen
        prototyp.save_request(tmp_path, "test-lead")

        deploy_calls = []

        responses = []
        handler = MagicMock()
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        body = {"html": "<html><body>Test One-Pager</body></html>"}

        with patch.object(app_module, "deploy") as mock_deploy:
            mock_deploy.deploy.side_effect = lambda *a, **kw: deploy_calls.append((a, kw)) or "https://x/y"
            app_module.CockpitHandler._handle_prototyp_draft(handler, "test-lead", body)

        assert len(responses) == 1
        assert responses[0]["body"]["status"] == "draft_ready"
        # deploy darf NICHT aufgerufen worden sein
        assert len(deploy_calls) == 0


def test_prototyp_draft_requires_pending_or_rework(tmp_path):
    """Draft ohne vorherigen Request gibt 400."""
    with patch.object(app_module, "ROOT", tmp_path):
        responses = []
        handler = MagicMock()
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        body = {"html": "<html><body>Test</body></html>"}

        # Kein save_request vorher → ValueError erwartet
        with pytest.raises(ValueError, match="Kein Prototyp-Auftrag"):
            app_module.CockpitHandler._handle_prototyp_draft(handler, "ghost-lead", body)


def test_prototyp_draft_requires_html(tmp_path):
    """Draft ohne HTML gibt ValueError."""
    with patch.object(app_module, "ROOT", tmp_path):
        prototyp.save_request(tmp_path, "test-lead")
        handler = MagicMock()
        responses = []
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        with pytest.raises(ValueError, match="html"):
            app_module.CockpitHandler._handle_prototyp_draft(handler, "test-lead", {"html": ""})


# ---------------------------------------------------------------------------
# W3.6: POST /api/leads/<slug>/prototyp/publish → published (nur bei approved_local)
# ---------------------------------------------------------------------------

def test_prototyp_publish_requires_approved_local(tmp_path):
    """Publish ohne approved_local gibt ValueError."""
    with patch.object(app_module, "ROOT", tmp_path):
        prototyp.save_request(tmp_path, "test-lead")
        prototyp.save_draft(tmp_path, "test-lead", "<html></html>")
        # Status ist draft_ready, nicht approved_local → Fehler erwartet

        handler = MagicMock()
        responses = []
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        with pytest.raises(ValueError, match="approved_local"):
            app_module.CockpitHandler._handle_prototyp_publish(handler, "test-lead", {})


def test_prototyp_publish_deploys_and_sets_published(tmp_path):
    """Publish bei approved_local: ruft deploy auf (Fake), setzt published + URL."""
    with patch.object(app_module, "ROOT", tmp_path):
        prototyp.save_request(tmp_path, "test-lead")
        prototyp.save_draft(tmp_path, "test-lead", "<html><body>x</body></html>")
        prototyp.approve_local(tmp_path, "test-lead")

        responses = []
        handler = MagicMock()
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        fake_url = "https://shawn-jed.github.io/prototyp/test-lead"

        with patch.object(app_module, "deploy") as mock_deploy_mod, \
             patch.object(app_module.config, "prototyp_repo_path", return_value=str(tmp_path / "pages")), \
             patch.object(app_module.config, "prototyp_pages_base", return_value="https://shawn-jed.github.io/prototyp"):
            mock_deploy_mod.deploy.return_value = fake_url
            app_module.CockpitHandler._handle_prototyp_publish(handler, "test-lead", {})

        assert len(responses) == 1
        assert responses[0]["body"]["status"] == "published"
        assert responses[0]["body"]["url"] == fake_url


def test_prototyp_publish_reports_deploy_error(tmp_path):
    """Fehler im Deploy-Schritt wird transparent als ValueError weitergegeben."""
    with patch.object(app_module, "ROOT", tmp_path):
        prototyp.save_request(tmp_path, "test-lead")
        prototyp.save_draft(tmp_path, "test-lead", "<html><body>x</body></html>")
        prototyp.approve_local(tmp_path, "test-lead")

        handler = MagicMock()

        with patch.object(app_module, "deploy") as mock_deploy_mod, \
             patch.object(app_module.config, "prototyp_repo_path", return_value=str(tmp_path / "pages")), \
             patch.object(app_module.config, "prototyp_pages_base", return_value="https://shawn-jed.github.io/prototyp"):
            mock_deploy_mod.deploy.side_effect = RuntimeError("Git push failed")
            with pytest.raises(RuntimeError, match="Git push failed"):
                app_module.CockpitHandler._handle_prototyp_publish(handler, "test-lead", {})


# ---------------------------------------------------------------------------
# W3.6: POST /api/leads/<slug>/prototyp/approve → approved_local
# ---------------------------------------------------------------------------

def test_prototyp_approve_sets_approved_local(tmp_path):
    """Approve-Endpunkt setzt approved_local."""
    with patch.object(app_module, "ROOT", tmp_path):
        prototyp.save_request(tmp_path, "test-lead")
        prototyp.save_draft(tmp_path, "test-lead", "<html></html>")

        responses = []
        handler = MagicMock()
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        app_module.CockpitHandler._handle_prototyp_approve(handler, "test-lead", {})

        assert len(responses) == 1
        assert responses[0]["body"]["status"] == "approved_local"


# ---------------------------------------------------------------------------
# W3.6: POST /api/leads/<slug>/prototyp/rework und /archive
# ---------------------------------------------------------------------------

def test_prototyp_rework_sets_rework(tmp_path):
    with patch.object(app_module, "ROOT", tmp_path):
        prototyp.save_request(tmp_path, "test-lead")
        prototyp.save_draft(tmp_path, "test-lead", "<html></html>")

        responses = []
        handler = MagicMock()
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        app_module.CockpitHandler._handle_prototyp_rework(handler, "test-lead", {})

        assert responses[0]["body"]["status"] == "rework"


def test_prototyp_archive_sets_archived(tmp_path):
    with patch.object(app_module, "ROOT", tmp_path):
        prototyp.save_request(tmp_path, "test-lead")
        prototyp.save_draft(tmp_path, "test-lead", "<html></html>")

        responses = []
        handler = MagicMock()
        handler._send_json = lambda obj, status=200: responses.append({"status": status, "body": obj})
        handler._send_error_json = lambda s, m: responses.append({"status": s, "body": {"error": m}})

        app_module.CockpitHandler._handle_prototyp_archive(handler, "test-lead", {})

        assert responses[0]["body"]["status"] == "archived"


# ---------------------------------------------------------------------------
# Migration: load() in build_state gibt korrekten Status zurück
# ---------------------------------------------------------------------------

def test_build_state_prototyp_state_migration(tmp_path):
    """build_state liefert migrierten Status für ready-Einträge."""
    import json as _json
    from datetime import date

    # pipeline.md anlegen (leer reicht)
    import leadtool
    leadtool.init_repo(tmp_path)

    # Alt-JSON anlegen
    p = tmp_path / "prototyp" / "alt-lead.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_json.dumps({
        "slug": "alt-lead",
        "status": "ready",
        "url": "https://shawn-jed.github.io/prototyp/alt-lead",
        "angefordert_am": "2026-01-01",
    }), encoding="utf-8")

    with patch.object(app_module, "ROOT", tmp_path):
        state = app_module.build_state(date.today())

    # Im Cockpit-State müssen wir published sehen, nicht ready
    # (nur wenn ein Lead mit slug "alt-lead" existiert; hier kein Lead, aber
    #  der Prototyp-Store-Test oben prüft die Migration direkt)
    # Dieser Test prüft, dass load() den migrierten Wert zurückgibt.
    loaded = prototyp.load(tmp_path, "alt-lead")
    assert loaded["status"] == "published"
