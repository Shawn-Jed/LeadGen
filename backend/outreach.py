"""Outreach-Zustand pro Lead als JSON: pending -> ready -> sent.

Datei: <root>/outreach/<slug>.json
  { "slug", "status", "request": {...}, "draft": {"betreff","text"} | None }
"""
from __future__ import annotations

import json
from pathlib import Path


def _dir(root: Path) -> Path:
    return root / "outreach"


def path(root: Path, slug: str) -> Path:
    return _dir(root) / f"{slug}.json"


def load(root: Path, slug: str) -> dict | None:
    p = path(root, slug)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _save(root: Path, slug: str, data: dict) -> None:
    p = path(root, slug)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_request(root: Path, slug: str, request: dict) -> dict:
    data = {"slug": slug, "status": "pending", "request": request, "draft": None}
    _save(root, slug, data)
    return data


def set_draft(root: Path, slug: str, betreff: str, text: str) -> dict:
    data = load(root, slug)
    if data is None:
        raise ValueError(f"Kein Outreach-Auftrag für '{slug}'")
    data["draft"] = {"betreff": betreff, "text": text}
    data["status"] = "ready"
    _save(root, slug, data)
    return data


def mark_sent(root: Path, slug: str) -> dict:
    data = load(root, slug)
    if data is None:
        raise ValueError(f"Kein Outreach-Auftrag für '{slug}'")
    data["status"] = "sent"
    _save(root, slug, data)
    return data


def list_pending(root: Path) -> list[dict]:
    d = _dir(root)
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("status") == "pending":
            out.append(data)
    return out
