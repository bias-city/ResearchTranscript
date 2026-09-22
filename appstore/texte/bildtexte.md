# Store-Bilder: Gestaltung und Texte

Vorschlag vom 22.9.2026, gezogen aus den Website-Texten (`site/index.html`) und der
Store-Beschreibung. Zielgruppe: qualitative Forschung, Auswertung mit QDA-Software.

## Haltung

Die App ist Werkzeug, nicht Unterhaltung. Die Bilder sollen wie eine Methodenseite
wirken, nicht wie eine Anzeige: ruhiger Grund, eine Aussage je Bild, das Fenster gross
genug, dass man die Oberfläche wirklich liest. Keine Pfeile, keine Sticker, keine
Gerätemontagen, keine Verläufe.

Drei Botschaften tragen alles, in dieser Reihenfolge:

1. **Der Mensch entscheidet.** Die KI liefert den Rohtext, geprüft wird von Hand.
2. **Es bleibt auf dem Rechner.** Quellenschutz ist bei Interviews kein Zusatz.
3. **Es endet zitierfähig.** REFI-QDA, Dokumentationspaket, Korrekturrate.

## Aufbau je Bild (2880 × 1800, 16:10)

| Element | Wert |
|---|---|
| Grund, helle Motive | `#f3f5f6` (Website `--wash`) |
| Grund, dunkles Motiv | `#1a1d20` (Website `--dunkel`), Schrift weiss |
| Aussenrand | 140 px |
| Schlagzeile | Recursive, 96 px, Gewicht 640, Zeilenabstand 1.12, Farbe `#000` bzw. `#fff` |
| Unterzeile | Recursive, 44 px, Gewicht 400, Farbe `#000` bei 70 % Deckung |
| Abstand Schlagzeile → Unterzeile | 20 px |
| Abstand Text → Fenster | 72 px |
| Fenster | volle Restbreite, Radius 18 px, Schatten `0 24px 60px rgba(0,0,0,.18)` |
| Akzent | `#4f46e5` (Website `--lila-600`), nur für ein einzelnes Wort oder eine 4-px-Linie über der Schlagzeile |

Schrift ist **Recursive** aus `site/fonts/Recursive_VF.woff2` (SIL OFL 1.1, Nennung in
`OFL.txt`) — dieselbe wie auf der Website, mit `CASL 0` und `MONO 0`.

Die Aufnahmen kommen aus der **gebauten Store-App**, nicht aus dem Browser: Umschalt-
Befehl-Vier, dann Leertaste auf das Fenster. Nur so zeigen die Bilder die eingereichte
Fassung (im Browser rendert die Oberfläche den Zweig für den Direktvertrieb).

## Reihenfolge und Texte

Die ersten drei Bilder sieht man im Store ohne Blättern.

### 1 · Editor (hell) — `01-editor`

| | |
|---|---|
| de | **Die KI schreibt. Du behältst das letzte Wort.**<br>Hören, korrigieren, Sprechende benennen — alles über die Tastatur. |
| en | **The AI writes. You have the last word.**<br>Listen, correct, name speakers — all from the keyboard. |
| fr | **L'IA écrit. Le dernier mot te revient.**<br>Écouter, corriger, nommer les locuteurs — au clavier. |
| it | **L'IA scrive. L'ultima parola è tua.**<br>Ascoltare, correggere, dare un nome a chi parla — da tastiera. |

### 2 · Warteliste (hell) — `02-ai-transkript`

| | |
|---|---|
| de | **Interviews hinein, Transkripte heraus.**<br>Mit Sprechertrennung. Mehrere Aufnahmen nacheinander, ohne Aufsicht. |
| en | **Interviews in, transcripts out.**<br>With speaker separation. Several recordings in a row, unattended. |
| fr | **Des entretiens en entrée, des transcriptions en sortie.**<br>Avec séparation des locuteurs. Plusieurs enregistrements à la suite. |
| it | **Interviste dentro, trascrizioni fuori.**<br>Con separazione dei parlanti. Più registrazioni di seguito. |

### 3 · Export (hell) — `03-export`

| | |
|---|---|
| de | **Zitierfähig, ohne Nacharbeit.**<br>REFI-QDA für die Analyse, Word für den Text, Dokumentationspaket für den Methodenteil. |
| en | **Citable, with no extra work.**<br>REFI-QDA for analysis, Word for the text, a documentation package for your methods section. |
| fr | **Citable, sans retouches.**<br>REFI-QDA pour l'analyse, Word pour le texte, un dossier de documentation pour la partie méthodes. |
| it | **Citabile, senza rilavorazione.**<br>REFI-QDA per l'analisi, Word per il testo, un pacchetto di documentazione per la sezione metodi. |

### 4 · Datenschutz (dunkel) — neu aufnehmen: Einstellungen, unterer Teil

| | |
|---|---|
| de | **Nichts verlässt deinen Mac.**<br>Kein Konto, keine Cloud, keine Telemetrie. Alle Modelle sind enthalten. |
| en | **Nothing leaves your Mac.**<br>No account, no cloud, no telemetry. All models are included. |
| fr | **Rien ne quitte ton Mac.**<br>Pas de compte, pas de cloud, pas de télémétrie. Tous les modèles sont inclus. |
| it | **Nulla lascia il tuo Mac.**<br>Nessun account, nessun cloud, nessuna telemetria. Tutti i modelli sono inclusi. |

### 5 · Suchen und Ersetzen (hell) — `04-suchen-ersetzen`

| | |
|---|---|
| de | **Pseudonyme in einem Zug.**<br>Suchen und Ersetzen über das ganze Transkript, mit Vorschau je Fund. |
| en | **Pseudonyms in one pass.**<br>Search and replace across the whole transcript, with a preview for each hit. |
| fr | **Les pseudonymes d'un seul geste.**<br>Rechercher et remplacer dans toute la transcription, avec aperçu. |
| it | **Pseudonimi in un colpo solo.**<br>Cerca e sostituisci in tutta la trascrizione, con anteprima. |

### 6 · Sprechende (hell) — `05-sprecherfarbe`

| | |
|---|---|
| de | **Sprechende benennen, färben, zusammenführen.**<br>Hörprobe je Stimme, bevor du dich entscheidest. |
| en | **Name, colour and merge your speakers.**<br>Listen to each voice before you decide. |
| fr | **Nommer, colorer, fusionner les locuteurs.**<br>Écouter chaque voix avant de décider. |
| it | **Nomina, colora e unisci chi parla.**<br>Ascolta ogni voce prima di decidere. |

### 7 · Editor dunkel — `07-editor-dunkel`

| | |
|---|---|
| de | **Timecodes auf die Hundertstelsekunde.**<br>Wellenform in den Farben der Sprechenden, zoombar bis in die Silbe. |
| en | **Timecodes to the hundredth of a second.**<br>Waveform in the speakers' colours, zoomable down to the syllable. |
| fr | **Des timecodes au centième de seconde.**<br>Forme d'onde aux couleurs des locuteurs, zoomable jusqu'à la syllabe. |
| it | **Timecode al centesimo di secondo.**<br>Forma d'onda nei colori di chi parla, con zoom fino alla sillaba. |

### 8 (wenn Platz) · Bibliothek (hell) — `06-bibliothek`

| | |
|---|---|
| de | **Alles in dem Ordner, den du wählst.**<br>Je Transkript ein Ordner mit Audio, Text und Verlauf. |
| en | **Everything in the folder you choose.**<br>One folder per transcript, with audio, text and history. |
| fr | **Tout dans le dossier que tu choisis.**<br>Un dossier par transcription, avec audio, texte et historique. |
| it | **Tutto nella cartella che scegli.**<br>Una cartella per trascrizione, con audio, testo e cronologia. |

## Was die Richtlinie dazu sagt

> 2.3.3 Screenshots should show the app in use … They may also include text and image
> overlays.

Beschriftung und Grund sind also zulässig. Die Grenze liegt beim Inhalt des Fensters:
Es muss die eingereichte Fassung zeigen, in Benutzung, ohne Funktionen, die es nicht
gibt. Deshalb die Aufnahme aus der Store-App und nicht aus dem Browser.
