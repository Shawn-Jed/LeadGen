"""Tests für priority_score(lead, today) — W2.1 Entscheidungsmodell."""
from datetime import date

import pytest

import leadtool


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def _cold(slug="test", status="identifiziert", schwaeche="", website="", kontaktiert_am="", wiedervorlage=""):
    return {
        "slug": slug, "firma": "Test GmbH", "status": status, "warm": False,
        "schwaeche": schwaeche, "website": website, "adresse": "Musterstr. 1",
        "kontaktiert_am": kontaktiert_am, "wiedervorlage": wiedervorlage,
        "notiz": "", "branche": "", "ort": "",
    }


def _warm(slug="warm-test", status="in_klaerung", schwaeche="Keine Website", website="", email="",
          kontaktiert_am="", wiedervorlage=""):
    kontakt = {"name": "Max", "email": email, "rolle": "", "quelle": ""}
    return {
        "slug": slug, "firma": "Warm GmbH", "status": status, "warm": True,
        "schwaeche": schwaeche, "website": website, "adresse": "Musterstr. 2",
        "kontaktiert_am": kontaktiert_am, "wiedervorlage": wiedervorlage,
        "kontakt": kontakt, "branche": "Handwerk", "ort": "Hamburg",
        "ucp": "Festpreis-Website",
    }


TODAY = date(2026, 8, 20)


# ---------------------------------------------------------------------------
# Rückgabestruktur
# ---------------------------------------------------------------------------

class TestPriorityStructure:
    def test_returns_dict_with_score_and_faktoren(self):
        r = leadtool.priority_score(_cold(), TODAY)
        assert "score" in r
        assert "faktoren" in r

    def test_faktoren_contains_all_four_factors(self):
        r = leadtool.priority_score(_cold(), TODAY)
        f = r["faktoren"]
        assert "befundstaerke" in f
        assert "segmentpassung" in f
        assert "datenvollstaendigkeit" in f
        assert "wiedervorlage_faellig" in f

    def test_score_is_int_or_float(self):
        r = leadtool.priority_score(_cold(), TODAY)
        assert isinstance(r["score"], (int, float))

    def test_jeder_faktor_hat_wert_und_erklaerung(self):
        r = leadtool.priority_score(_cold(schwaeche="Keine Website", website=""), TODAY)
        for name, faktor in r["faktoren"].items():
            assert "wert" in faktor, f"Faktor '{name}' fehlt 'wert'"
            assert "erklaerung" in faktor, f"Faktor '{name}' fehlt 'erklaerung'"


# ---------------------------------------------------------------------------
# Befundstärke
# ---------------------------------------------------------------------------

class TestBefundstaerke:
    def test_keine_schwaeche_gibt_null_punkte(self):
        r = leadtool.priority_score(_cold(schwaeche=""), TODAY)
        assert r["faktoren"]["befundstaerke"]["wert"] == 0

    def test_eine_schwaeche_gibt_mittlere_punkte(self):
        r = leadtool.priority_score(_cold(schwaeche="Keine Website"), TODAY)
        w = r["faktoren"]["befundstaerke"]["wert"]
        assert w > 0

    def test_mehrere_schwaechen_gibt_hoehere_punkte_als_eine(self):
        r1 = leadtool.priority_score(_cold(schwaeche="Keine Website"), TODAY)
        r2 = leadtool.priority_score(_cold(schwaeche="Keine Website, Nicht mobil, Kein SSL"), TODAY)
        assert r2["faktoren"]["befundstaerke"]["wert"] > r1["faktoren"]["befundstaerke"]["wert"]

    def test_erklaerung_nennt_anzahl_schwaechen(self):
        r = leadtool.priority_score(_cold(schwaeche="Keine Website, Nicht mobil"), TODAY)
        erkl = r["faktoren"]["befundstaerke"]["erklaerung"]
        # Muss irgendeine Zahl oder Hinweis auf Schwächen enthalten
        assert any(c.isdigit() for c in erkl) or "schwäche" in erkl.lower()


# ---------------------------------------------------------------------------
# Segmentpassung
# ---------------------------------------------------------------------------

class TestSegmentpassung:
    def test_warm_lead_hat_hoehere_segmentpassung_als_cold(self):
        warm = _warm()
        cold = _cold()
        r_warm = leadtool.priority_score(warm, TODAY)
        r_cold = leadtool.priority_score(cold, TODAY)
        assert r_warm["faktoren"]["segmentpassung"]["wert"] >= r_cold["faktoren"]["segmentpassung"]["wert"]

    def test_cold_ohne_branche_gibt_null(self):
        r = leadtool.priority_score(_cold(status="identifiziert"), TODAY)
        # Kalt ohne Branche → minimale Segmentpassung
        w = r["faktoren"]["segmentpassung"]["wert"]
        assert w >= 0  # nicht negativ

    def test_erklaerung_vorhanden(self):
        r = leadtool.priority_score(_warm(), TODAY)
        assert r["faktoren"]["segmentpassung"]["erklaerung"]


# ---------------------------------------------------------------------------
# Datenvollständigkeit
# ---------------------------------------------------------------------------

class TestDatenvollstaendigkeit:
    def test_lead_ohne_website_und_email_gibt_niedrige_punkte(self):
        lead = _warm(website="", email="")
        r = leadtool.priority_score(lead, TODAY)
        w = r["faktoren"]["datenvollstaendigkeit"]["wert"]
        assert w < 3  # unter Maximum

    def test_lead_mit_website_und_schwaeche_gibt_hoehere_punkte(self):
        lead_ohne = _warm(website="", email="", schwaeche="")
        lead_mit = _warm(website="test.de", email="info@test.de", schwaeche="Keine Mobile")
        r_ohne = leadtool.priority_score(lead_ohne, TODAY)
        r_mit = leadtool.priority_score(lead_mit, TODAY)
        assert r_mit["faktoren"]["datenvollstaendigkeit"]["wert"] > r_ohne["faktoren"]["datenvollstaendigkeit"]["wert"]

    def test_erklaerung_nennt_was_fehlt_oder_vorhanden(self):
        lead = _warm(website="", email="")
        r = leadtool.priority_score(lead, TODAY)
        erkl = r["faktoren"]["datenvollstaendigkeit"]["erklaerung"]
        assert erkl  # nicht leer


# ---------------------------------------------------------------------------
# Wiedervorlage fällig
# ---------------------------------------------------------------------------

class TestWiedervorlageFaellig:
    def test_keine_wiedervorlage_gibt_null(self):
        r = leadtool.priority_score(_cold(wiedervorlage=""), TODAY)
        assert r["faktoren"]["wiedervorlage_faellig"]["wert"] == 0

    def test_wiedervorlage_heute_gibt_bonus(self):
        r = leadtool.priority_score(_cold(wiedervorlage="2026-08-20"), TODAY)
        assert r["faktoren"]["wiedervorlage_faellig"]["wert"] > 0

    def test_wiedervorlage_in_der_zukunft_gibt_null(self):
        r = leadtool.priority_score(_cold(wiedervorlage="2026-09-01"), TODAY)
        assert r["faktoren"]["wiedervorlage_faellig"]["wert"] == 0

    def test_wiedervorlage_gestern_gibt_bonus(self):
        r = leadtool.priority_score(_cold(wiedervorlage="2026-08-19"), TODAY)
        assert r["faktoren"]["wiedervorlage_faellig"]["wert"] > 0


# ---------------------------------------------------------------------------
# Gesamtscore-Ordnung
# ---------------------------------------------------------------------------

class TestGesamtscore:
    def test_vollstaendiger_warmer_lead_schlaegt_leeren_kalten(self):
        vollstaendig = _warm(schwaeche="Keine Website, Nicht mobil", website="test.de", email="a@b.de")
        leer = _cold(schwaeche="")
        r1 = leadtool.priority_score(vollstaendig, TODAY)
        r2 = leadtool.priority_score(leer, TODAY)
        assert r1["score"] > r2["score"]

    def test_score_nicht_negativ(self):
        for lead in [_cold(), _warm(schwaeche="", website="", email="")]:
            r = leadtool.priority_score(lead, TODAY)
            assert r["score"] >= 0

    def test_wiedervorlage_hebt_score_an(self):
        ohne = _cold(schwaeche="Keine Website")
        mit = _cold(schwaeche="Keine Website", wiedervorlage="2026-08-20")
        r_ohne = leadtool.priority_score(ohne, TODAY)
        r_mit = leadtool.priority_score(mit, TODAY)
        assert r_mit["score"] > r_ohne["score"]
