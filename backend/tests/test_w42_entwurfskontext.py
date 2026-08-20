"""W4.2 — Entwurfskontext faktengebunden.

Demo-Link nur wenn prototyp_state.status == 'published'.
save_request darf keinen demo_link mit draft_ready/approved_local speichern.
"""
import pytest
import outreach


def _save(root, slug, **kw):
    req = {
        "angebot": kw.get("angebot", "Website-Relaunch"),
        "nutzen": kw.get("nutzen", "mehr Anfragen"),
        "cta": kw.get("cta", "Telefonat"),
        "anlass": kw.get("anlass", "Seite veraltet"),
    }
    if "demo_link" in kw:
        req["demo_link"] = kw["demo_link"]
    if "prototyp_status" in kw:
        req["prototyp_status"] = kw["prototyp_status"]
    return outreach.save_request(root, slug, req)


# ---------------------------------------------------------------------------
# Demo-Link-Speicherung
# ---------------------------------------------------------------------------

def test_save_request_published_link_erlaubt(tmp_path):
    data = outreach.save_request(tmp_path, "sl1", {
        "angebot": "X",
        "demo_link": "https://shawn-jed.github.io/prototyp/sl1/",
        "prototyp_status": "published",
    })
    assert data["request"]["demo_link"] == "https://shawn-jed.github.io/prototyp/sl1/"
    assert data["request"]["prototyp_status"] == "published"


def test_save_request_draft_ready_link_wird_entfernt(tmp_path):
    """draft_ready -> kein demo_link gespeichert."""
    data = outreach.save_request(tmp_path, "sl2", {
        "angebot": "X",
        "demo_link": "https://shawn-jed.github.io/prototyp/sl2/",
        "prototyp_status": "draft_ready",
    })
    # Link muss entfernt sein
    assert not data["request"].get("demo_link")


def test_save_request_approved_local_link_wird_entfernt(tmp_path):
    data = outreach.save_request(tmp_path, "sl3", {
        "angebot": "X",
        "demo_link": "https://example.com",
        "prototyp_status": "approved_local",
    })
    assert not data["request"].get("demo_link")


def test_save_request_link_ohne_prototyp_status_wird_entfernt(tmp_path):
    """Kein prototyp_status gesetzt -> Link wird präventiv entfernt."""
    data = outreach.save_request(tmp_path, "sl4", {
        "angebot": "X",
        "demo_link": "https://example.com",
    })
    assert not data["request"].get("demo_link")


def test_save_request_kein_link_kein_status(tmp_path):
    """Ohne Link + ohne Status: kein Fehler, kein Link im Request."""
    data = outreach.save_request(tmp_path, "sl5", {"angebot": "X"})
    assert not data["request"].get("demo_link")


# ---------------------------------------------------------------------------
# Persistenz: Gespeichertes ist was gelesen wird
# ---------------------------------------------------------------------------

def test_save_request_persisted_correctly(tmp_path):
    outreach.save_request(tmp_path, "sl6", {
        "angebot": "Festpreis-Relaunch",
        "nutzen": "mehr Anfragen",
        "demo_link": "https://shawn-jed.github.io/prototyp/sl6/",
        "prototyp_status": "published",
    })
    loaded = outreach.load(tmp_path, "sl6")
    assert loaded["request"]["angebot"] == "Festpreis-Relaunch"
    assert loaded["request"]["demo_link"] == "https://shawn-jed.github.io/prototyp/sl6/"
