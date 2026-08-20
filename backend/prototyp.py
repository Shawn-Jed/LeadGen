"""Prototyp-Zustand pro Lead als JSON: kanonische Demo-Zustandsmaschine.

Datei: <root>/prototyp/<slug>.json
  {
    "slug": str,
    "status": str,          # none|pending|draft_ready|approved_local|published|rework|archived
    "url": str|None,        # gesetzt nach published
    "html_local": str|None, # lokal gespeichertes HTML nach draft_ready
    "angefordert_am": str|None,
  }

Alt-Wert `ready` wird beim Laden migriert (nur in-memory, kein Schreiben):
  - ready + url gesetzt  → published
  - ready + url fehlt    → draft_ready

Slug-basiert — unabhängig davon, ob der Lead kalt (pipeline.md) oder warm
(leads/<slug>.md) ist. Spiegelt outreach.py.
"""
from __future__ import annotations

import json
from pathlib import Path

# Kanonische Statuswerte
VALID_STATUSES = frozenset({
    "none", "pending", "draft_ready", "approved_local", "published", "rework", "archived",
})


def _dir(root: Path) -> Path:
    return root / "prototyp"


def path(root: Path, slug: str) -> Path:
    return _dir(root) / f"{slug}.json"


def _migrate(data: dict) -> dict:
    """Migriert Alt-Wert `ready` → published oder draft_ready (in-memory, kein Disk-Write)."""
    if data.get("status") == "ready":
        if data.get("url"):
            data = {**data, "status": "published"}
        else:
            data = {**data, "status": "draft_ready"}
    return data


def load(root: Path, slug: str) -> dict | None:
    p = path(root, slug)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return _migrate(data)


def _save(root: Path, slug: str, data: dict) -> None:
    p = path(root, slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_request(root: Path, slug: str, today=None) -> dict:
    """Legt einen neuen Prototyp-Auftrag an (Status: pending)."""
    data = {
        "slug": slug,
        "status": "pending",
        "url": None,
        "html_local": None,
        "angefordert_am": today.isoformat() if today else None,
    }
    _save(root, slug, data)
    return data


def save_draft(root: Path, slug: str, html: str) -> dict:
    """Speichert HTML lokal und setzt Status draft_ready. Deployt NICHT."""
    data = load(root, slug)
    if data is None:
        raise ValueError(f"Kein Prototyp-Auftrag für '{slug}'")
    data["status"] = "draft_ready"
    data["html_local"] = html
    _save(root, slug, data)
    return data


def approve_local(root: Path, slug: str) -> dict:
    """Setzt Status approved_local. Nur erlaubt wenn Status == draft_ready."""
    data = load(root, slug)
    if data is None:
        raise ValueError(f"Kein Prototyp-Auftrag für '{slug}'")
    if data["status"] != "draft_ready":
        raise ValueError(
            f"approve_local erfordert Status 'draft_ready', ist aber '{data['status']}'"
        )
    data["status"] = "approved_local"
    _save(root, slug, data)
    return data


def mark_published(root: Path, slug: str, url: str) -> dict:
    """Setzt Status published + URL. Nur erlaubt wenn Status == approved_local."""
    data = load(root, slug)
    if data is None:
        raise ValueError(f"Kein Prototyp-Auftrag für '{slug}'")
    if data["status"] != "approved_local":
        raise ValueError(
            f"mark_published erfordert Status 'approved_local', ist aber '{data['status']}'"
        )
    data["status"] = "published"
    data["url"] = url
    _save(root, slug, data)
    return data


def mark_rework(root: Path, slug: str) -> dict:
    """Setzt Status rework (Entwurf muss überarbeitet werden)."""
    data = load(root, slug)
    if data is None:
        raise ValueError(f"Kein Prototyp-Auftrag für '{slug}'")
    data["status"] = "rework"
    _save(root, slug, data)
    return data


def mark_archived(root: Path, slug: str) -> dict:
    """Setzt Status archived."""
    data = load(root, slug)
    if data is None:
        raise ValueError(f"Kein Prototyp-Auftrag für '{slug}'")
    data["status"] = "archived"
    _save(root, slug, data)
    return data


# Legacy-Alias: bleibt für Rückwärtskompatibilität, setzt published direkt
# (nur noch als interner Schritt nach approved_local über mark_published nutzbar)
def mark_ready(root: Path, slug: str, url: str) -> dict:
    """Veraltet: direkt published setzen. Nur noch über approve_local + mark_published."""
    data = load(root, slug)
    if data is None:
        raise ValueError(f"Kein Prototyp-Auftrag für '{slug}'")
    data["status"] = "published"
    data["url"] = url
    _save(root, slug, data)
    return data


def list_pending(root: Path) -> list[dict]:
    """Gibt alle Einträge mit Status 'pending' zurück (nach Migration)."""
    d = _dir(root)
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        # Migration nur für den Status-Vergleich (nicht schreiben)
        migrated = _migrate(data)
        if migrated.get("status") == "pending":
            out.append(migrated)
    return out
