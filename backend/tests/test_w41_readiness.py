"""W4.1 — outreach_readiness: Kontakt-Readiness-Checkliste.

Pflichtpunkte:
  - warm (oder kalt_freigegeben)
  - email vorhanden
  - anlass (sachlicher Anlass)
  - angebot
  - nutzen
  - cta

Optional: demo_link nur wenn prototyp_state.status == 'published'.
"""
import outreach


def _lead(warm=True, email="a@b.de", **kw):
    """Minimales Lead-Dict für Readiness-Tests."""
    base = {
        "warm": warm,
        "kontakt": {"email": email},
        "prototyp_state": {"status": "none", "url": None},
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------------------
# Positiv: vollständiger Lead
# ---------------------------------------------------------------------------

def test_readiness_ok_all_fields():
    lead = _lead(
        anlass="Website veraltet seit 2018",
        angebot="Website-Relaunch Festpreis",
        nutzen="mehr Anfragen über Mobilgeräte",
        cta="15-Minuten-Telefonat",
    )
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is True
    assert r["fehlend"] == []


# ---------------------------------------------------------------------------
# Negativfälle: jeder Pflichtpunkt einzeln
# ---------------------------------------------------------------------------

def test_readiness_kalt_ohne_freigabe():
    lead = _lead(
        warm=False,
        anlass="X", angebot="X", nutzen="X", cta="X",
    )
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is False
    assert any("warm" in f.lower() or "freigabe" in f.lower() or "kalt" in f.lower()
               for f in r["fehlend"])


def test_readiness_kalt_mit_expliziter_freigabe():
    lead = _lead(
        warm=False,
        kalt_freigegeben=True,
        anlass="X", angebot="X", nutzen="X", cta="X",
    )
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is True


def test_readiness_fehlende_email():
    lead = _lead(
        email="",
        anlass="X", angebot="X", nutzen="X", cta="X",
    )
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is False
    assert any("mail" in f.lower() or "adresse" in f.lower() for f in r["fehlend"])


def test_readiness_fehlender_anlass():
    lead = _lead(angebot="X", nutzen="X", cta="X")
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is False
    assert any("anlass" in f.lower() for f in r["fehlend"])


def test_readiness_fehlendes_angebot():
    lead = _lead(anlass="X", nutzen="X", cta="X")
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is False
    assert any("angebot" in f.lower() for f in r["fehlend"])


def test_readiness_fehlender_nutzen():
    lead = _lead(anlass="X", angebot="X", cta="X")
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is False
    assert any("nutzen" in f.lower() for f in r["fehlend"])


def test_readiness_fehlende_cta():
    lead = _lead(anlass="X", angebot="X", nutzen="X")
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is False
    assert any("cta" in f.lower() or "call" in f.lower() or "aktion" in f.lower()
               for f in r["fehlend"])


def test_readiness_mehrere_fehlend():
    lead = _lead(email="")
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is False
    assert len(r["fehlend"]) >= 3  # email + anlass + angebot + nutzen + cta


# ---------------------------------------------------------------------------
# Demo-Link-Regel (optional, nur published)
# ---------------------------------------------------------------------------

def test_readiness_demo_link_published_ok():
    lead = _lead(
        anlass="X", angebot="X", nutzen="X", cta="X",
        prototyp_state={"status": "published", "url": "https://example.com/demo"},
    )
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is True
    assert r.get("demo_link") == "https://example.com/demo"


def test_readiness_demo_link_draft_ready_kein_link():
    lead = _lead(
        anlass="X", angebot="X", nutzen="X", cta="X",
        prototyp_state={"status": "draft_ready", "url": "https://example.com/demo"},
    )
    r = outreach.outreach_readiness(lead)
    # Demo-Link darf NICHT im Ergebnis stehen
    assert r.get("demo_link") is None


def test_readiness_demo_link_approved_local_kein_link():
    lead = _lead(
        anlass="X", angebot="X", nutzen="X", cta="X",
        prototyp_state={"status": "approved_local", "url": "https://example.com/demo"},
    )
    r = outreach.outreach_readiness(lead)
    assert r.get("demo_link") is None


def test_readiness_demo_link_none_status():
    lead = _lead(
        anlass="X", angebot="X", nutzen="X", cta="X",
        prototyp_state={"status": "none", "url": None},
    )
    r = outreach.outreach_readiness(lead)
    assert r["ok"] is True
    assert r.get("demo_link") is None
