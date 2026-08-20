# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primärer Nutzer der Demo ist die **Inhaberin/der Inhaber (bzw. Entscheider) eines kleinen,
lokalen Hamburger Betriebs** mit schwachem oder veraltetem Webauftritt — im aktuellen Pilot
ambulante Pflegedienste und Senioren-/Pflegeheime in Winterhude/Barmbek. Sie/er bekommt eine
unaufgeforderte, individuell gebaute Demo einer verbesserten Version des **eigenen** Auftritts
zu sehen und soll erkennen: „So könnte meine Seite aussehen."

Sekundär bildet die Demo die **Endkunden des Betriebs** ab (im Pilot: pflegende Angehörige,
die einen vertrauenswürdigen Dienst suchen) — denn nur eine für diese Zielgruppe überzeugende
Seite überzeugt auch den Inhaber vom geschäftlichen Mehrwert.

## Product Purpose

Pro Lead ein maßgeschneiderter **Akquise-Demo-One-Pager**: eine glaubwürdig verbesserte
Fassung des Webauftritts des konkreten Betriebs, die dessen dokumentierte Schwäche adressiert.
Zweck ist die Kaltakquise von **Festpreis-Webprojekten**. **Erfolg = der Inhaber erkennt die
Aufwertung und meldet sich (Anruf / Rückruf).** Die Demo ist das Verkaufsargument, nicht ein
fertiges Kundenprodukt.

## Positioning

Kein Template und kein Baukasten: **jede Demo wird einzeln aus verifizierten, öffentlichen
Fakten** über genau diesen Betrieb gebaut und adressiert dessen konkrete, belegte Schwäche.
Ein generischer Landing-Page-Generator könnte das nicht wahrheitsgetreu nachbilden. Keine
Massenproduktion — Qualität und Faktenbindung vor Menge.

## Operating Context

Teil des LeadGen-Funnels (Discovery → CRM → **Prototyp** → Outreach → Portfolio). Die Demo
entsteht aus dem CRM-Kontext eines Leads plus einem faktengebundenen Brief
(`docs/superpowers/briefs/<slug>-brief.md`), wird als **eine self-contained HTML-Datei**
gebaut, **lokal geprüft** und erst nach **ausdrücklicher menschlicher Einzelfreigabe** auf
GitHub Pages veröffentlicht; der Link speist dann den Outreach. Demo-Lebenszyklus:
`none → pending → draft_ready → approved_local → published` (+ `rework`/`archived`).

## Capabilities and Constraints

- **Eine self-contained HTML-Datei je Demo**: HTML + CSS (+ ggf. JS) inline, **keine externen
  CDN/Fonts/Skripte/Bilder** — muss offline und unter GitHub Pages ohne Netzabhängigkeit laufen.
  Distinctive Wirkung über web-safe/eingebettete Fonts, inline-SVG, CSS-Gradients/Noise.
- **Responsive/mobil**, nutzbar ab 375 px Breite.
- **Faktenbindung ist Pflicht**: nur belegte Fakten; alles Unbelegte (Fotos, Preise,
  Bewertungen, Zertifikate, Kundenstimmen) erscheint als **klar markierter Platzhalter** und
  wird nie erfunden.
- Sprache **Deutsch**. Die Demo trägt den **echten Firmennamen** des Betriebs.
- Genau **eine CTA** pro Demo (im Pilot: telefonischer Rückruf-/Kontaktweg).

## Brand Commitments

Die Demo übernimmt die **Identität des jeweiligen Betriebs**, nicht die von Shawn/LeadGen —
kein aufgezwungenes eigenes Branding. Tonalität: seriös, klar, vertrauenswürdig, schlichtes
Deutsch. Rechtliche Verantwortung für den Einsatz pro Lead liegt bei Shawn (die Demo wird
öffentlich unter seiner Pages-URL sichtbar).

## Evidence on Hand

Fakten je Lead stammen aus Discovery (OSM/Tier-2) + WebSearch-Gegencheck und liegen in den
CRM-Notizen sowie im jeweiligen Brief. Beispiel-Pilot: `ambulanter-betreuungsdienst` (Düwel) —
Brief unter `docs/superpowers/briefs/ambulanter-betreuungsdienst-brief.md` (u. a. Pflegenote
1,2, 24h-Erreichbarkeit, seit 1993, Leistungsspektrum). **Nicht vorhanden und nicht zu
erfinden:** echte Fotos, Kundenstimmen, exakte Preise → als Platzhalter kennzeichnen.

## Product Principles

1. **Fakten vor Fülle** — nur Belegtes; Unbelegtes wird markierter Platzhalter, nie Behauptung.
2. **Vertrauen ist das Produkt** — Seriosität und Lesbarkeit für die Zielgruppe schlagen
   Effekthascherei.
3. **Individuell, nie Vorlage** — jede Demo entsteht aus dem konkreten Betrieb heraus.
4. **Self-contained by default** — läuft offline und auf Pages, keine externen Abhängigkeiten.
5. **Mensch entscheidet die Außenwirkung** — kein Publish/Versand ohne Einzelfreigabe.

## Accessibility & Inclusion

Zielgruppe altersgeprägt (Pflege/Senioren-Umfeld): **große Schrift (≥17 px), hoher Kontrast**,
klar erkennbare Tap-/Klickziele, semantische Struktur, gut lesbare Zeilenlängen.
