"""CLI für Lead-Discovery (Tier 1). Bedient discotool gegen das aktuelle Verzeichnis."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import discotool


def _today(args) -> date:
    return date.fromisoformat(args.today) if args.today else date.today()


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    p = argparse.ArgumentParser(prog="discover", description="Lead-Discovery Hamburg (Tier 1)")
    p.add_argument("--today", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("scan", help="Branche+Stadtteil scannen")
    ps.add_argument("branche")
    ps.add_argument("stadtteil", nargs="?", default=None)
    ps.add_argument("--today", default=None)

    psh = sub.add_parser("show", help="Run-Datei anzeigen")
    psh.add_argument("run")
    psh.add_argument("--today", default=None)

    pst = sub.add_parser("setstatus", help="Kandidaten-Status setzen")
    pst.add_argument("run")
    pst.add_argument("id", type=int)
    pst.add_argument("status")
    pst.add_argument("url", nargs="?", default="")
    pst.add_argument("--today", default=None)

    pu = sub.add_parser("uebernehmen", help="Funde als Leads anlegen (ids|auto)")
    pu.add_argument("run")
    pu.add_argument("ids")
    pu.add_argument("--today", default=None)

    pa = sub.add_parser("analyse", help="Tier-2-HTML-Analyse für hat_website-Kandidaten")
    pa.add_argument("run")
    pa.add_argument("--today", default=None)

    psl = sub.add_parser("shortlist", help="Top-N analysierte Kandidaten für Tier-3-Bewertung")
    psl.add_argument("run")
    psl.add_argument("--top", type=int, default=10)
    psl.add_argument("--today", default=None)

    pbw = sub.add_parser("bewerten", help="Tier-3-Urteil per Playwright eintragen")
    pbw.add_argument("run")
    pbw.add_argument("id", type=int)
    pbw.add_argument("empfehlung", choices=["lohnt", "lohnt_nicht", "unklar"])
    pbw.add_argument("urteil")
    pbw.add_argument("--today", default=None)

    try:
        args = p.parse_args(argv)
    except SystemExit:
        return 1
    root = Path(".")

    try:
        if args.cmd == "scan":
            tags = discotool.branche_to_tags(args.branche)
            query = discotool.build_overpass_query(tags, args.stadtteil)
            data = discotool.fetch_overpass(query)
            cands = discotool.parse_elements(data)
            run = discotool.new_run(args.branche, args.stadtteil, cands, _today(args))
            path = discotool.run_path(root, args.branche, args.stadtteil, _today(args))
            discotool.save_run(path, run)
            unklar = sum(1 for c in run["kandidaten"] if c["status"] == "website_unklar")
            print(f"Scan: {len(cands)} Kandidaten → {path}")
            print(f"  davon {unklar} ohne website-Tag (website_unklar → per WebSearch prüfen)")
        elif args.cmd == "show":
            _print_run(discotool.load_run(Path(args.run)))
        elif args.cmd == "setstatus":
            run = discotool.load_run(Path(args.run))
            discotool.set_status(run, args.id, args.status, args.url)
            discotool.save_run(Path(args.run), run)
            print(f"id {args.id} → {args.status}")
        elif args.cmd == "uebernehmen":
            path = Path(args.run)
            run = discotool.load_run(path)
            which = "auto" if args.ids == "auto" else [int(x) for x in args.ids.split(",")]
            res = discotool.create_leads(root, run, which, _today(args))
            discotool.save_run(path, run)
            print(f"Leads angelegt: {len(res['angelegt'])} {res['angelegt']}")
            if res["uebersprungen"]:
                print(f"Übersprungen (Duplikat): {res['uebersprungen']}")
        elif args.cmd == "analyse":
            from datetime import date as _date
            path = Path(args.run)
            run = discotool.load_run(path)
            today_val = _today(args)
            summary = discotool.analyse_run(root, run, jahr=today_val.year)
            discotool.save_run(path, run)
            print(f"Analyse: {summary['analysiert']} Kandidaten analysiert.")
            if summary["fehler"]:
                print(f"  Fehler ({len(summary['fehler'])}):")
                for f in summary["fehler"]:
                    print(f"    {f}")
        elif args.cmd == "shortlist":
            run = discotool.load_run(Path(args.run))
            sl = discotool.shortlist(run, top=args.top)
            if not sl:
                print("Keine analysierten Kandidaten in diesem Run.")
            else:
                print(f"Shortlist ({len(sl)} Kandidaten, sortiert nach Score desc):")
                for c in sl:
                    url = c.get("gefundene_url") or c.get("website") or "—"
                    t3 = "✓bewertet" if "tier3" in c else ""
                    print(f"  [{c['id']}] {c['firma']}  Score={c['score']}  {url}  {t3}")
        elif args.cmd == "bewerten":
            path = Path(args.run)
            run = discotool.load_run(path)
            discotool.set_tier3(run, args.id, urteil=args.urteil, empfehlung=args.empfehlung)
            discotool.save_run(path, run)
            cand = next(c for c in run["kandidaten"] if c["id"] == args.id)
            print(f"Tier-3 gespeichert: [{args.id}] {cand['firma']} → {args.empfehlung}")
    except (ValueError, FileNotFoundError) as e:
        print(f"Fehler: {e}")
        return 1
    return 0


def _print_run(run: dict) -> None:
    print(f"Run: {run['branche']} / {run['stadtteil']} ({run['erstellt']})")
    for c in run["kandidaten"]:
        mark = "✓Lead" if c["lead_angelegt"] else ""
        print(f"  [{c['id']}] {c['firma']} — {c['status']} (Score {c['score']}) {c['adresse']} {mark}")


if __name__ == "__main__":
    raise SystemExit(main())
