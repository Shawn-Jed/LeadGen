"""Portfolio-Manifest-Tests (W5.1 + W5.2).

TDD-Reihenfolge: Tests zuerst geschrieben, Implementierung folgt.

Testdaten: Synthetische Fixtures — kein echter Lead/Demo im Manifest.
Startbedingungsgrenze: Die echte Startbedingung (>=2 intern freigegebene Demos)
ist noch nicht erfuellt (Stand: 2026-08-20). Daher rein strukturelle Tests
mit synthetischen Daten. Kein echter Produktionseintrag wird angelegt.
"""
import json
import pytest

import portfolio


# ---------------------------------------------------------------------------
# Hilfsfixture: minimaler gueltig-freigegebener Eintrag
# ---------------------------------------------------------------------------

def _approved_entry():
    return {
        "id": "p-001",
        "quell_slug": "muster-apotheke-x",
        "segment": "Apotheke",
        "problemtyp": "Kein Online-Buchungssystem",
        "muster": "Terminbuchungs-Widget One-Pager",
        "artefaktpfad": "prototyp/muster-apotheke-x",
        "freigabestatus": "portfolio_approved",
        "anonymisiert": True,
        "lernnotiz": "Zeigt, dass ein einfacher CTA-Button die Konversion erhoeht.",
    }


def _rejected_entry():
    """Eintrag ohne Freigabe — soll abgewiesen werden."""
    return {
        "id": "p-002",
        "quell_slug": "nicht-freigegeben-y",
        "segment": "Pflegedienst",
        "problemtyp": "Keine Mobile-Seite",
        "muster": "Responsive Landingpage",
        "artefaktpfad": "prototyp/nicht-freigegeben-y",
        "freigabestatus": "draft_ready",          # KEIN portfolio_approved
        "anonymisiert": True,
        "lernnotiz": "Noch nicht bereit.",
    }


# ---------------------------------------------------------------------------
# W5.1 load_manifest — leere + initialisierte Manifeste
# ---------------------------------------------------------------------------

def test_load_manifest_leer_wenn_keine_datei(tmp_path):
    m = portfolio.load_manifest(tmp_path)
    assert m["schema_version"] == 1
    assert m["eintraege"] == []


def test_load_manifest_liest_bestehende_datei(tmp_path):
    daten = {
        "schema_version": 1,
        "eintraege": [_approved_entry()],
    }
    p = tmp_path / "portfolio" / "manifest.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(daten), encoding="utf-8")
    m = portfolio.load_manifest(tmp_path)
    assert len(m["eintraege"]) == 1
    assert m["eintraege"][0]["id"] == "p-001"


# ---------------------------------------------------------------------------
# W5.1 Schema-Validierung: Pflichtfelder
# ---------------------------------------------------------------------------

PFLICHTFELDER = [
    "id", "quell_slug", "segment", "problemtyp", "muster",
    "artefaktpfad", "freigabestatus", "anonymisiert", "lernnotiz",
]

@pytest.mark.parametrize("fehlendes_feld", PFLICHTFELDER)
def test_add_entry_fehlendes_pflichtfeld_raises(tmp_path, fehlendes_feld):
    eintrag = _approved_entry()
    del eintrag[fehlendes_feld]
    with pytest.raises(ValueError, match=fehlendes_feld):
        portfolio.add_entry(tmp_path, eintrag)


# ---------------------------------------------------------------------------
# W5.2 Auswahlprozess: nur portfolio_approved wird aufgenommen
# ---------------------------------------------------------------------------

def test_add_entry_approved_anonymisiert_wird_aufgenommen(tmp_path):
    """Freigegeben + anonymisiert → Aufnahme."""
    eintrag = _approved_entry()
    portfolio.add_entry(tmp_path, eintrag)
    m = portfolio.load_manifest(tmp_path)
    assert len(m["eintraege"]) == 1
    assert m["eintraege"][0]["id"] == "p-001"


def test_add_entry_ohne_freigabe_wird_abgewiesen(tmp_path):
    """Nicht freigegebener Eintrag → ValueError."""
    eintrag = _rejected_entry()
    with pytest.raises(ValueError, match="portfolio_approved"):
        portfolio.add_entry(tmp_path, eintrag)


def test_add_entry_unbekannter_freigabestatus_wird_abgewiesen(tmp_path):
    """Unbekannter Freigabestatus → ValueError."""
    eintrag = _approved_entry()
    eintrag["freigabestatus"] = "irgendwas"
    with pytest.raises(ValueError, match="portfolio_approved"):
        portfolio.add_entry(tmp_path, eintrag)


# ---------------------------------------------------------------------------
# W5.2 Anonymisierung: anonymisiert==True muss gesetzt sein
# ---------------------------------------------------------------------------

def test_add_entry_nicht_anonymisiert_wird_abgewiesen(tmp_path):
    """anonymisiert==False → ValueError (Schutz vor versehentlichem Klarnamen)."""
    eintrag = _approved_entry()
    eintrag["anonymisiert"] = False
    with pytest.raises(ValueError, match="anonymisiert"):
        portfolio.add_entry(tmp_path, eintrag)


# ---------------------------------------------------------------------------
# W5.2 Maximale Eintragsanzahl: max. 3 hochwertige Eintraege
# ---------------------------------------------------------------------------

def test_add_entry_vierter_eintrag_wird_abgewiesen(tmp_path):
    """Mehr als 3 Eintraege → ValueError."""
    for i in range(1, 4):
        e = _approved_entry()
        e["id"] = f"p-{i:03d}"
        portfolio.add_entry(tmp_path, e)
    vierter = _approved_entry()
    vierter["id"] = "p-004"
    with pytest.raises(ValueError, match="3"):
        portfolio.add_entry(tmp_path, vierter)


# ---------------------------------------------------------------------------
# W5.2 Doppel-IDs werden abgewiesen
# ---------------------------------------------------------------------------

def test_add_entry_doppelte_id_wird_abgewiesen(tmp_path):
    portfolio.add_entry(tmp_path, _approved_entry())
    with pytest.raises(ValueError, match="p-001"):
        portfolio.add_entry(tmp_path, _approved_entry())


# ---------------------------------------------------------------------------
# Persistenz: Manifest wird auf Disk gespeichert
# ---------------------------------------------------------------------------

def test_add_entry_schreibt_auf_disk(tmp_path):
    portfolio.add_entry(tmp_path, _approved_entry())
    p = tmp_path / "portfolio" / "manifest.json"
    assert p.exists()
    daten = json.loads(p.read_text(encoding="utf-8"))
    assert daten["schema_version"] == 1
    assert len(daten["eintraege"]) == 1
