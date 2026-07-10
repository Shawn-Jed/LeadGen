"""Lead-Discovery-Kern (Tier 1): Overpass-Abfrage, Parsing, Score, Run-Dateien, Lead-Anlage.
Deterministisch; Overpass-HTTP ist injizierbar. today wird injiziert."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import leadtool

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Deutsches Branchenwort (normalisiert) → OSM-Tags. Erweiterbar.
BRANCHE_TAGS: dict[str, list[str]] = {
    "zahnarzt": ["amenity=dentist"], "zahnaerzte": ["amenity=dentist"],
    "arzt": ["amenity=doctors"], "aerzte": ["amenity=doctors"], "hausarzt": ["amenity=doctors"],
    "friseur": ["shop=hairdresser"], "friseure": ["shop=hairdresser"],
    "baeckerei": ["shop=bakery"], "baecker": ["shop=bakery"],
    "restaurant": ["amenity=restaurant"], "gastronomie": ["amenity=restaurant"],
    "sanitaer": ["craft=plumber"], "klempner": ["craft=plumber"],
    "elektriker": ["craft=electrician"],
    "anwalt": ["office=lawyer"], "rechtsanwalt": ["office=lawyer"], "kanzlei": ["office=lawyer"],
    "tischler": ["craft=carpenter"], "schreiner": ["craft=carpenter"],
    "autowerkstatt": ["shop=car_repair"], "kfz": ["shop=car_repair"],
}


def _norm(s: str) -> str:
    s = s.strip().lower()
    for k, v in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        s = s.replace(k, v)
    return s


def branche_to_tags(branche: str) -> list[str]:
    key = _norm(branche)
    if key not in BRANCHE_TAGS:
        raise ValueError(
            f"Unbekannte Branche '{branche}'. Bekannt: {sorted(BRANCHE_TAGS)}"
        )
    return BRANCHE_TAGS[key]


def build_overpass_query(tags: list[str], stadtteil: str | None = None) -> str:
    if stadtteil:
        area = f'area["name"="{stadtteil}"]["boundary"="administrative"]->.searchArea;'
    else:
        area = 'area["name"="Hamburg"]["admin_level"="4"]->.searchArea;'
    parts = []
    for tag in tags:
        k, _, v = tag.partition("=")
        for typ in ("node", "way", "relation"):
            parts.append(f'  {typ}["{k}"="{v}"](area.searchArea);')
    body = "\n".join(parts)
    return f"[out:json][timeout:60];\n{area}\n(\n{body}\n);\nout center tags;"


def _adresse(tags: dict) -> str:
    line1 = " ".join(p for p in [tags.get("addr:street", ""), tags.get("addr:housenumber", "")] if p)
    line2 = " ".join(p for p in [tags.get("addr:postcode", ""), tags.get("addr:city", "")] if p)
    return ", ".join(p for p in [line1, line2] if p)


def parse_elements(data: dict) -> list[dict]:
    out = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        firma = tags.get("name")
        if not firma:
            continue
        out.append({
            "firma": firma,
            "adresse": _adresse(tags),
            "website": tags.get("website") or tags.get("contact:website") or "",
            "telefon": tags.get("phone") or tags.get("contact:phone") or "",
            "osm_id": f"{el.get('type', '')}/{el.get('id', '')}",
        })
    return out


REJECTED_STATUS = "abgelehnt"
STATUSES = {"neu", "website_unklar", "keine_website", "hat_website", "analysiert", REJECTED_STATUS}


def score_tier1(cand: dict) -> int:
    return 60 if not cand.get("website") else 0


def new_run(branche: str, stadtteil: str | None, candidates: list[dict], today: date) -> dict:
    kand = []
    for i, c in enumerate(candidates, start=1):
        hat_web = bool(c.get("website"))
        kand.append({
            "id": i,
            "firma": c["firma"],
            "adresse": c.get("adresse", ""),
            "google_url": leadtool.google_maps_link(c["firma"], c.get("adresse", "")),
            "website": c.get("website", ""),
            "telefon": c.get("telefon", ""),
            "osm_id": c.get("osm_id", ""),
            "status": "hat_website" if hat_web else "website_unklar",
            "gefundene_url": "",
            "score": score_tier1(c),
            "befund": "Website in OSM hinterlegt" if hat_web else "kein website-Tag in OSM",
            "lead_angelegt": False,
        })
    return {"branche": branche, "stadtteil": stadtteil or "Hamburg",
            "erstellt": today.isoformat(), "kandidaten": kand}


def run_path(root: Path, branche: str, stadtteil: str | None, today: date) -> Path:
    slug = _norm(branche).replace(" ", "-")
    area = _norm(stadtteil or "hamburg").replace(" ", "-")
    return root / "discovery" / f"{today.isoformat()}-{slug}-{area}.json"


def save_run(path: Path, run: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")


def load_run(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def set_status(run: dict, cand_id: int, status: str, url: str = "") -> None:
    if status not in STATUSES:
        raise ValueError(f"Unbekannter Status '{status}'. Erlaubt: {sorted(STATUSES)}")
    for c in run["kandidaten"]:
        if c["id"] == cand_id:
            c["status"] = status
            if url:
                c["gefundene_url"] = url
            return
    raise ValueError(f"Kandidat id={cand_id} nicht gefunden")


def _find_cand(run: dict, cand_id: int) -> dict:
    for c in run["kandidaten"]:
        if c["id"] == cand_id:
            return c
    raise ValueError(f"Kandidat id={cand_id} nicht gefunden")


def reject(run: dict, cand_id: int) -> None:
    """Kandidat ablehnen: Status → 'abgelehnt', vorherigen Status für Restore merken.

    So fällt er aus 'keine_website' heraus und wird von `create_leads(..., "auto")`
    nicht mehr angefasst. Doppeltes Ablehnen überschreibt den gemerkten Status nicht.
    """
    c = _find_cand(run, cand_id)
    if c["status"] != REJECTED_STATUS:
        c["status_vor_ablehnung"] = c["status"]
    c["status"] = REJECTED_STATUS


def restore(run: dict, cand_id: int) -> None:
    """Ablehnung zurücknehmen: Status auf den gemerkten Wert (sonst 'neu')."""
    c = _find_cand(run, cand_id)
    c["status"] = c.pop("status_vor_ablehnung", "neu")


def schwaeche_fuer_lead(cand: dict) -> str:
    """Leitet die Lead-Schwäche aus dem Discovery-Befund des Kandidaten ab.

    So wandert die eigentliche Discovery-Erkenntnis (Tier-2-Mängelliste bzw.
    kein Web-Auftritt) in den Lead, statt sie durch einen generischen Text zu ersetzen.
    """
    befund = (cand.get("befund") or "").strip()
    # Tier-2-Mängelliste → Mängel selbst als Schwäche übernehmen
    prefix = "Tier-2-Mängel:"
    if befund.startswith(prefix):
        maengel = befund[len(prefix):].strip()
        return f"Website-Mängel: {maengel}" if maengel else "Website mit Mängeln"
    if cand.get("status") == "keine_website":
        return "keine auffindbare Website"
    # sonst: aussagekräftigen Befund nehmen, generische OSM-Hinweise verwerfen
    if befund and befund not in ("kein website-Tag in OSM", "Website in OSM hinterlegt"):
        return befund
    return "keine auffindbare Website"


def create_leads(root: Path, run: dict, which, today: date, *, website: str = "", notiz: str = "", schwaeche: str = "") -> dict:
    if which == "auto":
        targets = [c for c in run["kandidaten"]
                   if c["status"] == "keine_website" and not c["lead_angelegt"]]
    else:
        ids = set(which)
        targets = [c for c in run["kandidaten"] if c["id"] in ids and not c["lead_angelegt"]]
    # website/notiz/schwaeche stammen aus dem Einzel-Übernahme-Dialog — nur bei genau einem Kandidaten
    # anwenden, damit ein Bulk-Import sie nicht auf alle Leads schmiert.
    single = len(targets) == 1
    angelegt, uebersprungen = [], []
    for c in targets:
        try:
            # Vom Nutzer gewählte Schwäche-Tags haben Vorrang; sonst automatisch aus dem Discovery-Befund.
            eff_schwaeche = schwaeche.strip() if (single and schwaeche.strip()) else schwaeche_fuer_lead(c)
            slug = leadtool.add_lead(root, c["firma"], schwaeche=eff_schwaeche,
                                     adresse=c.get("adresse", ""),
                                     website=(website if single else ""), today=today)
            c["lead_angelegt"] = True
            if single and notiz.strip():
                leadtool.add_note(root, slug, notiz.strip(), today=today)
            angelegt.append(slug)
        except ValueError:
            uebersprungen.append(c["firma"])
    return {"angelegt": angelegt, "uebersprungen": uebersprungen}


def http_overpass(query: str) -> dict:
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_URL, data=data,
        headers={"User-Agent": "SelfworkLeads/0.1 (Hamburg lead discovery; shje@delta-sport.com)"},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_overpass(query: str, *, fetch_fn=None) -> dict:
    if fetch_fn is None:
        fetch_fn = http_overpass
    return fetch_fn(query)


import re as _re

from bs4 import BeautifulSoup as _BS


def analyse_site(html: str, url: str, *, jahr: int) -> dict:
    """Reine Funktion: HTML-String + URL → Tier-2-Signale.

    Parameters
    ----------
    html : str
        Rohes HTML der Seite.
    url : str
        Effektive URL der Seite (für https-Erkennung).
    jahr : int
        Heutiges Jahr (injiziert für testbarkeit, z.B. 2026).
    """
    soup = _BS(html, "html.parser")

    # --- https ---
    has_https = url.lower().startswith("https://")

    # --- viewport ---
    vp_tag = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "viewport"})
    has_viewport = vp_tag is not None

    # --- copyright_jahr ---
    text = soup.get_text(" ", strip=True)
    jahre = [int(m) for m in _re.findall(r"\b(19\d{2}|20\d{2})\b", text)]
    copyright_jahr = max(jahre) if jahre else None

    # --- veraltet ---
    veraltet = (copyright_jahr is not None) and (copyright_jahr < jahr - 2)

    # --- impressum ---
    imp_link = soup.find(lambda tag: tag.name in ("a", "span", "p", "li", "div")
                         and "impressum" in (tag.get_text() or "").lower())
    has_impressum = imp_link is not None

    # --- kontaktformular ---
    has_form = soup.find("form") is not None
    kontakt_link = soup.find(lambda tag: tag.name == "a"
                              and "kontakt" in (tag.get_text() or "").lower())
    has_kontakt = has_form or (kontakt_link is not None)

    return {
        "https": has_https,
        "viewport": has_viewport,
        "copyright_jahr": copyright_jahr,
        "veraltet": veraltet,
        "impressum": has_impressum,
        "kontaktformular": has_kontakt,
    }


def score_tier2(signals: dict) -> int:
    """Additive Aufschläge auf Basis der Tier-2-Signale.

    Aufschläge:
    - kein HTTPS       → +15
    - kein Viewport    → +20
    - veraltet         → +15
    - kein Impressum   → +10
    - kein Kontakt     → +10
    """
    score = 0
    if not signals.get("https"):
        score += 15
    if not signals.get("viewport"):
        score += 20
    if signals.get("veraltet"):
        score += 15
    if not signals.get("impressum"):
        score += 10
    if not signals.get("kontaktformular"):
        score += 10
    return score


def http_get(url: str) -> str:
    """Realer HTTP-GET einer Website-URL; gibt HTML-String zurück.

    Timeout 20 s. User-Agent konsistent mit http_overpass.
    Raises OSError / urllib.error.URLError bei Netz- oder HTTP-Fehlern.
    NICHT direkt unit-getestet — analyse_run erhält fetch_html_fn-Injektion.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SelfworkLeads/0.1 (Hamburg lead discovery; shje@delta-sport.com)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _effective_url(cand: dict) -> str:
    """Gibt die effektive URL eines Kandidaten zurück: website-Tag oder gefundene_url."""
    return cand.get("website") or cand.get("gefundene_url") or ""


def analyse_run(
    root,  # Path — unused in A2 but mirrors API of create_leads for symmetry
    run: dict,
    *,
    fetch_html_fn=None,
    jahr: int,
) -> dict:
    """Analysiert alle hat_website-Kandidaten eines Runs mit Tier-2-Heuristiken.

    Für jeden Kandidaten mit Status ``hat_website`` und nicht-leerer URL:
    - HTML holen (via fetch_html_fn oder http_get)
    - analyse_site ausführen
    - candidate["tier2"] = signals setzen
    - candidate["score"] += score_tier2(signals)
    - candidate["befund"] aktualisieren
    - candidate["status"] = "analysiert"

    Bei Fetch-Fehler: befund = "Seite nicht erreichbar: <exc>"; Status unverändert.

    A2-Kontrakt: nur tier2, score, befund, status werden mutiert.
    tier3, lead_angelegt, gefundene_url, osm_id etc. bleiben unberührt.

    Parameters
    ----------
    root : Path
        Repo-Root (Konventions-Parameter; in A2 ungenutzt).
    run : dict
        Run-dict (mutiert in-place).
    fetch_html_fn : callable | None
        Injizierbarer HTTP-Getter (url -> str). Fällt auf http_get zurück.
        In Tests immer angeben — kein echter Netz-Call.
    jahr : int
        Heutiges Jahr (für veraltet-Erkennung injiziert).

    Returns
    -------
    dict mit Keys:
        ``analysiert`` (int): Anzahl erfolgreich analysierter Kandidaten.
        ``fehler`` (list[str]): Fehlermeldungen je fehlgeschlagenem Fetch.
    """
    fetch_fn = fetch_html_fn if fetch_html_fn is not None else http_get
    analysiert_count = 0
    fehler_list: list[str] = []

    for cand in run["kandidaten"]:
        if cand.get("status") != "hat_website":
            continue
        url = _effective_url(cand)
        if not url:
            continue
        try:
            html = fetch_fn(url)
        except Exception as exc:
            cand["befund"] = f"Seite nicht erreichbar: {exc}"
            fehler_list.append(f"{url}: {exc}")
            continue

        signals = analyse_site(html, url, jahr=jahr)
        t2_score = score_tier2(signals)

        cand["tier2"] = signals
        cand["score"] = cand.get("score", 0) + t2_score
        # Befund: kompakte Mängelliste
        maengel = []
        if not signals["https"]:
            maengel.append("kein HTTPS")
        if not signals["viewport"]:
            maengel.append("nicht mobil")
        if signals["veraltet"]:
            maengel.append(f"veraltet ({signals['copyright_jahr']})")
        if not signals["impressum"]:
            maengel.append("kein Impressum")
        if not signals["kontaktformular"]:
            maengel.append("kein Kontaktformular")
        cand["befund"] = ("Tier-2-Mängel: " + ", ".join(maengel)) if maengel else "Tier-2: keine groben Mängel"
        cand["status"] = "analysiert"
        analysiert_count += 1

    return {"analysiert": analysiert_count, "fehler": fehler_list}


# ---------------------------------------------------------------------------
# A3 — Tier-3-Qualitätsurteil (qualitativ, kein Score-Einfluss)
# ---------------------------------------------------------------------------

_EMPFEHLUNGEN = {"lohnt", "lohnt_nicht", "unklar"}


def set_tier3(run: dict, cand_id: int, *, urteil: str, empfehlung: str) -> None:
    """Speichert das Tier-3-Urteil am Kandidaten.

    Daten-Shape-Kontrakt: setzt NUR candidate["tier3"]. Berührt score, tier2,
    lead_angelegt, status oder andere Keys NICHT.

    Args:
        run:         Run-Dict (mutiert in-place).
        cand_id:     id des Kandidaten (int).
        urteil:      Freitext-Begründung (z.B. "Veraltetes Design, kein Responsive").
        empfehlung:  Einer von: "lohnt" | "lohnt_nicht" | "unklar".

    Raises:
        ValueError: empfehlung nicht im erlaubten Set oder cand_id unbekannt.
    """
    if empfehlung not in _EMPFEHLUNGEN:
        raise ValueError(
            f"Ungültige empfehlung '{empfehlung}'. Erlaubt: {sorted(_EMPFEHLUNGEN)}"
        )
    for c in run["kandidaten"]:
        if c["id"] == cand_id:
            c["tier3"] = {"urteil": urteil, "empfehlung": empfehlung}
            return
    raise ValueError(f"Kandidat id={cand_id} nicht gefunden")


def shortlist(run: dict, *, top: int = 10) -> list[dict]:
    """Gibt die top-N analysierten Kandidaten sortiert nach Score (desc) zurück.

    Nur Kandidaten mit status == "analysiert" werden berücksichtigt.
    Wird vom Skill verwendet, um zu wissen, welche Sites per Playwright beurteilt
    werden sollen.

    Args:
        run: Run-Dict.
        top: Maximale Anzahl Kandidaten (default 10).

    Returns:
        Liste von Kandidaten-Dicts (Referenzen auf das Original, nicht kopiert).
    """
    analysiert = [c for c in run["kandidaten"] if c["status"] == "analysiert"]
    analysiert.sort(key=lambda c: c["score"], reverse=True)
    return analysiert[:top]
