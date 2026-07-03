import discotool
from datetime import date


def test_score_tier1():
    assert discotool.score_tier1({"website": ""}) == 60
    assert discotool.score_tier1({"website": "https://x.de"}) == 0


def test_new_run_assigns_ids_and_status():
    cands = [{"firma": "Mit Web", "website": "https://x.de", "adresse": "", "telefon": "", "osm_id": "node/1"},
             {"firma": "Ohne Web", "website": "", "adresse": "", "telefon": "", "osm_id": "node/2"}]
    run = discotool.new_run("Zahnärzte", "Eimsbüttel", cands, date(2026, 6, 28))
    assert run["branche"] == "Zahnärzte" and run["stadtteil"] == "Eimsbüttel"
    assert run["kandidaten"][0]["status"] == "hat_website"
    assert run["kandidaten"][1]["status"] == "website_unklar"
    assert run["kandidaten"][1]["score"] == 60
    assert run["kandidaten"][0]["id"] == 1 and run["kandidaten"][1]["id"] == 2


def test_run_save_load_roundtrip(tmp_path):
    run = discotool.new_run("Friseure", None, [], date(2026, 6, 28))
    path = discotool.run_path(tmp_path, "Friseure", None, date(2026, 6, 28))
    discotool.save_run(path, run)
    assert path.exists()
    assert discotool.load_run(path) == run


def test_set_status_updates_and_validates():
    run = discotool.new_run("X", None, [{"firma": "A", "website": "", "adresse": "", "telefon": "", "osm_id": ""}], date(2026, 6, 28))
    discotool.set_status(run, 1, "keine_website")
    assert run["kandidaten"][0]["status"] == "keine_website"
    discotool.set_status(run, 1, "hat_website", "https://found.de")
    assert run["kandidaten"][0]["gefundene_url"] == "https://found.de"
    try:
        discotool.set_status(run, 1, "quatsch")
        assert False
    except ValueError:
        pass
    try:
        discotool.set_status(run, 99, "keine_website")
        assert False
    except ValueError:
        pass
