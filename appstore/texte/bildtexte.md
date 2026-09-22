# Store-Bilder: Haltung, Gestaltung, Aufnahme

Stand 22.9.2026. Gezogen aus den Website-Texten (`site/index.html`) und der
Store-Beschreibung. Zielgruppe: qualitative Forschung, Auswertung mit QDA-Software.

> **Die Beschriftungen stehen in `bildtexte.json`, nicht hier.** Dort liest sie das
> Montageskript, in allen vier Sprachen. Hier steht nur, warum sie so aussehen und
> was auf den Aufnahmen zu sehen sein soll. Zwei Dateien mit denselben Texten laufen
> sonst auseinander.

## Haltung

Die App ist Werkzeug, nicht Unterhaltung. Die Bilder sollen wie eine Methodenseite
wirken, nicht wie eine Anzeige: ruhiger Grund, eine Aussage je Bild, das Fenster gross
und **ganz** sichtbar. Keine Pfeile, keine Sticker, keine Gerätemontagen.

Drei Botschaften tragen die Reihenfolge:

1. **Der Mensch entscheidet.** Die KI liefert den Rohtext, geprüft wird von Hand.
2. **Es bleibt auf dem Rechner.** Quellenschutz ist bei Interviews kein Zusatz.
3. **Es endet zitierfähig.** REFI-QDA, Dokumentationspaket, Korrekturrate.

## Gestaltung (2880 × 1800, 16:10)

| Element | Wert |
|---|---|
| Grund, alle Motive | `#eef2ff` (Website `--lila-050`) |
| Aussenrand | 100 px |
| Akzentlinie über der Schlagzeile | 110 × 4 px, `#4f46e5` (Website `--lila-600`) |
| Schlagzeile | Recursive, 76 px, Gewicht 640, Zeilenabstand 1.1 |
| Unterzeile | Recursive, 38 px, Gewicht 400, Schwarz bei 70 % Deckung |
| Kopfhöhe | 300 px, danach 44 px Luft |
| Fenster | ganz sichtbar, mittig in der Restfläche, Radius 18 px, weicher Schatten in Indigo |

Schrift ist **Recursive** aus `site/fonts/Recursive_VF.woff2` (SIL OFL 1.1, Lizenztext
in `OFL.txt`), dieselbe wie auf der Website, mit `CASL 0` und `MONO 0`.

Zwei Entscheide, die aus dem ersten Entwurf stammen:

- **Das Fenster wird nicht angeschnitten.** Im Editor sitzt die Wellenform am unteren
  Rand — genau die wäre sonst weg. Deshalb ist der Kopf knapp gehalten und das Bild
  wird in die Restfläche eingepasst.
- **Der Grund ist der Markenton, nicht das neutrale Grau der Website.** `--wash` lag zu
  nah an der Fensterleiste von macOS, das Fenster verschwand im Hintergrund.

## Motive, in dieser Reihenfolge

Die ersten drei sieht man im Store ohne Blättern.

| # | Rohaufnahme | Was zu sehen sein soll |
|---|---|---|
| 1 | `01-editor.png` | Editor mit Transkript, zwei Sprechenden, Wellenform unten — **und eine Zeile offen in Bearbeitung**, Einfügepunkt im Text sichtbar. Der Titel verspricht das Korrigieren, also muss man es sehen. |
| 2 | `08-einstellungen.png` | **neu** — Einstellungen, Karte Datenschutz und Lizenzen |
| 3 | `02-ai-transkript.png` | **laufende** Transkription: Blockzähler, Fortschrittsbalken, mitlaufender Text — **im dunklen Erscheinungsbild**. Die reine Warteliste zeigte nur Dateinamen; dass die App gerade arbeitet, sieht man erst am Fortschritt. |
| 4 | `03-export.png` | offenes Export-Menü mit allen Formaten |
| 5 | `09-memo.png` | **neu** — Editor mit **offenem Memo-Dialog an einer Zeile**, Memo geschrieben (ein echter Analysegedanke, kein «Test»). Die Bibliothek zeigte nur einen Ordner mit Dateien; das sagt über die Arbeit nichts. |
| 6 | `04-suchen-ersetzen.png` | Suchen und Ersetzen mit Treffern |
| 7 | `05-sprecherfarbe.png` | Sprechende benennen und färben |
| 8 | `07-editor-dunkel.png` | derselbe Editor im dunklen Erscheinungsbild |

## Aufnahme

Die Rohaufnahmen kommen aus der **gebauten Store-App** (TestFlight), nicht aus dem
Browser: Umschalt-Befehl-Vier, dann Leertaste, dann auf das Fenster klicken. Das Fenster
vorher **breit ziehen** — je näher es an 2:1 kommt, desto grösser steht es in der
Montage; ein schmales Fenster lässt links und rechts Luft stehen.

macOS nimmt das Fenster **mit Schatten und durchsichtigen Ecken** auf. Beides muss weg,
sonst zeigt die Montage einen schmutzigen Rand und vier helle Zipfel:

```
python3 scripts/appstore-freistellen.py ~/Desktop/Bildschirmfoto\ ….png \
        appstore/upload/de/09-memo.png
```

Das Skript schneidet auf den deckenden Fensterbereich zu und füllt die gerundeten Ecken
mit der Farbe des nächsten Fensterpixels. Rundung und Schatten setzt die Montage selbst,
damit alle Motive gleich aussehen. Ablegen unter `appstore/upload/<sprache>/` mit genau
den Dateinamen aus der Tabelle.

Warum nicht aus dem Browser: Dort ist `isTauri()` falsch und der Vertriebskanal «dmg».
Die Einstellungsseite zeigt dann einen Knopf «Releases», der aus dem Store heraus auf
Downloads ausserhalb des Stores verweist, und es fehlen Bedienelemente, die es nur in
der App gibt. Genau daran wäre die alte Fassung gescheitert.

Danach montieren:

```
node scripts/appstore-montage.mjs              # alle vier Sprachen
node scripts/appstore-montage.mjs --sprachen de
```

Ergebnis: `appstore/store/<sprache>/NN-motiv.png`, fertig zum Hochladen.

## Was die Richtlinie dazu sagt

> 2.3.3 Screenshots should show the app in use … They may also include text and image
> overlays.

Beschriftung und Grund sind also ausdrücklich zulässig. Die Grenze liegt beim Inhalt
des Fensters: Es muss die eingereichte Fassung zeigen, in Benutzung, ohne Funktionen,
die es nicht gibt.
