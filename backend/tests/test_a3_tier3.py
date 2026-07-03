import pytest
from datetime import date
import discotool


def _make_run() -> dict:
    """Minimal run mit 3 Kandidaten: 2 analysiert (unterschiedliche Scores), 1 website_unklar."""
    cands = [
        {"firma": "Alpha GmbH",   "website": "https://alpha.de",  "adresse": "", "telefon": "", "osm_id": "node/1"},
        {"firma": "Beta KG",      "website": "https://beta.de",   "adresse": "", "telefon": "", "osm_id": "node/2"},
        {"firma": "Gamma e.K.",   "website": "",                  "adresse": "", "telefon": "", "osm_id": "node/3"},
    ]
    run = discotool.new_run("Zahnärzte", "Eimsbüttel", cands, date(2026, 6, 28))
    # Alpha: analysiert, Score 25
    run["kandidaten"][0]["status"] = "analysiert"
    run["kandidaten"][0]["score"]  = 25
    # Beta: analysiert, Score 70
    run["kandidaten"][1]["status"] = "analysiert"
    run["kandidaten"][1]["score"]  = 70
    # Gamma bleibt website_unklar (Score 60 from tier1)
    return run


# --- set_tier3 ---

def test_set_tier3_stores_dict():
    run = _make_run()
    discotool.set_tier3(run, 1, urteil="Veraltetes Design, kein Responsive", empfehlung="lohnt")
    assert run["kandidaten"][0]["tier3"] == {
        "urteil": "Veraltetes Design, kein Responsive",
        "empfehlung": "lohnt",
    }


def test_set_tier3_all_valid_empfehlungen():
    for emp in ("lohnt", "lohnt_nicht", "unklar"):
        run = _make_run()
        discotool.set_tier3(run, 1, urteil="x", empfehlung=emp)
        assert run["kandidaten"][0]["tier3"]["empfehlung"] == emp


def test_set_tier3_invalid_empfehlung_raises():
    run = _make_run()
    with pytest.raises(ValueError, match="empfehlung"):
        discotool.set_tier3(run, 1, urteil="x", empfehlung="gut")


def test_set_tier3_unknown_id_raises():
    run = _make_run()
    with pytest.raises(ValueError, match="99"):
        discotool.set_tier3(run, 99, urteil="x", empfehlung="lohnt")


def test_set_tier3_does_not_touch_score():
    run = _make_run()
    score_before = run["kandidaten"][0]["score"]
    discotool.set_tier3(run, 1, urteil="schöne Seite", empfehlung="lohnt_nicht")
    assert run["kandidaten"][0]["score"] == score_before


def test_set_tier3_does_not_touch_tier2():
    run = _make_run()
    run["kandidaten"][0]["tier2"] = {"kein_https": True}
    discotool.set_tier3(run, 1, urteil="x", empfehlung="unklar")
    assert run["kandidaten"][0]["tier2"] == {"kein_https": True}


# --- shortlist ---

def test_shortlist_returns_only_analysiert():
    run = _make_run()
    sl = discotool.shortlist(run)
    firmen = [c["firma"] for c in sl]
    assert "Gamma e.K." not in firmen   # website_unklar → ausgeschlossen
    assert "Alpha GmbH" in firmen
    assert "Beta KG" in firmen


def test_shortlist_sorted_by_score_desc():
    run = _make_run()
    sl = discotool.shortlist(run)
    scores = [c["score"] for c in sl]
    assert scores == sorted(scores, reverse=True)


def test_shortlist_top_cap():
    """top=1 → nur der Kandidat mit höchstem Score."""
    run = _make_run()
    sl = discotool.shortlist(run, top=1)
    assert len(sl) == 1
    assert sl[0]["firma"] == "Beta KG"   # Score 70 > 25


def test_shortlist_default_top_ten():
    """Mit < 10 analysierten Kandidaten: alle zurückgegeben."""
    run = _make_run()
    sl = discotool.shortlist(run)
    assert len(sl) == 2   # nur 2 analysiert


def test_shortlist_empty_when_none_analysiert():
    cands = [{"firma": "Nur Unklar", "website": "", "adresse": "", "telefon": "", "osm_id": ""}]
    run = discotool.new_run("X", None, cands, date(2026, 6, 28))
    assert discotool.shortlist(run) == []
