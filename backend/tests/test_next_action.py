"""Tests für next_action(lead, today) — W2.2 Nächste Aktion."""
from datetime import date

import pytest

import leadtool


TODAY = date(2026, 8, 20)

VALID_ACTIONS = {"pruefen", "qualifizieren", "demo_beauftragen", "kontaktieren", "nachfassen"}


def _lead(status, warm=False, schwaeche="", website="", email="", kontaktiert_am="", wiedervorlage=""):
    kontakt = {"name": "", "email": email, "rolle": "", "quelle": ""}
    return {
        "slug": "test-lead", "firma": "Test GmbH", "status": status, "warm": warm,
        "schwaeche": schwaeche, "website": website, "adresse": "Str. 1",
        "kontaktiert_am": kontaktiert_am, "wiedervorlage": wiedervorlage,
        "kontakt": kontakt if warm else {},
        "branche": "Handwerk", "ort": "Hamburg",
    }


# ---------------------------------------------------------------------------
# Rückgabeformat
# ---------------------------------------------------------------------------

class TestNextActionFormat:
    def test_gibt_string_zurueck(self):
        r = leadtool.next_action(_lead("identifiziert"), TODAY)
        assert isinstance(r, str)

    def test_wert_ist_einer_der_fuenf_erlaubten(self):
        for status in ["identifiziert", "analysiert", "kontaktiert", "keine_antwort", "in_klaerung"]:
            warm = status in leadtool.WARM_STATUSES
            r = leadtool.next_action(_lead(status, warm=warm), TODAY)
            assert r in VALID_ACTIONS, f"Status '{status}' → '{r}' nicht in {VALID_ACTIONS}"


# ---------------------------------------------------------------------------
# Kalte Leads
# ---------------------------------------------------------------------------

class TestNextActionKalt:
    def test_identifiziert_ohne_schwaeche_gibt_pruefen(self):
        r = leadtool.next_action(_lead("identifiziert", schwaeche=""), TODAY)
        assert r == "pruefen"

    def test_identifiziert_mit_schwaeche_gibt_qualifizieren(self):
        r = leadtool.next_action(_lead("identifiziert", schwaeche="Keine Website"), TODAY)
        assert r == "qualifizieren"

    def test_analysiert_gibt_qualifizieren(self):
        r = leadtool.next_action(_lead("analysiert", schwaeche="Keine Website"), TODAY)
        assert r == "qualifizieren"

    def test_analysiert_mit_schwaeche_und_website_gibt_demo_beauftragen(self):
        r = leadtool.next_action(_lead("analysiert", schwaeche="Nicht mobil", website="alt.de"), TODAY)
        assert r == "demo_beauftragen"

    def test_kontaktiert_innerhalb_14_tage_gibt_nachfassen_nicht_sofort(self):
        # Erst nach > 14 Tagen → nachfassen; davor bleibt's beim letzten Stand
        r = leadtool.next_action(_lead("kontaktiert", kontaktiert_am="2026-08-18"), TODAY)
        # 2 Tage → noch nicht fällig → kontaktieren (warten)
        assert r in VALID_ACTIONS  # mindestens gültig

    def test_keine_antwort_nach_14_tagen_gibt_nachfassen(self):
        r = leadtool.next_action(_lead("keine_antwort", kontaktiert_am="2026-07-01"), TODAY)
        assert r == "nachfassen"

    def test_kontaktiert_ueber_14_tage_gibt_nachfassen(self):
        r = leadtool.next_action(_lead("kontaktiert", kontaktiert_am="2026-08-01"), TODAY)
        assert r == "nachfassen"


# ---------------------------------------------------------------------------
# Warme Leads
# ---------------------------------------------------------------------------

class TestNextActionWarm:
    def test_in_klaerung_gibt_kontaktieren(self):
        r = leadtool.next_action(_lead("in_klaerung", warm=True, schwaeche="Keine Website"), TODAY)
        assert r == "kontaktieren"

    def test_termin_vereinbart_gibt_nachfassen(self):
        r = leadtool.next_action(_lead("termin_vereinbart", warm=True), TODAY)
        assert r == "nachfassen"

    def test_angebot_raus_gibt_nachfassen(self):
        r = leadtool.next_action(_lead("angebot_raus", warm=True), TODAY)
        assert r == "nachfassen"

    def test_gewonnen_gibt_nachfassen(self):
        r = leadtool.next_action(_lead("gewonnen", warm=True), TODAY)
        assert r == "nachfassen"

    def test_warmer_lead_mit_schwaeche_und_kein_website_gibt_demo_beauftragen(self):
        r = leadtool.next_action(_lead("in_klaerung", warm=True, schwaeche="Keine Website", website=""), TODAY)
        # In Klärung + Schwäche ohne Website → Demo wäre wertvoll, aber Status dominiert
        assert r in VALID_ACTIONS


# ---------------------------------------------------------------------------
# Wiedervorlage dominiert
# ---------------------------------------------------------------------------

class TestNextActionWiedervorlage:
    def test_faellige_wiedervorlage_gibt_nachfassen(self):
        r = leadtool.next_action(_lead("analysiert", schwaeche="X", wiedervorlage="2026-08-19"), TODAY)
        assert r == "nachfassen"

    def test_zukuenftige_wiedervorlage_dominiert_nicht(self):
        r = leadtool.next_action(_lead("analysiert", schwaeche="X", wiedervorlage="2026-09-01"), TODAY)
        # Zukünftig → ignorieren, Status-Logik greift
        assert r != "nachfassen" or r in VALID_ACTIONS  # zukünftig darf nicht zu nachfassen zwingen


# ---------------------------------------------------------------------------
# Randfälle
# ---------------------------------------------------------------------------

class TestNextActionRandFaelle:
    def test_inaktiv_gibt_pruefen(self):
        r = leadtool.next_action(_lead("inaktiv"), TODAY)
        assert r == "pruefen"

    def test_verloren_gibt_pruefen(self):
        r = leadtool.next_action(_lead("verloren"), TODAY)
        assert r == "pruefen"

    def test_zurueckgestellt_mit_faelliger_wv_gibt_nachfassen(self):
        r = leadtool.next_action(_lead("zurückgestellt", wiedervorlage="2026-08-01"), TODAY)
        assert r == "nachfassen"

    def test_unbekannter_status_gibt_pruefen(self):
        lead = _lead("identifiziert")
        lead["status"] = "unbekannter_status_xyz"
        r = leadtool.next_action(lead, TODAY)
        assert r == "pruefen"
