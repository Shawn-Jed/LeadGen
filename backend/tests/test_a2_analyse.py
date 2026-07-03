# tests/test_a2_analyse.py
import discotool

HTML_MOBILE = """<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Test</title></head>
<body><p>Copyright 2024 Muster GmbH</p>
<a href="/impressum">Impressum</a>
<form action="/kontakt"><input name="email"/><button>Senden</button></form>
</body></html>"""

HTML_LEGACY = """<html><head><title>Old Site</title></head>
<body><p>Alle Rechte vorbehalten &copy; 2009 Altbau GmbH</p>
<p>Kontakt: info@altbau.de</p>
</body></html>"""

HTML_KONTAKT_LINK = """<html><head><title>Kontakt</title></head>
<body><a href="/kontakt">Kontakt aufnehmen</a></body></html>"""

HTML_MINIMAL = """<html><body><p>Hallo Welt</p></body></html>"""


def test_analyse_site_https_detected():
    sig = discotool.analyse_site(HTML_MINIMAL, "https://example.de", jahr=2026)
    assert sig["https"] is True

    sig2 = discotool.analyse_site(HTML_MINIMAL, "http://example.de", jahr=2026)
    assert sig2["https"] is False


def test_analyse_site_viewport_present():
    sig = discotool.analyse_site(HTML_MOBILE, "https://example.de", jahr=2026)
    assert sig["viewport"] is True


def test_analyse_site_viewport_absent():
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["viewport"] is False


def test_analyse_site_copyright_jahr_extracted():
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["copyright_jahr"] == 2009


def test_analyse_site_copyright_jahr_none_when_absent():
    sig = discotool.analyse_site(HTML_MINIMAL, "https://example.de", jahr=2026)
    assert sig["copyright_jahr"] is None


def test_analyse_site_veraltet_old_copyright():
    # 2009 < 2026 - 2 = 2024 → veraltet
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["veraltet"] is True


def test_analyse_site_veraltet_recent_copyright():
    # 2024 == 2026 - 2 → nicht veraltet (grenze: < today_year - 2)
    sig = discotool.analyse_site(HTML_MOBILE, "https://example.de", jahr=2026)
    assert sig["veraltet"] is False


def test_analyse_site_veraltet_false_when_no_copyright():
    sig = discotool.analyse_site(HTML_MINIMAL, "https://example.de", jahr=2026)
    assert sig["veraltet"] is False


def test_analyse_site_impressum_present():
    sig = discotool.analyse_site(HTML_MOBILE, "https://example.de", jahr=2026)
    assert sig["impressum"] is True


def test_analyse_site_impressum_absent():
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["impressum"] is False


def test_analyse_site_kontaktformular_via_form():
    sig = discotool.analyse_site(HTML_MOBILE, "https://example.de", jahr=2026)
    assert sig["kontaktformular"] is True


def test_analyse_site_kontaktformular_via_link():
    sig = discotool.analyse_site(HTML_KONTAKT_LINK, "https://example.de", jahr=2026)
    assert sig["kontaktformular"] is True


def test_analyse_site_kontaktformular_absent():
    sig = discotool.analyse_site(HTML_LEGACY, "http://example.de", jahr=2026)
    assert sig["kontaktformular"] is False


def test_analyse_site_returns_all_keys():
    sig = discotool.analyse_site(HTML_MINIMAL, "https://example.de", jahr=2026)
    assert set(sig.keys()) == {"https", "viewport", "copyright_jahr", "veraltet", "impressum", "kontaktformular"}


# --- score_tier2 ---

def test_score_tier2_all_ok():
    signals = {"https": True, "viewport": True, "veraltet": False,
               "impressum": True, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 0


def test_score_tier2_no_https():
    signals = {"https": False, "viewport": True, "veraltet": False,
               "impressum": True, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 15


def test_score_tier2_no_viewport():
    signals = {"https": True, "viewport": False, "veraltet": False,
               "impressum": True, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 20


def test_score_tier2_veraltet():
    signals = {"https": True, "viewport": True, "veraltet": True,
               "impressum": True, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 15


def test_score_tier2_no_impressum():
    signals = {"https": True, "viewport": True, "veraltet": False,
               "impressum": False, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 10


def test_score_tier2_no_kontakt():
    signals = {"https": True, "viewport": True, "veraltet": False,
               "impressum": True, "kontaktformular": False}
    assert discotool.score_tier2(signals) == 10


def test_score_tier2_all_bad():
    signals = {"https": False, "viewport": False, "veraltet": True,
               "impressum": False, "kontaktformular": False}
    assert discotool.score_tier2(signals) == 70  # 15+20+15+10+10


def test_score_tier2_partial():
    # kein https + kein viewport + kein impressum
    signals = {"https": False, "viewport": False, "veraltet": False,
               "impressum": False, "kontaktformular": True}
    assert discotool.score_tier2(signals) == 45  # 15+20+10
