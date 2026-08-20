"""W2.3 Datenintegrität — Lücken im CRM-Statusmodell.

Deckt ab:
  - Ungültige Statusübergänge (direkte Sprünge auf unbekannte Status)
  - Kalt→Warm-Graduierung: warmer Lead fällt nicht zurück in pipeline.md
  - Warmer Lead bleibt NICHT in pipeline.md nach Graduierung
  - Doppelte Slugs (Ist-Verhalten dokumentieren + sichern)
  - Wiedervorlage: ungültiges Datumsformat, Vergangenheitsdatum
  - Notizen: leere Notiz, Sonderzeichen/Umlaute-Encoding
  - priority_score() / next_action(): Negativfälle ohne Felder
"""
import pytest
from datetime import date

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import leadtool


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _minimal_lead_dict():
    """Minimales Lead-dict ohne optionale Felder — Robustheitstest für reine Funktionen."""
    return {"slug": "minimal", "status": "identifiziert"}


# ===========================================================================
# 1. Statusübergänge — ungültige/unbekannte Status
# ===========================================================================

class TestUngueltigeStatusuebergaenge:
    def test_unbekannter_status_kalt_raises(self, repo):
        """set_status mit völlig unbekanntem Status muss ValueError werfen."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        with pytest.raises(ValueError):
            leadtool.set_status(repo, "test-gmbh", "fantastisch", today=date(2026, 6, 2))

    def test_unbekannter_status_warm_raises(self, repo):
        """Auch bei warmem Lead darf ein unbekannter Status nicht akzeptiert werden."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "test-gmbh", "in_klaerung", today=date(2026, 6, 2))
        with pytest.raises(ValueError):
            leadtool.set_status(repo, "test-gmbh", "phantomstatus", today=date(2026, 6, 3))

    def test_alter_demo_status_nicht_in_all_statuses(self, repo):
        """'demo' ist kein erlaubter Status — historischer Schutz."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        with pytest.raises(ValueError):
            leadtool.set_status(repo, "test-gmbh", "demo", today=date(2026, 6, 2))

    def test_leerer_status_raises(self, repo):
        """Leerer String ist kein gültiger Status."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        with pytest.raises(ValueError):
            leadtool.set_status(repo, "test-gmbh", "", today=date(2026, 6, 2))

    def test_unbekannter_slug_kalt_raises(self, repo):
        """set_status auf nicht existierenden Slug muss ValueError werfen."""
        with pytest.raises(ValueError):
            leadtool.set_status(repo, "gibtsnicht", "identifiziert", today=date(2026, 6, 1))

    def test_cold_status_auf_warmem_lead_bleibt_in_datei(self, repo):
        """Kalter Status auf bereits warmem Lead: Datei bleibt, pipeline.md bleibt leer."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "test-gmbh", "in_klaerung", today=date(2026, 6, 2))
        # Jetzt kalten Status setzen (nicht graduieren-Pfad, sondern Frontmatter-Update)
        leadtool.set_status(repo, "test-gmbh", "inaktiv", today=date(2026, 6, 3))
        # Datei muss noch existieren
        assert leadtool.lead_path(repo, "test-gmbh").exists()
        # Pipeline bleibt leer (warmer Lead fällt nicht zurück)
        assert leadtool.read_pipeline(repo) == []
        # Status korrekt im Frontmatter
        meta, _ = leadtool.read_lead(repo, "test-gmbh")
        assert meta["status"] == "inaktiv"


# ===========================================================================
# 2. Kalt→Warm-Graduierung: kein Rückfall in pipeline.md
# ===========================================================================

class TestGraduierungKeinRueckfall:
    def test_graduierter_lead_nicht_mehr_in_pipeline(self, repo):
        """Nach Graduierung verschwindet der Lead aus pipeline.md."""
        leadtool.add_lead(repo, "Warm GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "warm-gmbh", "in_klaerung", today=date(2026, 6, 5))
        assert leadtool.read_pipeline(repo) == []

    def test_graduierter_lead_hat_eigene_datei(self, repo):
        """leads/<slug>.md existiert nach Graduierung."""
        leadtool.add_lead(repo, "Warm GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "warm-gmbh", "in_klaerung", today=date(2026, 6, 5))
        assert leadtool.lead_path(repo, "warm-gmbh").exists()

    def test_nach_graduierung_nochmals_warmer_status_nur_frontmatter(self, repo):
        """Mehrfacher warmer Status-Wechsel erzeugt keine zweite Datei und keinen pipeline-Eintrag."""
        leadtool.add_lead(repo, "Warm GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "warm-gmbh", "in_klaerung", today=date(2026, 6, 5))
        leadtool.set_status(repo, "warm-gmbh", "angebot_raus", today=date(2026, 6, 10))
        # Immer noch: pipeline leer, genau eine Datei
        assert leadtool.read_pipeline(repo) == []
        leads_files = list((repo / "leads").glob("warm-gmbh*.md"))
        assert len(leads_files) == 1

    def test_zwei_verschiedene_leads_graduierung_unabhaengig(self, repo):
        """Graduierung von Lead A beeinflusst Lead B nicht."""
        leadtool.add_lead(repo, "Alpha GmbH", today=date(2026, 6, 1))
        leadtool.add_lead(repo, "Beta GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "alpha-gmbh", "in_klaerung", today=date(2026, 6, 5))
        # Beta bleibt in pipeline
        pipeline = leadtool.read_pipeline(repo)
        assert len(pipeline) == 1
        assert pipeline[0]["slug"] == "beta-gmbh"
        # Alpha hat Datei
        assert leadtool.lead_path(repo, "alpha-gmbh").exists()


# ===========================================================================
# 3. Doppelte Slugs
# ===========================================================================

class TestDoppelteSlug:
    def test_doppelter_slug_kalt_kalt_raises(self, repo):
        """add_lead mit identischem Namen (→ gleichem Slug) in pipeline.md muss ValueError werfen."""
        leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 1))
        with pytest.raises(ValueError):
            leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 2))

    def test_doppelter_slug_kein_zweiter_eintrag_in_pipeline(self, repo):
        """Auch wenn add_lead wirft, darf pipeline.md keinen doppelten Eintrag enthalten."""
        leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 1))
        try:
            leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 2))
        except ValueError:
            pass
        rows = leadtool.read_pipeline(repo)
        assert len(rows) == 1

    def test_doppelter_slug_warm_kalt_raises(self, repo):
        """add_lead darf nicht gelingen, wenn slug bereits als warme Datei existiert."""
        leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 1))
        leadtool.set_status(repo, "mueller-sanitaer", "in_klaerung", today=date(2026, 6, 5))
        with pytest.raises(ValueError):
            leadtool.add_lead(repo, "Müller Sanitär", today=date(2026, 6, 10))

    def test_verschiedene_slugs_kein_konflikt(self, repo):
        """Verschiedene Firmen mit verschiedenen Slugs dürfen beide angelegt werden."""
        leadtool.add_lead(repo, "Alpha GmbH", today=date(2026, 6, 1))
        leadtool.add_lead(repo, "Beta GmbH", today=date(2026, 6, 1))
        assert len(leadtool.read_pipeline(repo)) == 2


# ===========================================================================
# 4. Wiedervorlage — ungültige Fälle
# ===========================================================================

class TestWiedervorlageNegativ:
    def test_ungültiges_datumsformat_raises(self, repo):
        """Nicht-ISO-Datum muss ValueError auslösen."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        with pytest.raises(ValueError):
            leadtool.set_wiedervorlage(repo, "test-gmbh", "31.07.2026")

    def test_datumsformat_mit_uhrzeit_raises(self, repo):
        """ISO-Datum mit Uhrzeit-Anhang ist kein reines Datum — muss ablehnen."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        with pytest.raises(ValueError):
            leadtool.set_wiedervorlage(repo, "test-gmbh", "2026-07-31T10:00:00")

    def test_leerer_string_raises(self, repo):
        """Leerer Datums-String muss ValueError auslösen."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        with pytest.raises(ValueError):
            leadtool.set_wiedervorlage(repo, "test-gmbh", "")

    def test_vergangenheitsdatum_wird_gesetzt_kein_fehler(self, repo):
        """Vergangenheitsdatum ist technisch gültig — set_wiedervorlage lehnt es NICHT ab.

        Begründung: Das Datum war evtl. gestern fällig und wird jetzt manuell korrigiert.
        Der Report zeigt es als 'fällig' an — das ist korrekt, kein Fehler.
        """
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        # Kein Fehler erwartet
        leadtool.set_wiedervorlage(repo, "test-gmbh", "2026-01-01")
        assert leadtool.read_pipeline(repo)[0]["wiedervorlage"] == "2026-01-01"

    def test_vergangenheitsdatum_erscheint_in_report_faellig(self, repo):
        """Vergangenheitsdatum macht den Lead im Report als 'wiedervorlage_faellig' sichtbar."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        leadtool.set_wiedervorlage(repo, "test-gmbh", "2026-01-01")
        rep = leadtool.report(repo, today=date(2026, 6, 1))
        assert any(c["slug"] == "test-gmbh" for c in rep["wiedervorlage_faellig"])

    def test_monatsnamen_format_raises(self, repo):
        """Monatsnamen wie '5. Juli' sind kein ISO-Datum."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        with pytest.raises(ValueError):
            leadtool.set_wiedervorlage(repo, "test-gmbh", "5. Juli")


# ===========================================================================
# 5. Notizen — leere Notiz und Sonderzeichen/Umlaute
# ===========================================================================

class TestNotizenNegativUndEncoding:
    def test_leere_notiz_kalt_kein_absturz(self, repo):
        """Leere Notiz auf kaltem Lead darf nicht abstürzen — Ist-Verhalten sichern."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        # Kein Fehler erwartet; leere Notiz wird gesetzt (oder ignoriert)
        leadtool.add_note(repo, "test-gmbh", "", today=date(2026, 6, 2))
        # Pipeline-Zeile bleibt konsistent lesbar
        rows = leadtool.read_pipeline(repo)
        assert len(rows) == 1

    def test_leere_notiz_warm_kein_absturz(self, repo):
        """Leere Notiz auf warmem Lead darf nicht abstürzen."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "test-gmbh", "in_klaerung", today=date(2026, 6, 2))
        leadtool.add_note(repo, "test-gmbh", "", today=date(2026, 6, 3))
        # Datei bleibt lesbar
        meta, body = leadtool.read_lead(repo, "test-gmbh")
        assert isinstance(body, str)

    def test_umlaute_in_notiz_utf8_korrekt(self, repo):
        """Umlaute/Sonderzeichen in Notizen müssen UTF-8-korrekt gespeichert und gelesen werden."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "test-gmbh", "in_klaerung", today=date(2026, 6, 2))
        text = "Müller möchte Änderungen — Preis: 3.500 € · Frist: März"
        leadtool.add_note(repo, "test-gmbh", text, today=date(2026, 6, 3))
        _, body = leadtool.read_lead(repo, "test-gmbh")
        assert "Müller" in body
        assert "Änderungen" in body
        assert "€" in body
        assert "März" in body

    def test_sonderzeichen_in_notiz_kalt_utf8_korrekt(self, repo):
        """Umlaute in Notiz einer Kalt-Pipeline-Zeile werden UTF-8-korrekt gespeichert."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        text = "Büro geschlossen — bitte Öffnungszeiten prüfen"
        leadtool.add_note(repo, "test-gmbh", text, today=date(2026, 6, 2))
        rows = leadtool.read_pipeline(repo)
        assert "Büro" in rows[0]["notiz"]
        assert "Öffnungszeiten" in rows[0]["notiz"]

    def test_pipe_zeichen_in_notiz_wird_escaped(self, repo):
        """Pipe '|' in Notiz darf die Markdown-Tabelle nicht zerstören."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        leadtool.add_note(repo, "test-gmbh", "Option A | Option B", today=date(2026, 6, 2))
        # Tabelle muss noch genau eine Zeile enthalten (nicht mehr wegen geplatzter Zellen)
        rows = leadtool.read_pipeline(repo)
        assert len(rows) == 1

    def test_notiz_unbekannter_slug_raises(self, repo):
        """add_note auf nicht existierenden Slug muss ValueError werfen."""
        with pytest.raises(ValueError):
            leadtool.add_note(repo, "gibtsnicht", "Hallo", today=date(2026, 6, 1))


# ===========================================================================
# 6. priority_score() — Negativfälle / minimale Dicts
# ===========================================================================

class TestPriorityScoreNegativ:
    def test_leeres_dict_kein_absturz(self):
        """priority_score({}, today) darf nicht abstürzen."""
        r = leadtool.priority_score({}, date(2026, 8, 20))
        assert "score" in r
        assert r["score"] >= 0

    def test_minimales_dict_nur_status(self):
        """Nur 'status' im Dict — alle anderen Felder fehlen."""
        r = leadtool.priority_score({"status": "identifiziert"}, date(2026, 8, 20))
        assert "faktoren" in r
        assert r["score"] >= 0

    def test_none_felder_kein_absturz(self):
        """None-Werte in schwaeche, website, wiedervorlage dürfen keinen Fehler verursachen."""
        lead = {
            "slug": "test", "status": "identifiziert", "warm": False,
            "schwaeche": None, "website": None, "wiedervorlage": None,
            "kontakt": None, "branche": None, "ort": None,
        }
        r = leadtool.priority_score(lead, date(2026, 8, 20))
        assert r["score"] >= 0

    def test_ungültiges_wiedervorlage_datum_kein_absturz(self):
        """Ungültiges Datum-Format in wiedervorlage: kein Absturz, wert=0."""
        lead = _minimal_lead_dict()
        lead["wiedervorlage"] = "kein-datum"
        r = leadtool.priority_score(lead, date(2026, 8, 20))
        assert r["faktoren"]["wiedervorlage_faellig"]["wert"] == 0

    def test_alle_faktoren_immer_vorhanden(self):
        """Alle vier Faktor-Keys müssen immer zurückgegeben werden — auch bei leerem Dict."""
        r = leadtool.priority_score({}, date(2026, 8, 20))
        for key in ("befundstaerke", "segmentpassung", "datenvollstaendigkeit", "wiedervorlage_faellig"):
            assert key in r["faktoren"], f"Faktor '{key}' fehlt bei leerem Dict"

    def test_score_entspricht_summe_der_faktorwerte(self):
        """score == Summe aller Faktor-Werte (Konsistenzprüfung)."""
        lead = {
            "status": "analysiert", "warm": False,
            "schwaeche": "Keine Website, Nicht mobil",
            "website": "test.de", "wiedervorlage": "2026-08-19",
            "branche": "Handwerk", "ort": "Hamburg",
        }
        r = leadtool.priority_score(lead, date(2026, 8, 20))
        expected = sum(f["wert"] for f in r["faktoren"].values())
        assert r["score"] == expected


# ===========================================================================
# 7. next_action() — Negativfälle / minimale Dicts
# ===========================================================================

class TestNextActionNegativ:
    def test_leeres_dict_gibt_pruefen(self):
        """next_action({}, today) darf nicht abstürzen und gibt 'pruefen' zurück."""
        r = leadtool.next_action({}, date(2026, 8, 20))
        assert r == "pruefen"

    def test_minimales_dict_nur_status_gibt_gueltigen_wert(self):
        """Nur 'status' im Dict — valides Ergebnis ohne Absturz."""
        valid = {"pruefen", "qualifizieren", "demo_beauftragen", "kontaktieren", "nachfassen"}
        r = leadtool.next_action({"status": "identifiziert"}, date(2026, 8, 20))
        assert r in valid

    def test_none_felder_kein_absturz(self):
        """None-Werte in schwaeche, website, wiedervorlage, kontaktiert_am — kein Absturz."""
        lead = {
            "slug": "test", "status": "kontaktiert", "warm": False,
            "schwaeche": None, "website": None, "wiedervorlage": None,
            "kontaktiert_am": None,
        }
        r = leadtool.next_action(lead, date(2026, 8, 20))
        assert isinstance(r, str)

    def test_ungültiges_wiedervorlage_datum_wird_ignoriert(self):
        """Ungültiges Datum in wiedervorlage: Regel 1 greift nicht, kein Absturz."""
        lead = _minimal_lead_dict()
        lead["wiedervorlage"] = "kein-datum"
        lead["schwaeche"] = "Keine Website"
        # Status identifiziert + Schwäche → qualifizieren (Wiedervorlage-Regel ignoriert)
        r = leadtool.next_action(lead, date(2026, 8, 20))
        assert r == "qualifizieren"

    def test_ungültiges_kontaktiert_am_wird_ignoriert(self):
        """Ungültiges kontaktiert_am: Regel 2 greift nicht → kein nachfassen allein deshalb."""
        lead = {
            "status": "kontaktiert", "warm": False,
            "schwaeche": "", "website": "", "wiedervorlage": "",
            "kontaktiert_am": "gestern",
        }
        r = leadtool.next_action(lead, date(2026, 8, 20))
        # Kann nur pruefen sein (kein Datum → kein nachfassen durch Regel 2)
        assert r in {"pruefen", "qualifizieren", "kontaktieren"}

    def test_warm_false_warmer_status_in_klaerung_gibt_kontaktieren(self):
        """warm=False aber status=in_klaerung: next_action folgt dem Status, nicht dem warm-Flag."""
        lead = {
            "status": "in_klaerung", "warm": False,
            "schwaeche": "", "website": "", "wiedervorlage": "", "kontaktiert_am": "",
        }
        r = leadtool.next_action(lead, date(2026, 8, 20))
        # Status dominiert: in_klaerung ist in WARM_STATUSES → kontaktieren
        assert r == "kontaktieren"


# ===========================================================================
# 8. report() — Negativfälle
# ===========================================================================

class TestReportNegativ:
    def test_leere_pipeline_kein_absturz(self, repo):
        """report() auf leerem Repo darf nicht abstürzen."""
        rep = leadtool.report(repo, today=date(2026, 6, 1))
        assert rep["keine_antwort"] == []
        assert rep["wiedervorlage_faellig"] == []

    def test_kontaktiert_ohne_datum_nicht_in_keine_antwort(self, repo):
        """kontaktiert-Lead ohne kontaktiert_am darf NICHT in keine_antwort erscheinen."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        # Status setzen, aber kontaktiert_am leer lassen (manuell)
        rows = leadtool.read_pipeline(repo)
        rows[0]["status"] = "kontaktiert"
        rows[0]["kontaktiert_am"] = ""
        leadtool.write_pipeline(repo, rows)
        rep = leadtool.report(repo, today=date(2026, 6, 30))
        assert rep["keine_antwort"] == []

    def test_warmer_lead_ohne_wiedervorlage_nicht_faellig(self, repo):
        """Warmer Lead ohne Wiedervorlage-Datum erscheint nicht in wiedervorlage_faellig."""
        leadtool.add_lead(repo, "Test GmbH", today=date(2026, 6, 1))
        leadtool.set_status(repo, "test-gmbh", "in_klaerung", today=date(2026, 6, 2))
        rep = leadtool.report(repo, today=date(2026, 6, 30))
        assert not any(c["slug"] == "test-gmbh" for c in rep["wiedervorlage_faellig"])
