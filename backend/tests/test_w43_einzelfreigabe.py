"""W4.3 — Einzel-Freigabe: injizierter Mailer, Negativfälle, Doppelversand.

Kein echtes SMTP. Alle Sendetests injizieren einen FakeSMTP oder nutzen draft-Modus.
"""
import datetime
import pytest

import leadtool
import outreach
import mailer

TODAY = datetime.date(2026, 8, 20)


# ---------------------------------------------------------------------------
# Hilfsfunktionen / Fixtures
# ---------------------------------------------------------------------------

def _setup_warm_lead(repo, slug="betrieb-x", email="info@betrieb.de"):
    leadtool.add_lead(repo, "Betrieb X GmbH", schwaeche="veraltet", today=TODAY)
    # Slug ableiten wie leadtool es tut
    actual_slug = leadtool.slugify("Betrieb X GmbH")
    leadtool.set_status(repo, actual_slug, "in_klaerung", today=TODAY)
    leadtool.set_email(repo, actual_slug, email)
    return actual_slug


def _make_ready(root, slug):
    """Legt pending + ready-Entwurf an."""
    outreach.save_request(root, slug, {"angebot": "Website-Relaunch"})
    outreach.set_draft(root, slug, "Ihr Web-Auftritt", "Hallo,\n…\nVG Shawn")


class FakeMailer:
    def __init__(self):
        self.calls = []

    def deliver(self, msg, *, mode, cfg, eml_path, smtp_factory=None):
        self.calls.append({"mode": mode, "to": msg["To"], "subject": msg["Subject"]})
        if mode == "draft":
            import pathlib
            eml_path = pathlib.Path(eml_path)
            eml_path.parent.mkdir(parents=True, exist_ok=True)
            eml_path.write_bytes(bytes(msg))
            return {"mode": "draft", "eml": str(eml_path)}
        return {"mode": "direct"}


# ---------------------------------------------------------------------------
# W4.3a: fehlende E-Mail-Adresse wird abgewiesen
# ---------------------------------------------------------------------------

def test_send_abgewiesen_ohne_email(repo):
    slug = _setup_warm_lead(repo)
    # E-Mail wieder entfernen: direkt im Frontmatter löschen (Ausnahme: Test-Setup)
    meta, body = leadtool.read_lead(repo, slug)
    meta["kontakt"]["email"] = ""
    leadtool.write_lead(repo, slug, meta, body)

    _make_ready(repo, slug)

    state = outreach.load(repo, slug)
    assert state["status"] == "ready"

    # Direkte Backend-Logik testen: send muss ValueError werfen wenn kein email
    with pytest.raises(ValueError, match="[Mm]ail|[Aa]dress"):
        outreach.validate_send(repo, slug)


# ---------------------------------------------------------------------------
# W4.3b: Doppelversand wird abgewiesen
# ---------------------------------------------------------------------------

def test_doppelversand_abgewiesen(repo):
    slug = _setup_warm_lead(repo)
    _make_ready(repo, slug)
    outreach.mark_sent(repo, slug)

    with pytest.raises(ValueError, match="[Ss]ent|[Gg]esendet|[Bb]ereits"):
        outreach.validate_send(repo, slug)


# ---------------------------------------------------------------------------
# W4.3c: draft bleibt Default
# ---------------------------------------------------------------------------

def test_send_draft_schreibt_eml(repo, tmp_path):
    slug = _setup_warm_lead(repo)
    _make_ready(repo, slug)

    state = outreach.load(repo, slug)
    draft = state["draft"]
    meta, _ = leadtool.read_lead(repo, slug)
    to_addr = meta["kontakt"]["email"]

    msg = mailer.build_message(
        from_addr="shawn@example.com",
        to_addr=to_addr,
        subject=draft["betreff"],
        body=draft["text"],
    )
    eml_path = tmp_path / "outreach" / f"{slug}.eml"
    result = mailer.deliver(msg, mode="draft", cfg={}, eml_path=eml_path)
    assert result["mode"] == "draft"
    assert eml_path.exists()
    content = eml_path.read_bytes()
    assert b"Subject:" in content
    assert to_addr.encode() in content


# ---------------------------------------------------------------------------
# W4.3d: direct-Modus sendet via injiziertem SMTP
# ---------------------------------------------------------------------------

def test_send_direct_injizierter_mailer(repo, tmp_path):
    slug = _setup_warm_lead(repo)
    _make_ready(repo, slug)

    sent = {}

    class FakeSMTP:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): sent["tls"] = True
        def login(self, u, p): sent["login"] = (u, p)
        def send_message(self, m): sent["msg"] = m

    state = outreach.load(repo, slug)
    draft = state["draft"]
    meta, _ = leadtool.read_lead(repo, slug)
    to_addr = meta["kontakt"]["email"]

    msg = mailer.build_message(
        from_addr="shawn@example.com",
        to_addr=to_addr,
        subject=draft["betreff"],
        body=draft["text"],
    )
    cfg = {"host": "smtp.example.com", "port": 587, "user": "u", "password": "pw",
           "from_addr": "shawn@example.com"}
    result = mailer.deliver(msg, mode="direct", cfg=cfg,
                            eml_path=tmp_path / "x.eml",
                            smtp_factory=lambda: FakeSMTP())
    assert result["mode"] == "direct"
    assert sent.get("tls") is True
    assert sent.get("msg") is msg


# ---------------------------------------------------------------------------
# W4.3e: validate_send - kein Entwurf vorhanden
# ---------------------------------------------------------------------------

def test_validate_send_kein_entwurf(repo):
    slug = _setup_warm_lead(repo)
    # Kein outreach-Datensatz angelegt
    with pytest.raises((ValueError, FileNotFoundError)):
        outreach.validate_send(repo, slug)


def test_validate_send_nur_pending(repo):
    slug = _setup_warm_lead(repo)
    outreach.save_request(repo, slug, {"angebot": "X"})
    # pending, kein draft
    with pytest.raises(ValueError, match="[Ee]ntwurf|[Dd]raft|[Ff]ertig"):
        outreach.validate_send(repo, slug)
