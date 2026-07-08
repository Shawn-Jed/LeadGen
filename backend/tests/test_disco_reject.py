from datetime import date

import discotool
import pytest


def _run():
    cands = [
        {"firma": "Alpha", "adresse": "Weg 1", "website": ""},
        {"firma": "Beta", "adresse": "Weg 2", "website": "https://beta.de"},
    ]
    return discotool.new_run("friseur", "Ottensen", cands, date(2026, 7, 8))


def test_reject_sets_status_and_stashes_previous():
    run = _run()
    vorher = run["kandidaten"][0]["status"]        # website_unklar (keine Website)
    discotool.reject(run, 1)
    c = run["kandidaten"][0]
    assert c["status"] == "abgelehnt"
    assert c["status_vor_ablehnung"] == vorher


def test_restore_reverts_to_previous_status():
    run = _run()
    vorher = run["kandidaten"][1]["status"]        # hat_website
    discotool.reject(run, 2)
    discotool.restore(run, 2)
    c = run["kandidaten"][1]
    assert c["status"] == vorher
    assert "status_vor_ablehnung" not in c


def test_double_reject_keeps_original_previous_status():
    run = _run()
    vorher = run["kandidaten"][0]["status"]
    discotool.reject(run, 1)
    discotool.reject(run, 1)                        # zweites Mal darf Stash nicht überschreiben
    assert run["kandidaten"][0]["status_vor_ablehnung"] == vorher


def test_restore_without_stash_falls_back_to_neu():
    run = _run()
    run["kandidaten"][0]["status"] = "abgelehnt"    # ohne status_vor_ablehnung (z.B. Altbestand)
    discotool.restore(run, 1)
    assert run["kandidaten"][0]["status"] == "neu"


def test_reject_unknown_id_raises():
    run = _run()
    with pytest.raises(ValueError):
        discotool.reject(run, 999)


def test_auto_uebernehmen_skips_rejected_candidate(repo):
    run = _run()
    # Alpha (id=1) ist 'keine_website'? Nein — new_run setzt website_unklar bei fehlender Website.
    # Für den auto-Pfad brauchen wir Status keine_website; setzen wir explizit.
    run["kandidaten"][0]["status"] = "keine_website"
    discotool.reject(run, 1)                        # abgelehnt → darf nicht auto-übernommen werden
    res = discotool.create_leads(repo, run, "auto", date(2026, 7, 8))
    assert res["angelegt"] == []
    assert run["kandidaten"][0]["lead_angelegt"] is False
