"""Prototyp-Deploy: schreibt One-Pager-HTML ins Pages-Repo und pusht.

Der Push ist injizierbar (pusher) für Tests — analog mailer.smtp_factory.
Default-Pusher ruft git über subprocess auf (kein Netz im Test, weil injiziert).
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _default_pusher(repo_path: Path, slug: str) -> None:
    rel = f"{slug}/index.html"
    subprocess.run(["git", "-C", str(repo_path), "add", rel], check=True)
    subprocess.run(["git", "-C", str(repo_path), "commit", "-m", f"prototyp: {slug}"], check=True)
    subprocess.run(["git", "-C", str(repo_path), "push"], check=True)


def deploy(slug: str, html: str, *, repo_path: Path, pages_base: str, pusher=None) -> str:
    """Schreibt <repo_path>/<slug>/index.html, pusht (injizierbar) und gibt die Pages-URL zurück."""
    repo_path = Path(repo_path)
    target = repo_path / slug / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    (pusher or _default_pusher)(repo_path, slug)
    return f"{pages_base.rstrip('/')}/{slug}"
