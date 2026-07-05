"""Mail-Erzeugung + Versand. Versand ist injizierbar (smtp_factory) für Tests.

Modi:
- "direct": echter SMTP-Versand (STARTTLS + Login, falls user gesetzt).
- "draft" : Nachricht als .eml-Datei ablegen (kein Netz).
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path


def build_message(*, from_addr: str, to_addr: str, subject: str, body: str,
                  attachment: dict | None = None) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    if attachment is not None:
        msg.add_attachment(
            attachment["data"],
            maintype=attachment.get("maintype", "application"),
            subtype=attachment.get("subtype", "octet-stream"),
            filename=attachment["filename"],
        )
    return msg


def send_smtp(msg: EmailMessage, cfg: dict, *, smtp_factory=None) -> None:
    factory = smtp_factory or (lambda: smtplib.SMTP(cfg["host"], cfg["port"]))
    with factory() as server:
        server.starttls()
        if cfg.get("user"):
            server.login(cfg["user"], cfg["password"])
        server.send_message(msg)


def save_eml(msg: EmailMessage, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(msg))
    return path


def deliver(msg: EmailMessage, *, mode: str, cfg: dict, eml_path: Path,
            smtp_factory=None) -> dict:
    if mode == "direct":
        send_smtp(msg, cfg, smtp_factory=smtp_factory)
        return {"mode": "direct"}
    save_eml(msg, eml_path)
    return {"mode": "draft", "eml": str(eml_path)}
