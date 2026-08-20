"""LeadGen-Backend: stdlib-HTTP-Server, der eine JSON-API über die Logik in
leadtool.py + discotool.py bereitstellt.

Voll entkoppelt vom Frontend:
  - CORS ist aktiv (Default-Origin '*', per --cors-origin einschränkbar).
  - Standardmäßig liefert der Server zusätzlich das Schwester-Verzeichnis ../frontend
    aus (bequem für lokale Entwicklung). Mit --api-only wird nur die API bedient.

Start:
  python app.py                 → API + statisches Frontend auf http://127.0.0.1:8723
  python app.py --api-only      → nur JSON-API (Frontend separat, z.B. `npx serve ../frontend`)

Keine externen Dependencies außer den schon installierten yaml/bs4 (indirekt via Module).
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import discotool
import leadtool
import config
import mailer
import outreach
import prototyp
import deploy
import portfolio

ROOT = Path(__file__).parent
config.load_env(ROOT)  # .env → os.environ (SMTP + OUTREACH_SEND_MODE)
# Frontend liegt als Schwester-Verzeichnis neben backend/ (entkoppelte Struktur).
FRONTEND = ROOT.parent / "frontend"
DEFAULT_PORT = 8723

# Statusreihenfolge fürs Cockpit (kalt → warm → Endzustände)
STATUS_REIHENFOLGE = [
    "identifiziert", "analysiert", "prototyp_erstellt", "kontaktiert",
    "keine_antwort", "in_klaerung", "termin_vereinbart", "angebot_raus",
    "gewonnen", "verloren", "zurückgestellt", "inaktiv",
]

# MIME-Typen nach Endung fürs statische Ausliefern
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".map": "application/json; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


# ---------------------------------------------------------------------------
# Hilfsfunktionen: body-Parsing der warmen Lead-Markdown
# ---------------------------------------------------------------------------

def _section_lines(body: str, header: str) -> list[str]:
    """Extrahiert die '- '-Zeilen unter '## <header>' (ohne führendes '- ')."""
    out: list[str] = []
    in_section = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = (stripped[3:].strip() == header)
            continue
        if in_section and stripped.startswith("- "):
            out.append(stripped[2:])
    return out


def _warm_lead_dict(meta: dict, body: str) -> dict:
    """Baut das warme-Lead-dict gemäß API-Kontrakt aus Frontmatter + Body."""
    schwaeche = meta.get("schwaeche") or []
    if isinstance(schwaeche, list):
        schwaeche_str = ", ".join(str(s) for s in schwaeche)
    else:
        schwaeche_str = str(schwaeche)
    kontakt = meta.get("kontakt") or {}
    return {
        "slug": meta.get("slug", ""),
        "firma": meta.get("firma", ""),
        "status": meta.get("status", ""),
        "schwaeche": schwaeche_str,
        "kontaktiert_am": meta.get("kontaktiert_am") or "",
        "wiedervorlage": meta.get("wiedervorlage") or "",
        "notiz": "",
        "warm": True,
        "prioritaet": meta.get("prioritaet", ""),
        "ort": meta.get("ort", ""),
        "branche": meta.get("branche", ""),
        "website": meta.get("website", ""),
        "adresse": meta.get("adresse", ""),
        # Fallback: fehlt das Feld (Alt-Lead), Link live aus Firma (+ Adresse) ableiten.
        "google_eintrag": meta.get("google_eintrag")
        or leadtool.google_maps_link(meta.get("firma", ""), meta.get("adresse", "")),
        "ucp": meta.get("ucp", ""),
        "roi_these": meta.get("roi_these", ""),
        "prototyp": meta.get("prototyp", ""),
        "kontakt": {
            "name": kontakt.get("name", ""),
            "rolle": kontakt.get("rolle", ""),
            "email": kontakt.get("email", ""),
            "quelle": kontakt.get("quelle", ""),
        },
        "angelegt": meta.get("angelegt", ""),
        "historie": _section_lines(body, "Historie"),
        "notizen": _section_lines(body, "Notizen"),
    }


def build_state(today: date) -> dict:
    """Kombinierter Cockpit-Snapshot: Leads (kalt+warm), Report, Discovery-Runs."""
    # kalte Leads
    leads: list[dict] = []
    for r in leadtool.read_pipeline(ROOT):
        leads.append({
            "slug": r.get("slug", ""),
            "firma": r.get("firma", ""),
            "status": r.get("status", ""),
            "schwaeche": r.get("schwaeche", ""),
            "adresse": r.get("adresse", ""),
            "website": r.get("website", ""),
            "google_eintrag": leadtool.google_maps_link(r.get("firma", ""), r.get("adresse", "")),
            "kontaktiert_am": r.get("kontaktiert_am", ""),
            "wiedervorlage": r.get("wiedervorlage", ""),
            "notiz": r.get("notiz", ""),
            "warm": False,
        })
    # warme Leads aus leads/*.md
    leads_dir = ROOT / "leads"
    if leads_dir.exists():
        for f in sorted(leads_dir.glob("*.md")):
            meta, body = leadtool.read_lead(ROOT, f.stem)
            leads.append(_warm_lead_dict(meta, body))

    # Prototyp-Status je Lead aus dem Store anreichern (kalt + warm)
    for lead in leads:
        ps = prototyp.load(ROOT, lead["slug"])
        lead["prototyp_state"] = (
            {"status": ps["status"], "url": ps.get("url")} if ps
            else {"status": "none", "url": None}
        )
        # W2.1 + W2.2: Priorität und nächste Aktion berechnen und einbetten
        prio = leadtool.priority_score(lead, today)
        lead["priority"] = prio
        lead["next_action"] = leadtool.next_action(lead, today)

    rep = leadtool.report(ROOT, today=today)

    # Discovery-Runs auflisten (Übersicht, ohne volles Kandidaten-Array)
    discovery_runs: list[dict] = []
    disco_dir = ROOT / "discovery"
    if disco_dir.exists():
        for f in sorted(disco_dir.glob("*.json")):
            try:
                run = discotool.load_run(f)
            except Exception:
                continue  # kaputte Datei überspringen
            kandidaten = run.get("kandidaten", [])
            counts: dict[str, int] = {}
            for c in kandidaten:
                st = c.get("status", "")
                counts[st] = counts.get(st, 0) + 1
            discovery_runs.append({
                "file": f"discovery/{f.name}",
                "branche": run.get("branche", ""),
                "stadtteil": run.get("stadtteil", ""),
                "erstellt": run.get("erstellt", ""),
                "anzahl": len(kandidaten),
                "counts": counts,
            })

    return {
        "today": today.isoformat(),
        "statuses": {
            "cold": sorted(leadtool.COLD_STATUSES),
            "warm": sorted(leadtool.WARM_STATUSES),
            "all": sorted(leadtool.ALL_STATUSES),
            "candidate": sorted(discotool.STATUSES),
            "reihenfolge": STATUS_REIHENFOLGE,
        },
        "leads": leads,
        "report": rep,
        "discovery_runs": discovery_runs,
    }


_SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def _valid_slug(slug: str) -> str:
    if not _SLUG_RE.match(slug):
        raise ValueError(f"Ungültiger Slug '{slug}'")
    return slug


def _lead_summary(slug: str) -> dict:
    """Best-effort Firma/Schwäche/Ort/Branche für einen Slug (warm zuerst, dann Pipeline)."""
    try:
        meta, _ = leadtool.read_lead(ROOT, slug)
        return {"firma": meta.get("firma", ""), "schwaeche": meta.get("schwaeche", ""),
                "ort": meta.get("ort", ""), "branche": meta.get("branche", "")}
    except FileNotFoundError:
        pass
    try:
        for row in leadtool.read_pipeline(ROOT):
            if leadtool.slugify(row.get("firma", "")) == slug:
                return {"firma": row.get("firma", ""), "schwaeche": row.get("schwaeche", ""),
                        "ort": row.get("ort", ""), "branche": row.get("branche", "")}
    except (FileNotFoundError, OSError):
        pass
    return {"firma": slug, "schwaeche": "", "ort": "", "branche": ""}


def _prototyp_info_md(slug: str, url: str, info: dict) -> str:
    """Baut den info.md-Text für den lokalen Prototyp-Ordner (inkl. Live-Link)."""
    zeilen = [
        f"# Prototyp — {info.get('firma') or slug}",
        "",
        f"- **Slug:** {slug}",
        f"- **Live (GitHub Pages):** {url}",
        f"- **Veröffentlicht:** {date.today().isoformat()}",
    ]
    if info.get("ort"):
        zeilen.append(f"- **Ort:** {info['ort']}")
    if info.get("branche"):
        zeilen.append(f"- **Branche:** {info['branche']}")
    if info.get("schwaeche"):
        zeilen.append(f"- **Adressierte Schwäche:** {info['schwaeche']}")
    zeilen += [
        "",
        "HTML-Kopie: [index.html](index.html)",
        "",
        "> Öffentlich unter Shawns Pages-URL sichtbar (echter Firmenname). Demo/unverbindlich.",
        "",
    ]
    return "\n".join(zeilen)


def _resolve_run_file(file_param: str) -> Path:
    """Validiert einen 'discovery/<name>.json'-Pfad gegen Traversal; gibt Path zurück.

    Wirft ValueError, wenn der aufgelöste Pfad nicht unter root/discovery liegt.
    """
    disco_dir = (ROOT / "discovery").resolve()
    candidate = (ROOT / file_param).resolve()
    # candidate muss innerhalb disco_dir liegen
    if candidate != disco_dir and disco_dir not in candidate.parents:
        raise ValueError(f"Ungültiger Pfad '{file_param}' (außerhalb discovery/)")
    return candidate


# ---------------------------------------------------------------------------
# HTTP-Handler
# ---------------------------------------------------------------------------

class CockpitHandler(BaseHTTPRequestHandler):
    server_version = "LeadGen/1.0"

    # Konfiguration (in main() gesetzt)
    api_only: bool = False
    cors_origin: str = "*"

    # --- CORS ---

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", self.cors_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:  # noqa: N802 (stdlib-Namenskonvention)
        # Preflight für entkoppeltes Frontend
        self.send_response(204)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    # --- Antwort-Helfer ---

    def _send_json(self, obj, status: int = 200) -> None:
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json({"error": message}, status)

    def _send_bytes(self, data: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> dict:
        """Liest Content-Length-Bytes und parst JSON; wirft ValueError bei Murks."""
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Ungültiger JSON-Body: {exc}")
        if not isinstance(obj, dict):
            raise ValueError("JSON-Body muss ein Objekt sein")
        return obj

    # --- Routing ---

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        query = self._query()
        try:
            if path == "/api/state":
                self._send_json(build_state(date.today()))
                return
            if path == "/api/discovery/run":
                self._handle_discovery_run(query)
                return
            if path == "/api/outreach/pending":
                self._send_json(outreach.list_pending(ROOT))
                return
            if path == "/api/prototyp/pending":
                self._send_json(prototyp.list_pending(ROOT))
                return
            if path == "/api/portfolio":
                self._send_json(portfolio.load_manifest(ROOT))
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/prototyp", path)
            if m:
                slug = _valid_slug(m.group(1))
                state = prototyp.load(ROOT, slug) or {"slug": slug, "status": "none", "url": None}
                self._send_json(state)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/outreach", path)
            if m:
                slug = _valid_slug(m.group(1))
                state = outreach.load(ROOT, slug) or {"slug": slug, "status": "none", "draft": None}
                self._send_json(state)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/outreach/readiness", path)
            if m:
                slug = _valid_slug(m.group(1))
                try:
                    meta, _ = leadtool.read_lead(ROOT, slug)
                    ist_warm = True
                except FileNotFoundError:
                    meta = {}
                    ist_warm = False
                # prototyp_state aus dem Store (Demo-Link nur bei published)
                try:
                    ps = prototyp.load(ROOT, slug) or {"status": "none", "url": None}
                except Exception:
                    ps = {"status": "none", "url": None}
                lead_ctx = {
                    "warm": ist_warm,
                    "kalt_freigegeben": meta.get("kalt_freigegeben", False),
                    "kontakt": meta.get("kontakt") or {},
                    "anlass": meta.get("schwaeche") or meta.get("anlass") or "",
                    "angebot": meta.get("ucp") or meta.get("angebot") or "",
                    "nutzen": meta.get("roi_these") or meta.get("nutzen") or "",
                    "cta": meta.get("cta") or "",
                    "prototyp_state": ps,
                }
                self._send_json(outreach.outreach_readiness(lead_ctx))
                return
            if path.startswith("/api/"):
                self._send_error_json(404, f"Unbekannte Route: {path}")
                return
            # statisch (nur wenn nicht --api-only)
            if self.api_only:
                self._send_error_json(404, "API-only-Modus: statische Auslieferung deaktiviert")
                return
            self._serve_static(path)
        except ValueError as exc:
            self._send_error_json(400, str(exc))
        except (FileNotFoundError, KeyError) as exc:
            self._send_error_json(404, str(exc))
        except Exception as exc:  # noqa: BLE001
            self._send_error_json(500, str(exc))

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            body = self._read_json_body()
            if path == "/api/leads":
                self._handle_create_lead(body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/status", path)
            if m:
                self._handle_lead_status(m.group(1), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/note", path)
            if m:
                self._handle_lead_note(m.group(1), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/wiedervorlage", path)
            if m:
                self._handle_lead_wiedervorlage(m.group(1), body)
                return
            if path == "/api/discovery/setstatus":
                self._handle_disco_setstatus(body)
                return
            if path == "/api/discovery/uebernehmen":
                self._handle_disco_uebernehmen(body)
                return
            if path == "/api/discovery/reject":
                self._handle_disco_mutate(body, discotool.reject)
                return
            if path == "/api/discovery/restore":
                self._handle_disco_mutate(body, discotool.restore)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/email", path)
            if m:
                self._handle_set_email(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/outreach/request", path)
            if m:
                self._handle_outreach_request(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/outreach/draft", path)
            if m:
                self._handle_outreach_draft(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/outreach/send", path)
            if m:
                self._handle_outreach_send(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/prototyp/request", path)
            if m:
                self._handle_prototyp_request(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/prototyp/draft", path)
            if m:
                self._handle_prototyp_draft(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/prototyp/approve", path)
            if m:
                self._handle_prototyp_approve(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/prototyp/publish", path)
            if m:
                self._handle_prototyp_publish(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/prototyp/rework", path)
            if m:
                self._handle_prototyp_rework(_valid_slug(m.group(1)), body)
                return
            m = re.fullmatch(r"/api/leads/([^/]+)/prototyp/archive", path)
            if m:
                self._handle_prototyp_archive(_valid_slug(m.group(1)), body)
                return
            self._send_error_json(404, f"Unbekannte Route: {path}")
        except ValueError as exc:
            # Duplikat-ValueError als 409, sonst 400
            msg = str(exc)
            if "existiert bereits" in msg:
                self._send_error_json(409, msg)
            else:
                self._send_error_json(400, msg)
        except (FileNotFoundError, KeyError) as exc:
            self._send_error_json(404, str(exc))
        except Exception as exc:  # noqa: BLE001
            self._send_error_json(500, str(exc))

    # --- Query-Parsing ---

    def _query(self) -> dict:
        from urllib.parse import parse_qs, urlparse
        qs = urlparse(self.path).query
        return {k: v[0] for k, v in parse_qs(qs).items()}

    # --- API-Handler ---

    def _handle_discovery_run(self, query: dict) -> None:
        file_param = query.get("file")
        if not file_param:
            raise ValueError("Parameter 'file' fehlt")
        path = _resolve_run_file(file_param)
        if not path.exists():
            raise FileNotFoundError(f"Run-Datei nicht gefunden: {file_param}")
        self._send_json(discotool.load_run(path))

    def _handle_create_lead(self, body: dict) -> None:
        firma = (body.get("firma") or "").strip()
        if not firma:
            raise ValueError("Feld 'firma' fehlt oder ist leer")
        schwaeche = body.get("schwaeche") or ""
        slug = leadtool.add_lead(ROOT, firma, schwaeche=schwaeche, today=date.today())
        # Optionale Anlege-Notiz (warum angenommen / was verbesserbar) direkt anhängen
        notiz = (body.get("notiz") or "").strip()
        if notiz:
            leadtool.add_note(ROOT, slug, notiz, today=date.today())
        self._send_json({"slug": slug}, status=201)

    def _handle_lead_status(self, slug: str, body: dict) -> None:
        status = (body.get("status") or "").strip()
        if not status:
            raise ValueError("Feld 'status' fehlt")
        leadtool.set_status(ROOT, slug, status, today=date.today())
        self._send_json({"ok": True, "slug": slug, "status": status})

    def _handle_lead_note(self, slug: str, body: dict) -> None:
        text = body.get("text") or ""
        if not str(text).strip():
            raise ValueError("Feld 'text' fehlt oder ist leer")
        leadtool.add_note(ROOT, slug, text, today=date.today())
        self._send_json({"ok": True})

    def _handle_lead_wiedervorlage(self, slug: str, body: dict) -> None:
        datum = (body.get("datum") or "").strip()
        if not datum:
            raise ValueError("Feld 'datum' fehlt")
        leadtool.set_wiedervorlage(ROOT, slug, datum)
        self._send_json({"ok": True})

    def _handle_disco_setstatus(self, body: dict) -> None:
        file_param = body.get("file")
        if not file_param:
            raise ValueError("Feld 'file' fehlt")
        if "id" not in body:
            raise ValueError("Feld 'id' fehlt")
        status = body.get("status")
        if not status:
            raise ValueError("Feld 'status' fehlt")
        path = _resolve_run_file(file_param)
        if not path.exists():
            raise FileNotFoundError(f"Run-Datei nicht gefunden: {file_param}")
        run = discotool.load_run(path)
        discotool.set_status(run, int(body["id"]), status, body.get("url", ""))
        discotool.save_run(path, run)
        self._send_json({"ok": True})

    def _handle_disco_mutate(self, body: dict, fn) -> None:
        """Gemeinsamer Handler für reject/restore: Run laden, Kandidat mutieren, speichern."""
        file_param = body.get("file")
        if not file_param:
            raise ValueError("Feld 'file' fehlt")
        if "id" not in body:
            raise ValueError("Feld 'id' fehlt")
        path = _resolve_run_file(file_param)
        if not path.exists():
            raise FileNotFoundError(f"Run-Datei nicht gefunden: {file_param}")
        run = discotool.load_run(path)
        fn(run, int(body["id"]))
        discotool.save_run(path, run)
        self._send_json({"ok": True})

    def _handle_disco_uebernehmen(self, body: dict) -> None:
        file_param = body.get("file")
        if not file_param:
            raise ValueError("Feld 'file' fehlt")
        which = body.get("which")
        if which is None:
            raise ValueError("Feld 'which' fehlt")
        if which != "auto" and not isinstance(which, list):
            raise ValueError("Feld 'which' muss 'auto' oder eine Liste von ints sein")
        path = _resolve_run_file(file_param)
        if not path.exists():
            raise FileNotFoundError(f"Run-Datei nicht gefunden: {file_param}")
        run = discotool.load_run(path)
        website = (body.get("website") or "").strip()
        notiz = (body.get("notiz") or "").strip()
        schwaeche = (body.get("schwaeche") or "").strip()
        result = discotool.create_leads(ROOT, run, which, date.today(), website=website, notiz=notiz, schwaeche=schwaeche)
        discotool.save_run(path, run)
        self._send_json(result)

    def _handle_set_email(self, slug: str, body: dict) -> None:
        email = (body.get("email") or "").strip()
        if not email:
            raise ValueError("Feld 'email' fehlt oder ist leer")
        leadtool.set_email(ROOT, slug, email)
        self._send_json({"ok": True})

    def _handle_outreach_request(self, slug: str, body: dict) -> None:
        # Pflicht: angebot. Optional: nutzen, ton, cta, betreff, prototyp.
        if not (body.get("angebot") or "").strip():
            raise ValueError("Feld 'angebot' fehlt")
        data = outreach.save_request(ROOT, slug, body)
        self._send_json(data, status=201)

    def _handle_outreach_draft(self, slug: str, body: dict) -> None:
        betreff = (body.get("betreff") or "").strip()
        text = (body.get("text") or "").strip()
        if not betreff or not text:
            raise ValueError("Felder 'betreff' und 'text' sind Pflicht")
        self._send_json(outreach.set_draft(ROOT, slug, betreff, text))

    def _handle_outreach_send(self, slug: str, body: dict) -> None:
        import base64
        # validate_send prüft: Entwurf vorhanden, nicht already sent, E-Mail vorhanden
        state = outreach.validate_send(ROOT, slug)
        meta, _ = leadtool.read_lead(ROOT, slug)
        to_addr = (meta.get("kontakt") or {}).get("email") or ""
        draft = state["draft"]
        req = state.get("request") or {}
        attachment = None
        proto = req.get("prototyp") or {}
        if proto.get("mode") == "anhang" and proto.get("data"):
            attachment = {
                "filename": proto.get("filename", "prototyp.bin"),
                "data": base64.b64decode(proto["data"]),
                "maintype": proto.get("maintype", "application"),
                "subtype": proto.get("subtype", "octet-stream"),
            }
        cfg = config.smtp_config()
        msg = mailer.build_message(from_addr=cfg["from_addr"], to_addr=to_addr,
                                   subject=draft["betreff"], body=draft["text"],
                                   attachment=attachment)
        eml_path = (ROOT / "outreach" / f"{slug}.eml")
        # W4.3: 'direct' nur bei expliziter Auswahl im Body; sonst immer 'draft'
        requested_mode = (body.get("send_mode") or "").strip().lower()
        mode = "direct" if requested_mode == "direct" else config.send_mode()
        result = mailer.deliver(msg, mode=mode, cfg=cfg, eml_path=eml_path)
        outreach.mark_sent(ROOT, slug)
        leadtool.mark_contacted(ROOT, slug, betreff=draft["betreff"], today=date.today())
        self._send_json({"ok": True, "send_mode": mode, **result})

    def _handle_prototyp_request(self, slug: str, body: dict) -> None:
        data = prototyp.save_request(ROOT, slug, today=date.today())
        self._send_json(data, status=201)

    def _handle_prototyp_draft(self, slug: str, body: dict) -> None:
        """Speichert HTML lokal → draft_ready. Deployt NICHT automatisch."""
        html = body.get("html") or ""
        if "<html" not in html.lower():
            raise ValueError("Feld 'html' fehlt oder ist kein HTML-Dokument")
        self._send_json(prototyp.save_draft(ROOT, slug, html))

    def _handle_prototyp_approve(self, slug: str, body: dict) -> None:
        """Setzt Status approved_local (menschliche Freigabe, nur aus draft_ready)."""
        self._send_json(prototyp.approve_local(ROOT, slug))

    def _handle_prototyp_publish(self, slug: str, body: dict) -> None:
        """Veröffentlicht die Demo: deploy (injizierbar) + published. Nur bei approved_local."""
        state = prototyp.load(ROOT, slug)
        if state is None or state.get("status") != "approved_local":
            raise ValueError(
                "Publish erfordert Status 'approved_local'"
            )
        repo = config.prototyp_repo_path()
        base = config.prototyp_pages_base()
        if not repo or not base:
            raise ValueError("PROTOTYP_REPO_PATH/PROTOTYP_PAGES_BASE nicht gesetzt (.env)")
        html = state.get("html_local") or ""
        if not html.strip():
            raise ValueError(
                f"Kein lokales HTML für '{slug}' — Publish würde eine leere Seite deployen. "
                "Erst einen Entwurf (draft) speichern."
            )
        url = deploy.deploy(slug, html, repo_path=Path(repo), pages_base=base)
        data = prototyp.mark_published(ROOT, slug, url)
        # Lokalen Ordner prototypes/<slug>/ mit HTML-Kopie + info.md (inkl. Live-Link) anlegen
        info = _lead_summary(slug)
        info_md = _prototyp_info_md(slug, url, info)
        prototyp.write_bundle(ROOT.parent / "prototypes", slug, html, info_md)
        self._send_json(data)

    def _handle_prototyp_rework(self, slug: str, body: dict) -> None:
        """Markiert Entwurf zur Überarbeitung."""
        self._send_json(prototyp.mark_rework(ROOT, slug))

    def _handle_prototyp_archive(self, slug: str, body: dict) -> None:
        """Archiviert den Prototyp-Eintrag."""
        self._send_json(prototyp.mark_archived(ROOT, slug))

    # --- Statisches Ausliefern ---

    def _serve_static(self, path: str) -> None:
        rel = "index.html" if path in ("", "/") else path.lstrip("/")
        target = (FRONTEND / rel).resolve()
        frontend_root = FRONTEND.resolve()
        # Traversal-Schutz: target muss unter frontend/ liegen
        if target != frontend_root and frontend_root not in target.parents:
            self._send_error_json(404, "Nicht gefunden")
            return
        if not target.is_file():
            self._send_error_json(404, "Nicht gefunden")
            return
        content_type = MIME.get(target.suffix.lower(), "application/octet-stream")
        self._send_bytes(target.read_bytes(), content_type)

    # --- Logging knapp halten ---

    def log_message(self, fmt, *args) -> None:  # noqa: A003
        # knappes Log auf stderr im Stil der CLI-Tools
        import sys
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="LeadGen-Backend (JSON-API)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="HTTP-Port (default 8723)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind-Host (default 127.0.0.1)")
    parser.add_argument("--api-only", action="store_true",
                        help="Nur JSON-API bedienen, kein statisches Frontend ausliefern")
    parser.add_argument("--cors-origin", default="*",
                        help="Wert für Access-Control-Allow-Origin (default '*')")
    args = parser.parse_args()

    CockpitHandler.api_only = args.api_only
    CockpitHandler.cors_origin = args.cors_origin

    server = ThreadingHTTPServer((args.host, args.port), CockpitHandler)
    url = f"http://{args.host}:{args.port}"
    mode = "API-only" if args.api_only else "API + Frontend"
    print(f"LeadGen-Backend ({mode}) läuft auf {url}  (Strg+C zum Beenden)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
