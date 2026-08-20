"""Store-Tests für kanonische Demo-Zustandsmaschine (W3.1 + W3.2 + W3.6)."""
import pytest

import prototyp


# ---------------------------------------------------------------------------
# Grundlegende Übergänge (kanonisch)
# ---------------------------------------------------------------------------

def test_save_request_creates_pending(tmp_path):
    data = prototyp.save_request(tmp_path, "lead-x")
    assert data["status"] == "pending"
    assert data["url"] is None
    assert prototyp.load(tmp_path, "lead-x")["status"] == "pending"


def test_mark_draft_ready_from_pending(tmp_path):
    prototyp.save_request(tmp_path, "lead-x")
    html = "<html><body>Demo</body></html>"
    data = prototyp.save_draft(tmp_path, "lead-x", html)
    assert data["status"] == "draft_ready"
    assert data["url"] is None
    loaded = prototyp.load(tmp_path, "lead-x")
    assert loaded["status"] == "draft_ready"
    assert loaded["html_local"] == html


def test_save_draft_without_request_raises(tmp_path):
    with pytest.raises(ValueError, match="Kein Prototyp-Auftrag"):
        prototyp.save_draft(tmp_path, "ghost", "<html></html>")


def test_approve_local_from_draft_ready(tmp_path):
    prototyp.save_request(tmp_path, "lead-x")
    prototyp.save_draft(tmp_path, "lead-x", "<html></html>")
    data = prototyp.approve_local(tmp_path, "lead-x")
    assert data["status"] == "approved_local"


def test_approve_local_requires_draft_ready(tmp_path):
    prototyp.save_request(tmp_path, "lead-x")
    with pytest.raises(ValueError, match="draft_ready"):
        prototyp.approve_local(tmp_path, "lead-x")


def test_mark_published_from_approved_local(tmp_path):
    prototyp.save_request(tmp_path, "lead-x")
    prototyp.save_draft(tmp_path, "lead-x", "<html></html>")
    prototyp.approve_local(tmp_path, "lead-x")
    data = prototyp.mark_published(tmp_path, "lead-x", "https://example.com/lead-x")
    assert data["status"] == "published"
    assert data["url"] == "https://example.com/lead-x"


def test_mark_published_requires_approved_local(tmp_path):
    prototyp.save_request(tmp_path, "lead-x")
    prototyp.save_draft(tmp_path, "lead-x", "<html></html>")
    with pytest.raises(ValueError, match="approved_local"):
        prototyp.mark_published(tmp_path, "lead-x", "https://example.com/lead-x")


def test_mark_published_without_request_raises(tmp_path):
    with pytest.raises(ValueError, match="Kein Prototyp-Auftrag"):
        prototyp.mark_published(tmp_path, "ghost", "https://x")


def test_mark_rework_from_draft_ready(tmp_path):
    prototyp.save_request(tmp_path, "lead-x")
    prototyp.save_draft(tmp_path, "lead-x", "<html></html>")
    data = prototyp.mark_rework(tmp_path, "lead-x")
    assert data["status"] == "rework"


def test_mark_archived(tmp_path):
    prototyp.save_request(tmp_path, "lead-x")
    prototyp.save_draft(tmp_path, "lead-x", "<html></html>")
    data = prototyp.mark_archived(tmp_path, "lead-x")
    assert data["status"] == "archived"


def test_mark_archived_without_request_raises(tmp_path):
    with pytest.raises(ValueError, match="Kein Prototyp-Auftrag"):
        prototyp.mark_archived(tmp_path, "ghost")


# ---------------------------------------------------------------------------
# list_pending — nur pending
# ---------------------------------------------------------------------------

def test_list_pending_only_pending(tmp_path):
    prototyp.save_request(tmp_path, "a")
    prototyp.save_request(tmp_path, "b")
    prototyp.save_draft(tmp_path, "b", "<html></html>")
    pending = prototyp.list_pending(tmp_path)
    assert [p["slug"] for p in pending] == ["a"]


def test_load_missing_returns_none(tmp_path):
    assert prototyp.load(tmp_path, "nope") is None


# ---------------------------------------------------------------------------
# W3.1 Migration: Alt-Wert `ready`
# ---------------------------------------------------------------------------

def test_migration_ready_with_url_becomes_published(tmp_path):
    """Alt-Datei mit status=ready + url → published beim Laden."""
    import json
    p = tmp_path / "prototyp" / "old-lead.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "slug": "old-lead",
        "status": "ready",
        "url": "https://shawn-jed.github.io/prototyp/old-lead",
        "angefordert_am": "2026-01-01",
    }), encoding="utf-8")
    data = prototyp.load(tmp_path, "old-lead")
    assert data["status"] == "published"
    assert data["url"] == "https://shawn-jed.github.io/prototyp/old-lead"


def test_migration_ready_without_url_becomes_draft_ready(tmp_path):
    """Alt-Datei mit status=ready, url=None → draft_ready beim Laden."""
    import json
    p = tmp_path / "prototyp" / "old-lead2.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "slug": "old-lead2",
        "status": "ready",
        "url": None,
        "angefordert_am": "2026-01-01",
    }), encoding="utf-8")
    data = prototyp.load(tmp_path, "old-lead2")
    assert data["status"] == "draft_ready"


def test_migration_unknown_status_preserved(tmp_path):
    """Unbekannte Status-Werte werden nicht verworfen — kein Datenverlust."""
    import json
    p = tmp_path / "prototyp" / "weird.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "slug": "weird",
        "status": "some_future_state",
        "url": None,
        "angefordert_am": None,
    }), encoding="utf-8")
    data = prototyp.load(tmp_path, "weird")
    assert data["status"] == "some_future_state"


def test_migration_does_not_write_file(tmp_path):
    """Migration beim load() schreibt NICHT in die Datei (nur in-memory)."""
    import json
    p = tmp_path / "prototyp" / "old-lead3.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps({
        "slug": "old-lead3",
        "status": "ready",
        "url": None,
        "angefordert_am": None,
    })
    p.write_text(raw, encoding="utf-8")
    prototyp.load(tmp_path, "old-lead3")
    # Datei muss noch den Original-Wert haben
    on_disk = json.loads(p.read_text(encoding="utf-8"))
    assert on_disk["status"] == "ready"


# ---------------------------------------------------------------------------
# W3.1 list_pending bei Migration (ready ohne URL zählt als pending-ähnlich,
# aber list_pending soll nur echte pending liefern)
# ---------------------------------------------------------------------------

def test_list_pending_ignores_migrated_ready(tmp_path):
    """list_pending liefert keine alten ready-Einträge."""
    import json
    p = tmp_path / "prototyp" / "alt.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "slug": "alt", "status": "ready", "url": None, "angefordert_am": None
    }), encoding="utf-8")
    prototyp.save_request(tmp_path, "neu")
    pending = prototyp.list_pending(tmp_path)
    assert len(pending) == 1
    assert pending[0]["slug"] == "neu"
