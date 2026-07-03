"""Config-Loader (stdlib): liest .env in os.environ, liefert SMTP-Config + Sendemodus."""
from __future__ import annotations

import os
from pathlib import Path


def load_env(root: Path) -> None:
    """Lädt KEY=VALUE-Zeilen aus root/.env nach os.environ (setdefault). Fehlt die Datei: no-op."""
    env = root / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def smtp_config() -> dict:
    user = os.environ.get("SMTP_USER", "")
    return {
        "host": os.environ.get("SMTP_HOST", ""),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": user,
        "password": os.environ.get("SMTP_PASS", ""),
        "from_addr": os.environ.get("SMTP_FROM", user),
    }


def send_mode() -> str:
    return os.environ.get("OUTREACH_SEND_MODE", "draft").lower()
