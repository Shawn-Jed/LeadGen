# Entwurfsvertrag — Ambulanter Betreuungsdienst Angelika Düwel

**Lead-Slug:** `ambulanter-betreuungsdienst`
**Brief-Datum:** 2026-08-20
**Autor:** prototype-art-director
**Status:** bereit für HTML-Umsetzung

---

## 1. Nachweisbare Fakten

Alle Angaben in diesem Abschnitt sind durch öffentlich zugängliche Quellen belegt.
Quelle wird je Aussage angegeben. Nichts darf ohne Quellenangabe als Fakt dargestellt werden.

| Aussage | Quelle |
|---|---|
| Firmenname: Ambulanter Betreuungsdienst Angelika Düwel | hamburg.de-Branchenbuch, pflegesuche.de |
| Adresse: Krohnskamp 13, 22301 Hamburg-Winterhude | hamburg.de-Branchenbuch |
| Telefon: 040 519246 | hamburg.de-Branchenbuch, pflegesuche.de |
| Fax: 040 51310221 | hamburg.de-Branchenbuch |
| Website (Bestand): www.ambulanter-pflegedienst-duewel.de | Direktaufruf 2026-08-20 |
| Gegründet 1993 von Angelika Düwel | pflegesuche.de, pflegefinder.bkk-dachverband.de |
| Inhaberin ist examinierte Altenpflegerin | pflegesuche.de |
| Leistungen: Grundpflege | pflegesuche.de, pflegefinder.bkk-dachverband.de |
| Leistungen: Behandlungspflege | pflegesuche.de, pflegefinder.bkk-dachverband.de |
| Leistungen: Hauswirtschaftliche Versorgung | pflegesuche.de, pflegefinder.bkk-dachverband.de |
| Leistungen: Freizeit & Service | pflegesuche.de |
| Leistungen: Beratung Angehöriger | pflegesuche.de |
| Leistungen: Unterstützung bei Finanzierung | pflegesuche.de |
| Leistungen: Wahl einer vertrauten Pflegeperson | pflegesuche.de |
| Leistungen: Persönliche Beratung | pflegesuche.de |
| 24-Stunden-Erreichbarkeit | pflegesuche.de |
| Leitmotiv: Fürsorge, Hilfe zur Selbsthilfe, so lange wie möglich im gewohnten Umfeld bleiben | pflegesuche.de |
| Ca. 52 Kunden | pflegefinder.bkk-dachverband.de |
| Einsatzgebiet: ca. 6 km um Winterhude | pflegefinder.bkk-dachverband.de |
| Pflegenote: 1,2 (sehr gut) | pflegefinder.bkk-dachverband.de |
| Institutionskennzeichen: 460204404 | pflegefinder.bkk-dachverband.de |

---

## 2. Platzhalter — explizit als solche markiert

Die folgenden Elemente sind **nicht belegt** und dürfen im HTML **nicht als Fakten** erscheinen.
Sie werden im Entwurf als sichtbare Platzhalter dargestellt (z.B. `[FOTO: Team]`, `[ZITAT: Kundin]`).

| Platzhalter | Warum Platzhalter |
|---|---|
| `[FOTO: Angelika Düwel / Team]` | Kein öffentlich lizensiertes Bild vorhanden |
| `[FOTO: Pflege-Situation / Hero-Bild]` | Kein eigenes Bildmaterial vorhanden |
| `[ZITAT: Kundin / pflegender Angehöriger]` | Keine verifizierten Kundenstimmen vorliegen |
| `[ÖFFNUNGSZEITEN: Büro]` | Nicht aus öffentlichen Quellen belegbar |
| `[E-MAIL-ADRESSE]` | Nicht aus öffentlichen Quellen belegbar |
| `[PREISE / STUNDENSÄTZE]` | Nicht aus öffentlichen Quellen belegbar; je nach Pflegegrad individuell |
| `[ZERTIFIKATE / MITGLIEDSCHAFTEN]` | Keine belegt |
| `[ANZAHL MITARBEITER]` | Nicht belegt (nur Kundenzahl 52 ist belegt) |

---

## 3. Schwäche des Ist-Auftritts

- **SSL/TLS-Fehler:** Die Domain `www.ambulanter-pflegedienst-duewel.de` ist nur über veraltetes TLS erreichbar. Moderne Browser (Chrome, Firefox, Safari) blockieren den Aufruf oder zeigen eine Sicherheitswarnung. Für die Zielgruppe (oft weniger technisch versierte Angehörige) ist das ein faktischer Zugangssperr.
- **Mutmaßlich nicht mobil-optimiert:** Anhand des Alters des Auftritts und der TLS-Situation ist ein responsives Layout nicht zu erwarten. Nicht direkt verifiziert (Browser-Blockade verhindert Inspektion) — daher als "mutmaßlich" zu kennzeichnen.
- **Veraltete Gestaltung:** Optisch entspricht der Auftritt nicht dem Vertrauensanspruch eines Pflegedienstes (Stand: ca. 2000er-Jahre-Design).

**Praktische Wirkung auf die Zielgruppe:** Eine pflegende Tochter oder ein pflegender Sohn, der in Hamburg nach kurzfristiger Pflege für ein Elternteil sucht, öffnet die Website auf dem Smartphone — und landet entweder auf einer Sicherheitswarnung oder einem unlesbaren Desktop-Layout. Das Vertrauen ist weg, bevor ein einziges Wort gelesen wurde.

---

## 4. Zielgruppe

**Primär:** Pflegende Angehörige in Winterhude und den angrenzenden Stadtteilen (Eppendorf, Barmbek-Nord, Uhlenhorst), die für ein Familienmitglied kurzfristig oder dauerhaft einen ambulanten Pflegedienst suchen. Entscheidung oft unter emotionalem Druck, häufig auf dem Smartphone.

**Sekundär:** Die Pflegebedürftigen selbst (wenn noch selbstständig in Entscheidungen), ca. 65+ Jahre, mit Bedarf an sehr gut lesbarer Darstellung.

**Implizit:** Zuweisende Krankenhäuser, Sozialstationen und Ärzte in Winterhude — die nach einer schnellen, seriösen Kontaktmöglichkeit suchen.

---

## 5. CTA — genau eine

**Rückruf anfragen via Telefon:**
> "Jetzt anrufen: 040 519246"

Begründung: Die 24-Stunden-Erreichbarkeit ist belegt. Telefon ist für die Zielgruppe der direkteste Kanal. Ein Formular würde einen nicht belegten E-Mail-Kanal voraussetzen. Kein zweiter CTA (kein "Termin buchen online", kein "Kontaktformular").

Der CTA erscheint prominent im Hero-Bereich und wiederholt sich einmalig im Kontakt-Abschnitt am Ende.

---

## 6. Erlaubte Module

Die folgenden Seitenabschnitte sind aus den belegten Fakten vollständig befüllbar oder mit klar ausgewiesenen Platzhaltern sauber darstellbar.

| Modul | Inhalt (belegbar) | Platzhalter im Modul |
|---|---|---|
| **Hero** | Name, Standort Winterhude, Leitmotiv ("so lange wie möglich im gewohnten Umfeld bleiben"), CTA Telefon | `[FOTO: Pflege-Situation]` als Hintergrundbild |
| **Leistungen** | 8 belegte Leistungen als Kachelraster | — |
| **Vertrauen / Pflegenote** | "Pflegenote 1,2 — sehr gut" + Institutionskennzeichen 460204404 | — |
| **Über uns / Seit 1993** | Gründungsjahr, Gründerin Angelika Düwel, examinierte Altenpflegerin, ca. 52 Kunden, Einsatzgebiet 6 km um Winterhude | `[FOTO: Angelika Düwel / Team]`, `[ZITAT: Kundin]` |
| **Kontakt / Anfahrt** | Krohnskamp 13, 22301 Hamburg-Winterhude, Tel. 040 519246, Fax 040 51310221, 24h-Erreichbarkeit, eingebettete Karte (OpenStreetMap oder statische Google-Maps-Verlinkung) | `[ÖFFNUNGSZEITEN]`, `[E-MAIL]` |

Modulreihenfolge auf der Seite: Hero → Leistungen → Vertrauen/Note → Über uns → Kontakt/Anfahrt.

---

## 7. Visuelle Richtung

**Ton:** Warm, persönlich, bodenständig. Kein steriler Klinik-Stil. Kein übertrieben modernes Startup-Design. Signalisiert: "Wir sind schon lange hier, wir kennen uns aus, ruf uns an."

**Farbwelt:**
- Primär: Warmes Grün (z.B. #3d7a5f oder ähnlich) — assoziiert mit Natur, Fürsorge, Gesundheit
- Sekundär: Cremeweiß / Hellbeige als Hintergrund — nicht kalt, nicht klinisch
- Akzent/CTA: Kräftiges Dunkelgrün oder ruhiges Terrakotta für den Telefon-Button — hoher Kontrast, sicher erfüllt WCAG AA
- Keine grellen Farben, kein Blau-Weiß-Klinikmuster

**Typografie:**
- Lauftext: mindestens 17px (Zielgruppe 65+), Zeilenhöhe 1,65
- Überschriften: serifenlos, klar (z.B. System-Stack oder Google Fonts — keine verspielten Schriften)
- Kein Text über Foto ohne ausreichenden Kontrast-Overlay

**Bildlogik:**
- Hero: Platzhalter mit sichtbarem Hinweis `[FOTO erforderlich: Pflege-Situation, lizenzfrei]`
- Über uns: Platzhalter mit sichtbarem Hinweis `[FOTO erforderlich: Angelika Düwel oder Team]`
- Keine Stock-Fotos aus anderen Quellen einbauen — Platzhalter sind besser als fremde Bilder

**Qualitätslatte:** Orientierung an professionellen Hamburger Pflegedienst-Websites (z.B. Pflege-Netz Hamburg) — als Inspirationsquelle für Lesbarkeit und Vertrauen, nicht als Copy-Vorlage.

---

## 8. Nicht erlaubte Behauptungen

Das Folgende darf im HTML **unter keinen Umständen** erscheinen, da kein Beleg vorliegt:

- Erfundene oder geschätzte Preise / Stundensätze
- Bewertungen außer der belegten Pflegenote 1,2 (keine erfundenen Google-Sterne, keine Testimonials ohne Quelle)
- Zertifikate, Auszeichnungen oder Mitgliedschaften ohne Beleg
- Konkrete Mitarbeiterzahl (nur "kleines, erfahrenes Team" wäre als nicht-quantifizierte Aussage tolerierbar)
- Aussagen über Reaktionszeiten (z.B. "innerhalb 24 Stunden") außer der belegten 24h-Rufbereitschaft
- Aussagen über Versicherungszulassungen über das IK-Kennzeichen hinaus
- Erwähnung konkreter Pflegekassen-Verträge ohne Beleg
- Behauptungen über eine digitale Buchungsmöglichkeit oder Online-Formular (kein Beleg für E-Mail-Kanal)

---

## 9. Visuelle Prüfliste für den Reviewer

### Desktop (ab 1024 px)

- [ ] Hero-Bereich: Firmenname und Leitmotiv auf den ersten Blick lesbar, CTA-Button mit Telefonnummer sichtbar ohne Scrollen
- [ ] Alle 8 Leistungen dargestellt (vollständige Liste laut Abschnitt 1)
- [ ] Pflegenote 1,2 mit Quellenhinweis sichtbar
- [ ] Gründungsjahr 1993 und Name Angelika Düwel im Über-uns-Abschnitt vorhanden
- [ ] Alle Platzhalter aus Abschnitt 2 als solche ausgewiesen — kein erfundener Inhalt
- [ ] Adresse und Telefon im Kontakt-Abschnitt korrekt (Krohnskamp 13, 22301 Hamburg, 040 519246)
- [ ] Kein zweiter CTA (kein Formular, kein "Termin buchen" ohne Beleg)
- [ ] Kein Text aus der "Nicht erlaubte Behauptungen"-Liste (Abschnitt 8) vorhanden
- [ ] Kontrast Fließtext auf Hintergrund: WCAG AA (4,5:1 Minimum)
- [ ] CTA-Button-Kontrast: WCAG AA (3:1 Minimum für großen Text)

### Mobil (375 px — iPhone SE / kleinste gängige Breite)

- [ ] Hero-Text lesbar ohne Zoomen; Telefon-CTA als tappbarer Button (min. 44x44 px Tap-Target)
- [ ] Leistungs-Kacheln umbrechen sauber (1-spaltig auf 375 px oder 2-spaltig ohne Überlauf)
- [ ] Kein horizontales Scrollen
- [ ] Schriftgröße Lauftext mindestens 16px auf 375 px
- [ ] Kontakt-Abschnitt: Telefonnummer ist ein `tel:`-Link (direktes Tippen zum Anrufen)
- [ ] Pflegenote und Über-uns-Block vollständig sichtbar ohne abgeschnittene Inhalte
- [ ] Kein Bild-Overlay macht Text auf kleinem Bildschirm unlesbar

---

## 10. HTML-Übergabe-Hinweise

- **Self-contained:** Alle Styles inline oder in einem `<style>`-Block — kein externes CSS-Framework, keine externe JS-Abhängigkeit außer optionalem Karten-Embed.
- **Platzhalter-Darstellung:** Jeder `[PLATZHALTER]` als visuell abgehobener Block (z.B. gestrichelte Umrandung, hellgrauer Hintergrund, Schriftgröße 13px in Kleinschrift).
- **Keine externen Fonts per CDN** falls nicht gewünscht — System-Font-Stack ist ausreichend und schneller.
- **Karten-Embed:** OpenStreetMap-Permalink oder statischer Google-Maps-Link — kein JavaScript-API-Key erforderlich.
- **Telefon-CTA:** `<a href="tel:+4940519246">040 519246</a>` — korrekt für Mobile.
- **Keine Tracking-Pixel, keine Analytics, keine Cookie-Banner** in der Demo.
