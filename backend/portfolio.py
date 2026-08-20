"""Portfolio-Manifest: kuratierte, freigegebene Fallstudien (Subsystem E).

Datei: <root>/portfolio/manifest.json
  {
    "schema_version": 1,
    "eintraege": [ <Eintrag>, ... ]
  }

Eintrag-Felder (alle Pflicht):
  id            -- eindeutiger Bezeichner (z.B. "p-001")
  quell_slug    -- Slug des Quell-Leads (intern, nicht zwingend oeffentlich)
  segment       -- Branchensegment (z.B. "Apotheke")
  problemtyp    -- Kurzbeschreibung des erkannten Problems
  muster        -- Name des wiederverwendbaren Loesung-Musters
  artefaktpfad  -- relativer Pfad zum Artefakt (z.B. "prototyp/<slug>")
  freigabestatus -- muss "portfolio_approved" sein
  anonymisiert  -- bool, muss True sein (Schutz vor Klarnamen-Leak)
  lernnotiz     -- warum dieser Eintrag aufgenommen wurde

Harte Regeln:
- Aufnahme nur mit freigabestatus == "portfolio_approved".
- anonymisiert muss True sein.
- Maximal 3 Eintraege.
- Doppelte IDs werden abgewiesen.

Startbedingungsgrenze (Stand: 2026-08-20):
  Die Produktionsbedingung (>=2 intern freigegebene Demos) ist noch nicht
  erfuellt. Das Manifest bleibt vorerst leer; Eintraege werden erst nach
  echter Demo-Freigabe im Cockpit hinzugefuegt.
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_VERSION = 1
MAX_EINTRAEGE = 3
PFLICHTFELDER = [
    "id",
    "quell_slug",
    "segment",
    "problemtyp",
    "muster",
    "artefaktpfad",
    "freigabestatus",
    "anonymisiert",
    "lernnotiz",
]


def _manifest_path(root: Path) -> Path:
    return root / "portfolio" / "manifest.json"


def load_manifest(root: Path) -> dict:
    """Laedt das Manifest. Gibt leeres Manifest zurueck, wenn keine Datei existiert."""
    p = _manifest_path(root)
    if not p.exists():
        return {"schema_version": SCHEMA_VERSION, "eintraege": []}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_manifest(root: Path, manifest: dict) -> None:
    p = _manifest_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _validate_schema(eintrag: dict) -> None:
    """Prueft Pflichtfelder. Wirft ValueError mit fehlendem Feldnamen."""
    for feld in PFLICHTFELDER:
        if feld not in eintrag:
            raise ValueError(
                f"Pflichtfeld '{feld}' fehlt im Portfolio-Eintrag."
            )


def _validate_freigabe(eintrag: dict) -> None:
    """Eintrag wird nur mit expliziter portfolio_approved-Entscheidung aufgenommen."""
    if eintrag.get("freigabestatus") != "portfolio_approved":
        raise ValueError(
            f"Eintrag '{eintrag.get('id')}' hat keinen gueltigen Freigabestatus "
            f"'portfolio_approved' (ist: '{eintrag.get('freigabestatus')}')."
        )


def _validate_anonymisierung(eintrag: dict) -> None:
    """anonymisiert==True ist Pflicht — Schutz vor versehentlichem Klarnamen-Leak."""
    if not eintrag.get("anonymisiert"):
        raise ValueError(
            f"Eintrag '{eintrag.get('id')}' muss anonymisiert==True haben. "
            "Originalnamen und externe Links werden nicht automatisch uebernommen."
        )


def add_entry(root: Path, eintrag: dict) -> dict:
    """Fuegt einen neuen Eintrag zum Manifest hinzu.

    Prueft Schema, Freigabe, Anonymisierung, Duplikate und Maximalanzahl.
    Gibt den gespeicherten Eintrag zurueck.
    """
    # 1. Schema-Validierung (Pflichtfelder)
    _validate_schema(eintrag)

    # 2. Freigabe-Check
    _validate_freigabe(eintrag)

    # 3. Anonymisierungs-Check
    _validate_anonymisierung(eintrag)

    manifest = load_manifest(root)
    eintraege = manifest["eintraege"]

    # 4. Doppel-ID-Check
    vorhandene_ids = {e["id"] for e in eintraege}
    if eintrag["id"] in vorhandene_ids:
        raise ValueError(
            f"Portfolio-Eintrag mit ID '{eintrag['id']}' existiert bereits."
        )

    # 5. Maximalanzahl (max. 3 hochwertige Eintraege)
    if len(eintraege) >= MAX_EINTRAEGE:
        raise ValueError(
            f"Portfolio ist voll: maximal {MAX_EINTRAEGE} Eintraege erlaubt. "
            "Bestehende Eintraege zuerst archivieren."
        )

    eintraege.append(eintrag)
    _save_manifest(root, manifest)
    return eintrag
