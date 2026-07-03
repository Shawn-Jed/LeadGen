"""CLI für das Lead-CRM. Bedient leadtool gegen das aktuelle Verzeichnis (root=.)."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import leadtool


def _today(args) -> date:
    return date.fromisoformat(args.today) if args.today else date.today()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="lead", description="Lead-Tracking-CRM")
    p.add_argument("--today", help="ISO-Datum überschreiben (Tests/Debug)", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Repo-Dateien anlegen")
    p_init.add_argument("--today", help=argparse.SUPPRESS, default=None)

    p_neu = sub.add_parser("neu", help="Lead anlegen")
    p_neu.add_argument("firma")
    p_neu.add_argument("--schwaeche", default="")
    p_neu.add_argument("--today", help=argparse.SUPPRESS, default=None)

    p_st = sub.add_parser("status", help="Status setzen (graduiert bei warm)")
    p_st.add_argument("slug")
    p_st.add_argument("status")
    p_st.add_argument("--today", help=argparse.SUPPRESS, default=None)

    p_no = sub.add_parser("notiz", help="Notiz anhängen")
    p_no.add_argument("slug")
    p_no.add_argument("text")
    p_no.add_argument("--today", help=argparse.SUPPRESS, default=None)

    p_rep = sub.add_parser("report", help="Fällige Wiedervorlagen + überfällige Kontakte")
    p_rep.add_argument("--today", help=argparse.SUPPRESS, default=None)

    p_wv = sub.add_parser("wiedervorlage", help="Wiedervorlage-Datum setzen (YYYY-MM-DD)")
    p_wv.add_argument("slug")
    p_wv.add_argument("datum")
    p_wv.add_argument("--today", help=argparse.SUPPRESS, default=None)

    args = p.parse_args(argv)
    root = Path(".")

    try:
        if args.cmd == "init":
            leadtool.init_repo(root)
            print("Repo initialisiert.")
        elif args.cmd == "neu":
            slug = leadtool.add_lead(root, args.firma, schwaeche=args.schwaeche, today=_today(args))
            print(f"Lead angelegt: {slug}")
        elif args.cmd == "status":
            leadtool.set_status(root, args.slug, args.status, today=_today(args))
            print(f"{args.slug} → {args.status}")
        elif args.cmd == "notiz":
            leadtool.add_note(root, args.slug, args.text, today=_today(args))
            print(f"Notiz an {args.slug} angehängt.")
        elif args.cmd == "report":
            _print_report(leadtool.report(root, today=_today(args)))
        elif args.cmd == "wiedervorlage":
            leadtool.set_wiedervorlage(root, args.slug, args.datum)
            print(f"Wiedervorlage für {args.slug}: {args.datum}")
    except (ValueError, FileNotFoundError) as e:
        print(f"Fehler: {e}")
        return 1
    return 0


def _print_report(rep: dict) -> None:
    print("=== Fällige Wiedervorlagen ===")
    for c in rep["wiedervorlage_faellig"]:
        print(f"  [{c['slug']}] {c['firma']} — Wiedervorlage {c['wiedervorlage']} (Status {c['status']})")
    if not rep["wiedervorlage_faellig"]:
        print("  keine")
    print("=== >14 Tage keine Antwort (→ Status 'keine_antwort' erwägen) ===")
    for c in rep["keine_antwort"]:
        print(f"  [{c['slug']}] {c['firma']} — kontaktiert {c['kontaktiert_am']} ({c['tage']} Tage her)")
    if not rep["keine_antwort"]:
        print("  keine")


if __name__ == "__main__":
    raise SystemExit(main())
