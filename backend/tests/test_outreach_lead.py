import datetime

import leadtool
import pytest

TODAY = datetime.date(2026, 7, 3)


def _warm(repo):
    """Legt einen warmen Lead an und gibt seinen slug zurück."""
    slug = leadtool.add_lead(repo, "Test Betrieb", schwaeche="veraltet", today=TODAY)
    leadtool.set_status(repo, slug, "in_klaerung", today=TODAY)  # graduiert -> leads/<slug>.md
    return slug


def test_set_email_warm(repo):
    slug = _warm(repo)
    leadtool.set_email(repo, slug, "info@betrieb.de")
    meta, _ = leadtool.read_lead(repo, slug)
    assert meta["kontakt"]["email"] == "info@betrieb.de"


def test_set_email_cold_raises(repo):
    slug = leadtool.add_lead(repo, "Kalt GmbH", schwaeche="x", today=TODAY)  # bleibt kalt
    with pytest.raises(ValueError):
        leadtool.set_email(repo, slug, "x@y.de")


def test_mark_contacted_stamps_and_logs(repo):
    slug = _warm(repo)
    leadtool.mark_contacted(repo, slug, betreff="Ihr Web-Auftritt", today=TODAY)
    meta, body = leadtool.read_lead(repo, slug)
    assert meta["kontaktiert_am"] == "2026-07-03"
    assert meta["status"] == "in_klaerung"  # KEIN Downgrade auf kontaktiert
    assert "2026-07-03: Mail gesendet — Ihr Web-Auftritt" in body
