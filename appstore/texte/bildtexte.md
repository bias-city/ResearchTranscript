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

Vier Bilder, die zusammen einen Ablauf erzählen — mehr verwässert nur. Hell und
dunkel wechseln sich ab, damit der Satz im Store nicht monoton wirkt und beide
Erscheinungsbilder belegt sind.

| # | Grund | Rohaufnahme | Was zu sehen ist |
|---|---|---|---|
| 1 | hell | `01-editor.png` | Editor mit Transkript, zwei Sprechenden, Wellenform — **eine Zeile offen in Bearbeitung, Text markiert**. Der Titel verspricht das Korrigieren, also muss man es sehen. |
| 2 | dunkel | `02-ai-transkript.png` | Ein Lauf **arbeitet**: Blockzähler, Fortschritt, mitlaufender Text. Darüber wartet die Schlange mit drei Dateien und ihrer Sprecherzahl, darunter steht ein fertiger Lauf. |
| 3 | hell | `09-memo.png` | Memo-Dialog an derselben Zeile, Memo **geschrieben** — in der Sprache der Oberfläche. |
| 4 | dunkel | `03-export.png` | offenes Export-Menü mit allen Formaten |

Nicht mehr im Satz, aber jederzeit wieder aufnehmbar: Suchen und Ersetzen,
Sprecherfarben, Bibliothek, Einstellungen. Die Datenschutz-Aussage steht jetzt in
der Unterzeile von Motiv 2, wo sie am Bild hängt.

## Aufnahme

Die Rohaufnahmen entstehen mit dem Skript — vier Sprachen, beide Erscheinungsbilder,
in einem Lauf:

```
node scripts/appstore-screenshots.mjs --satz
node scripts/appstore-montage.mjs
```

Aufgenommen wird die echte Oberfläche gegen ein Demo-Backend mit dem **erfundenen**
Interview aus `docs/demo` — nie echtes Forschungsmaterial. Fenster 1440 × 720 bei
doppelter Auflösung: 2880 × 1440, Seitenverhältnis 2:1, damit das Fenster die Bühne
der Montage fast ganz füllt. Ergebnis:
`appstore/screenshots/<sprache>/<hell|dunkel>/2880x1440/`.

**Handaufnahmen nur als Rückfall.** Wo ein Motiv im Browser-Betrieb nicht entstehen
kann — vor allem die Einstellungsseite, die dort den Knopf «Releases» aus dem
DMG-Kanal zeigt —, kommt es aus der gebauten Store-App: Umschalt-Befehl-Vier, dann
Leertaste, dann auf das Fenster klicken; Fenster vorher breit ziehen. macOS nimmt es
**mit Schatten und durchsichtigen Ecken** auf, beides muss weg:

```
python3 scripts/appstore-freistellen.py ~/Desktop/Bildschirmfoto\ ….png \
        appstore/upload/de/08-einstellungen.png
```

Das Skript schneidet auf den deckenden Fensterbereich zu und füllt die gerundeten
Ecken mit der Farbe des nächsten Fensterpixels; Rundung und Schatten setzt die
Montage, damit alle Motive gleich aussehen. Die Montage nimmt für jedes Motiv zuerst
das erzeugte Bild und greift nur dort auf `appstore/upload/<sprache>/` zurück, wo
keines liegt — sie sagt in der Ausgabe, wann sie das tut.

Ergebnis: `appstore/store/<sprache>/NN-motiv.png`, fertig zum Hochladen.

## Was die Richtlinie dazu sagt

> 2.3.3 Screenshots should show the app in use … They may also include text and image
> overlays.

Beschriftung und Grund sind also ausdrücklich zulässig. Die Grenze liegt beim Inhalt
des Fensters: Es muss die eingereichte Fassung zeigen, in Benutzung, ohne Funktionen,
die es nicht gibt.
