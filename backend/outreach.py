"""Outreach-Zustand pro Lead als JSON: pending -> ready -> sent.

Datei: <root>/outreach/<slug>.json
  { "slug", "status", "request": {...}, "draft": {"betreff","text"} | None }

Kanonische Status: none | pending | ready | sent
Demo-Link-Regel: nur bei prototyp_state.status == 'published'.
"""
from __future__ import annotations

import json
from pathlib import Path

# Demo-Zustände, bei denen ein Link erlaubt ist
_DEMO_LINK_ALLOWED = {"published"}


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
    # Demo-Link nur bei published erlaubt — bei allen anderen Zuständen entfernen
    req = dict(request)
    proto_status = req.get("prototyp_status", "")
    if proto_status not in _DEMO_LINK_ALLOWED:
        req.pop("demo_link", None)
    data = {"slug": slug, "status": "pending", "request": req, "draft": None}
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


# ---------------------------------------------------------------------------
# W4.1 — Kontakt-Readiness-Checkliste
# ---------------------------------------------------------------------------

def outreach_readiness(lead: dict) -> dict:
    """Prüft, ob ein Lead bereit zum Anschreiben ist.

    Pflichtpunkte: warm (oder kalt_freigegeben), email, anlass,
                   angebot, nutzen, cta.
    Optional:      demo_link — nur wenn prototyp_state.status == 'published'.

    Rückgabe: {"ok": bool, "fehlend": [...], "demo_link": str | None}
    """
    fehlend: list[str] = []

    # Warm oder bewusst kalt freigegeben?
    warm = lead.get("warm", False)
    kalt_freigegeben = lead.get("kalt_freigegeben", False)
    if not warm and not kalt_freigegeben:
        fehlend.append("Lead ist kalt — erst qualifizieren oder kalt_freigegeben setzen")

    # E-Mail-Adresse
    email = (lead.get("kontakt") or {}).get("email") or ""
    if not str(email).strip():
        fehlend.append("E-Mail-Adresse fehlt")

    # Sachlicher Anlass
    if not str(lead.get("anlass") or "").strip():
        fehlend.append("Anlass fehlt (z.B. 'Website veraltet seit 2018')")

    # Angebot
    if not str(lead.get("angebot") or "").strip():
        fehlend.append("Angebot fehlt (z.B. 'Website-Relaunch zum Festpreis')")

    # Nutzen
    if not str(lead.get("nutzen") or "").strip():
        fehlend.append("Nutzen fehlt (z.B. 'mehr Anfragen über Mobilgeräte')")

    # CTA
    if not str(lead.get("cta") or "").strip():
        fehlend.append("CTA fehlt (z.B. '15-Minuten-Telefonat')")

    # Demo-Link: nur bei published
    ps = lead.get("prototyp_state") or {}
    demo_link: str | None = None
    if ps.get("status") in _DEMO_LINK_ALLOWED and ps.get("url"):
        demo_link = ps["url"]

    return {"ok": len(fehlend) == 0, "fehlend": fehlend, "demo_link": demo_link}


# ---------------------------------------------------------------------------
# W4.3 — validate_send: Vorprüfung vor dem Versand
# ---------------------------------------------------------------------------

def validate_send(root: Path, slug: str) -> dict:
    """Wirft ValueError bei ungültigem Sendezustand.

    Prüft:
    - Outreach-Datensatz vorhanden
    - Entwurf (draft) vollständig vorhanden
    - Noch nicht gesendet (kein Doppelversand)
    - E-Mail-Adresse im Lead-Frontmatter (via leadtool)

    Gibt das State-Dict zurück, wenn alle Checks bestehen.
    """
    import leadtool  # lokaler Import vermeidet zirkuläre Abhängigkeit

    state = load(root, slug)
    if state is None:
        raise ValueError(f"Kein Outreach-Auftrag für '{slug}'")

    if not state.get("draft"):
        raise ValueError(
            f"Kein fertiger Entwurf (draft) vorhanden für '{slug}' — "
            "Status: {state.get('status', 'unbekannt')}"
        )

    if state.get("status") == "sent":
        raise ValueError(f"Mail für '{slug}' wurde bereits gesendet (Doppelversand verhindert)")

    # E-Mail-Adresse aus Lead-Frontmatter
    try:
        meta, _ = leadtool.read_lead(root, slug)
    except FileNotFoundError:
        raise ValueError(f"Lead-Datei für '{slug}' nicht gefunden")

    to_addr = (meta.get("kontakt") or {}).get("email") or ""
    if not str(to_addr).strip():
        raise ValueError(f"Lead '{slug}' hat keine E-Mail-Adresse")

    return state
