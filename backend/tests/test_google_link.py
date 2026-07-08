import urllib.parse
from datetime import date

import leadtool


# --- google_maps_link ------------------------------------------------------

def test_link_from_firma_only_appends_hamburg():
    url = leadtool.google_maps_link("Friseur Schnittwerk")
    assert url.startswith("https://www.google.com/maps/search/?api=1&query=")
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["query"][0]
    assert query == "Friseur Schnittwerk Hamburg"


def test_link_with_adresse_does_not_double_hamburg():
    url = leadtool.google_maps_link("Barbershop", "Friedensallee 9, 22765 Hamburg")
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["query"][0]
    assert query.lower().count("hamburg") == 1


def test_link_encodes_umlauts():
    url = leadtool.google_maps_link("Zahnärzte Isestraße")
    # Umlaute korrekt url-encoded, nicht roh im Link
    assert "ä" not in url and "ß" not in url
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["query"][0]
    assert query == "Zahnärzte Isestraße Hamburg"


def test_link_empty_firma_returns_empty():
    assert leadtool.google_maps_link("") == ""
    assert leadtool.google_maps_link("   ") == ""


# --- add_lead speichert Adresse -------------------------------------------

def test_add_lead_stores_adresse(repo):
    leadtool.add_lead(repo, "Barbershop Ottensen", adresse="Friedensallee 9, Hamburg",
                      today=date(2026, 7, 8))
    rows = leadtool.read_pipeline(repo)
    assert rows[0]["adresse"] == "Friedensallee 9, Hamburg"


# --- graduate schreibt adresse + google_eintrag ---------------------------

def test_graduate_writes_adresse_and_google_eintrag(repo):
    leadtool.add_lead(repo, "Barbershop Ottensen", schwaeche="keine Website",
                      adresse="Friedensallee 9, 22765 Hamburg", today=date(2026, 7, 8))
    leadtool.graduate(repo, "barbershop-ottensen", status="in_klaerung", today=date(2026, 7, 8))
    meta, _ = leadtool.read_lead(repo, "barbershop-ottensen")
    assert meta["adresse"] == "Friedensallee 9, 22765 Hamburg"
    assert meta["google_eintrag"].startswith("https://www.google.com/maps/search/")
    assert "Barbershop" in urllib.parse.unquote(meta["google_eintrag"])


# --- Abwärtskompatibilität: alte Tabelle ohne Adresse-Spalte --------------

def test_parse_pipeline_backfills_missing_adresse():
    # Alt-Schema: 7 Spalten (ohne Adresse)
    old = (
        "| slug | Firma | Status | Schwäche | kontaktiert_am | Wiedervorlage | Notiz |\n"
        "|---|---|---|---|---|---|---|\n"
        "| alpha | Alpha GmbH | identifiziert | keine Website | — | — | — |\n"
    )
    rows = leadtool.parse_pipeline_table(old)
    assert len(rows) == 1
    assert rows[0]["slug"] == "alpha"
    assert rows[0]["firma"] == "Alpha GmbH"
    assert rows[0]["adresse"] == ""
    assert rows[0]["status"] == "identifiziert"
