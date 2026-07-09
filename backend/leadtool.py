"""Lead-Tracking-Kern: parse/render, Status, Graduierung, Report. Reine Logik, today wird injiziert."""
from __future__ import annotations

import re
import unicodedata
import urllib.parse
from datetime import date
from pathlib import Path

import yaml

# Spalten der Sammeltabelle (interne Keys, Reihenfolge = Spaltenreihenfolge)
PIPELINE_COLUMNS = ["slug", "firma", "adresse", "status", "schwaeche", "kontaktiert_am", "wiedervorlage", "notiz"]
# Anzeige-Header (Spaltenüberschriften in pipeline.md)
PIPELINE_HEADERS = ["slug", "Firma", "Adresse", "Status", "Schwäche", "kontaktiert_am", "Wiedervorlage", "Notiz"]
# Index der Adresse-Spalte — für abwärtskompatibles Parsen alter (adresse-loser) Tabellen.
_ADRESSE_IDX = PIPELINE_COLUMNS.index("adresse")

COLD_STATUSES = {"identifiziert", "analysiert", "prototyp_erstellt", "kontaktiert", "keine_antwort", "verloren", "zurückgestellt", "inaktiv"}
WARM_STATUSES = {"in_klaerung", "termin_vereinbart", "angebot_raus", "gewonnen"}
ALL_STATUSES = COLD_STATUSES | WARM_STATUSES

NO_ANSWER_DAYS = 14
EMPTY_CELL = "—"

PIPELINE_TITLE = "# Lead-Pipeline (kalt/früh)\n\nEine Zeile pro Lead. Warme Leads (ab `in_klaerung`) wandern nach `leads/<slug>.md`.\n\n"
BODY_SKELETON = "## Historie\n\n## Absprachen\n\n## Notizen\n"
LEAD_TEMPLATE = "---\n# Frontmatter wird von lead.py beim Graduieren gefüllt\n---\n" + BODY_SKELETON


def init_repo(root: Path) -> None:
    """Erzeugt pipeline.md, templates/lead.md, leads/, prototypes/ falls fehlend."""
    (root / "leads").mkdir(exist_ok=True)
    (root / "prototypes").mkdir(exist_ok=True)
    (root / "templates").mkdir(exist_ok=True)
    tmpl = root / "templates" / "lead.md"
    if not tmpl.exists():
        tmpl.write_text(LEAD_TEMPLATE, encoding="utf-8")
    pipeline = root / "pipeline.md"
    if not pipeline.exists():
        pipeline.write_text(PIPELINE_TITLE + render_pipeline_table([]), encoding="utf-8")


def _cell(value: str) -> str:
    value = (value or "").replace("|", "/").strip()
    return value if value else EMPTY_CELL


def render_pipeline_table(rows: list[dict]) -> str:
    lines = ["| " + " | ".join(PIPELINE_HEADERS) + " |",
             "|" + "|".join(["---"] * len(PIPELINE_HEADERS)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_cell(row.get(k, "")) for k in PIPELINE_COLUMNS) + " |")
    return "\n".join(lines) + "\n"


def parse_pipeline_table(text: str) -> list[dict]:
    table_lines = [ln for ln in text.splitlines() if ln.lstrip().startswith("|")]
    rows: list[dict] = []
    for ln in table_lines[2:]:  # [0]=Header, [1]=Separator
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        # Alt-Schema ohne Adresse-Spalte → leere Adresse einschieben (self-healing beim nächsten write).
        if len(cells) == len(PIPELINE_COLUMNS) - 1:
            cells.insert(_ADRESSE_IDX, "")
        if len(cells) != len(PIPELINE_COLUMNS):
            continue
        values = ["" if c == EMPTY_CELL else c for c in cells]
        rows.append(dict(zip(PIPELINE_COLUMNS, values)))
    return rows


def google_maps_link(firma: str, adresse: str = "", *, ort: str = "Hamburg") -> str:
    """Deterministischer Google-Maps-Suchlink aus Firma (+ Adresse). Kein API-Key nötig.

    Ergänzt 'Hamburg', falls weder Firma noch Adresse den Ort schon nennen — so landet
    die Suche zuverlässig beim richtigen Eintrag. Leere Firma → leerer Link.
    """
    teile = [t.strip() for t in (firma, adresse) if t and t.strip()]
    if not teile:
        return ""
    if ort and not any(ort.lower() in t.lower() for t in teile):
        teile.append(ort)
    query = urllib.parse.quote_plus(" ".join(teile))
    return f"https://www.google.com/maps/search/?api=1&query={query}"


# Nach .lower() reichen Kleinbuchstaben-Keys.
_UMLAUTS = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}


def slugify(name: str) -> str:
    s = name.strip().lower()
    for k, v in _UMLAUTS.items():
        s = s.replace(k, v)
    # restliche Akzente (é, à, ç, ...) generisch zu ASCII entfernen
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def read_pipeline(root: Path) -> list[dict]:
    return parse_pipeline_table((root / "pipeline.md").read_text(encoding="utf-8"))


def write_pipeline(root: Path, rows: list[dict]) -> None:
    (root / "pipeline.md").write_text(PIPELINE_TITLE + render_pipeline_table(rows), encoding="utf-8")


def add_lead(root: Path, firma: str, *, schwaeche: str = "", status: str = "identifiziert",
             adresse: str = "", today: date) -> str:
    slug = slugify(firma)
    rows = read_pipeline(root)
    if any(r["slug"] == slug for r in rows) or lead_path(root, slug).exists():
        raise ValueError(f"Lead '{slug}' existiert bereits")
    rows.append({"slug": slug, "firma": firma, "adresse": adresse, "status": status,
                 "schwaeche": schwaeche, "kontaktiert_am": "", "wiedervorlage": "", "notiz": ""})
    write_pipeline(root, rows)
    return slug


def lead_path(root: Path, slug: str) -> Path:
    return root / "leads" / f"{slug}.md"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body


def dump_frontmatter(meta: dict, body: str) -> str:
    fm = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, default_flow_style=False)
    return f"---\n{fm}---\n{body}"


def _split_schwaeche(raw: str) -> list[str]:
    parts = re.split(r"[;,]", raw or "")
    return [p.strip() for p in parts if p.strip()]


def _template_body(root: Path) -> str:
    tmpl = root / "templates" / "lead.md"
    if tmpl.exists():
        _, body = parse_frontmatter(tmpl.read_text(encoding="utf-8"))
        if body.strip():
            return body
    return BODY_SKELETON


def graduate(root: Path, slug: str, *, status: str, today: date) -> Path:
    rows = read_pipeline(root)
    row = next((r for r in rows if r["slug"] == slug), None)
    if row is None:
        raise ValueError(f"Lead '{slug}' nicht in pipeline.md")
    meta = {
        "firma": row["firma"], "slug": slug, "status": status,
        "prioritaet": "mittel", "ort": "", "branche": "", "website": "",
        "adresse": row.get("adresse", ""),
        "google_eintrag": google_maps_link(row["firma"], row.get("adresse", "")),
        "schwaeche": _split_schwaeche(row["schwaeche"]),
        "ucp": "", "roi_these": "", "prototyp": "",
        "kontakt": {"name": "", "rolle": "", "email": "", "quelle": ""},
        "kontaktiert_am": row["kontaktiert_am"], "wiedervorlage": row["wiedervorlage"],
        "angelegt": today.isoformat(),
    }
    path = lead_path(root, slug)
    path.write_text(dump_frontmatter(meta, _template_body(root)), encoding="utf-8")
    write_pipeline(root, [r for r in rows if r["slug"] != slug])
    return path


def read_lead(root: Path, slug: str) -> tuple[dict, str]:
    return parse_frontmatter(lead_path(root, slug).read_text(encoding="utf-8"))


def write_lead(root: Path, slug: str, meta: dict, body: str) -> None:
    lead_path(root, slug).write_text(dump_frontmatter(meta, body), encoding="utf-8")


def set_status(root: Path, slug: str, status: str, *, today: date) -> None:
    if status not in ALL_STATUSES:
        raise ValueError(f"Unbekannter Status '{status}'. Erlaubt: {sorted(ALL_STATUSES)}")

    if lead_path(root, slug).exists():          # bereits warm → Frontmatter aktualisieren
        meta, body = read_lead(root, slug)
        meta["status"] = status
        write_lead(root, slug, meta, body)
        return

    rows = read_pipeline(root)
    row = next((r for r in rows if r["slug"] == slug), None)
    if row is None:
        raise ValueError(f"Lead '{slug}' nicht gefunden")

    if status in WARM_STATUSES:                 # kalt → warm: graduieren
        graduate(root, slug, status=status, today=today)
        return

    row["status"] = status                      # kalt → kalt
    if status == "kontaktiert" and not row["kontaktiert_am"]:
        row["kontaktiert_am"] = today.isoformat()
    write_pipeline(root, rows)


def _all_leads(root: Path) -> list[dict]:
    """Vereinheitlichte Sicht: kalte Zeilen + warme Frontmatter, je als dict mit slug/firma/status/kontaktiert_am/wiedervorlage."""
    out: list[dict] = []
    for r in read_pipeline(root):
        out.append({"slug": r["slug"], "firma": r["firma"], "status": r["status"],
                    "kontaktiert_am": r["kontaktiert_am"], "wiedervorlage": r["wiedervorlage"]})
    for f in sorted((root / "leads").glob("*.md")):
        meta, _ = parse_frontmatter(f.read_text(encoding="utf-8"))
        out.append({"slug": meta.get("slug", f.stem), "firma": meta.get("firma", ""),
                    "status": meta.get("status", ""), "kontaktiert_am": meta.get("kontaktiert_am") or "",
                    "wiedervorlage": meta.get("wiedervorlage") or ""})
    return out


def report(root: Path, *, today: date) -> dict:
    keine_antwort, wiedervorlage_faellig = [], []
    for lead in _all_leads(root):
        if lead["status"] == "kontaktiert" and lead["kontaktiert_am"]:
            tage = (today - date.fromisoformat(lead["kontaktiert_am"])).days
            if tage > NO_ANSWER_DAYS:
                keine_antwort.append({**lead, "tage": tage})
        if lead["wiedervorlage"] and date.fromisoformat(lead["wiedervorlage"]) <= today:
            wiedervorlage_faellig.append(lead)
    return {"keine_antwort": keine_antwort, "wiedervorlage_faellig": wiedervorlage_faellig}


def set_wiedervorlage(root: Path, slug: str, datum: str) -> None:
    """Setzt das Wiedervorlage-Datum (ISO YYYY-MM-DD) — bei warmem Lead im Frontmatter, sonst in der Pipeline-Zeile."""
    date.fromisoformat(datum)  # validiert Format, wirft ValueError bei Murks
    if lead_path(root, slug).exists():
        meta, body = read_lead(root, slug)
        meta["wiedervorlage"] = datum
        write_lead(root, slug, meta, body)
        return
    rows = read_pipeline(root)
    row = next((r for r in rows if r["slug"] == slug), None)
    if row is None:
        raise ValueError(f"Lead '{slug}' nicht gefunden")
    row["wiedervorlage"] = datum
    write_pipeline(root, rows)


def add_note(root: Path, slug: str, text: str, *, today: date) -> None:
    stamp = today.isoformat()
    if lead_path(root, slug).exists():
        meta, body = read_lead(root, slug)
        line = f"- {stamp}: {text}\n"
        if "## Notizen" in body:
            head, _, tail = body.partition("## Notizen\n")
            body = head + "## Notizen\n" + line + tail
        else:
            body = body.rstrip("\n") + f"\n\n## Notizen\n{line}"
        write_lead(root, slug, meta, body)
        return
    rows = read_pipeline(root)
    row = next((r for r in rows if r["slug"] == slug), None)
    if row is None:
        raise ValueError(f"Lead '{slug}' nicht gefunden")
    existing = row["notiz"]
    # Zeitstempel je Notiz, damit die Zelle als kleiner Verlauf lesbar bleibt
    entry = f"{stamp}: {text}"
    row["notiz"] = f"{existing} · {entry}" if existing else entry
    write_pipeline(root, rows)


def set_email(root: Path, slug: str, email: str) -> None:
    """Setzt kontakt.email — nur bei warmen Leads (eigene Datei). Sonst ValueError."""
    if not lead_path(root, slug).exists():
        raise ValueError(f"E-Mail nur bei warmen Leads setzbar; '{slug}' ist nicht warm")
    meta, body = read_lead(root, slug)
    kontakt = meta.get("kontakt") or {}
    kontakt["email"] = email
    meta["kontakt"] = kontakt
    write_lead(root, slug, meta, body)


def mark_contacted(root: Path, slug: str, *, betreff: str, today: date) -> None:
    """Nach Mailversand: kontaktiert_am stempeln (falls leer) + Historie-Zeile anhängen.

    Ändert den Pipeline-Status NICHT (kein Downgrade eines warmen Leads auf 'kontaktiert').
    """
    if not lead_path(root, slug).exists():
        raise ValueError(f"'{slug}' ist nicht warm — Anschreiben nur für warme Leads")
    meta, body = read_lead(root, slug)
    if not meta.get("kontaktiert_am"):
        meta["kontaktiert_am"] = today.isoformat()
    line = f"- {today.isoformat()}: Mail gesendet — {betreff}\n"
    if "## Historie" in body:
        head, _, tail = body.partition("## Historie\n")
        body = head + "## Historie\n" + line + tail
    else:
        body = f"## Historie\n{line}\n" + body
    write_lead(root, slug, meta, body)
