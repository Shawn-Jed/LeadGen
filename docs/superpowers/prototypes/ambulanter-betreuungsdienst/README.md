# A/B-Vergleich — Demo Ambulanter Betreuungsdienst Düwel

Ziel: sehen, was die Design-Skills (`frontend-design` + `impeccable`) an der Prototyp-Qualität
bewegen. Beide One-Pager stammen aus **demselben** Entwurfsvertrag
([`../../briefs/ambulanter-betreuungsdienst-brief.md`](../../briefs/ambulanter-betreuungsdienst-brief.md))
— gleiche Fakten, gleiche eine CTA (`tel:040 519246`), gleiche markierte Platzhalter, beide
**self-contained** (keine externen Ladevorgänge).

| Datei | Bau |
|---|---|
| [`variant-a-ohne-skill.html`](variant-a-ohne-skill.html) | Ohne Design-Skill — solide, aber generisch: System-Font, gleich­förmiges Karten-Raster, Eyebrow-Label, Big-Number-„1,2", Material-Grün. |
| [`variant-b-mit-skill.html`](variant-b-mit-skill.html) | Mit `frontend-design` + impeccable-Craft-Floor — committete warme Farbwelt (Tannengrün/Creme/Terrakotta), charaktervolle Serifen-Display, asymmetrischer Hero, ein inszenierter Lade-Auftritt, gezeichnete SVG-Icons (statt Emoji), Pflegenote als Siegel, getönte Browser-Oberflächen (Selection/Scrollbar/Focus/Caret). |

**So vergleichen:** beide Dateien im Browser öffnen (Doppelklick), einmal Desktop, einmal
schmal ziehen (~375 px). Achte auf: Vertrauenswirkung, Lesbarkeit für 65+, Klarheit der CTA,
Mobil-Verhalten, „individuell vs. generisch".

**Fairness-Constraint:** Version B nutzt keine externen Google-Fonts (die die Design-Skill
sonst gern zöge), sondern einen web-safe Serifen-Stack — sonst wäre sie nicht self-contained
und würde die Technikprüfung (W3.4) und GitHub-Pages-Anforderung verletzen.

> Beide Varianten sind **lokale Entwürfe** (Demo-Status ≈ `draft_ready`). Es wird nichts
> veröffentlicht — ein öffentlicher Link entstünde erst nach ausdrücklicher Freigabe
> (`approved_local` → `published`, Welle 3.6).
