# ResearchTranscript — App-Blatt für Forschende

Was die App ist, welche KI darin was tut, wo der Code liegt, und warum
das Transkript den Rechner nicht verlässt. Zum Weitergeben an
Projektleitung, Ethikkommission oder Kolleg:innen. Stand 18. September
2026, Version 0.6.0.

Dieses Blatt ist die allgemeine Vorlage. Seit 0.6.0 erzeugt die App
selbst die Fassung zum einzelnen Transkript (Editor › Export ›
«Dokumentationspaket (.zip) …»): Transkriptionsprotokoll mit dem
tatsächlich verwendeten Modell samt Version und dem gemessenen Mass der
Bearbeitung von Hand, Methodenabsatz, Tatsachen für den Datenschutz,
Datenblatt für das Repositorium und Zitierdatei.

## Was die App tut

ResearchTranscript wandelt Audioaufnahmen — Interviews, Gruppengespräche,
Workshops — in Text mit Zeitmarken und Sprecherzuordnung um. Danach
wird das Transkript in einem Editor korrigiert, Sprecher werden
benannt, Namen ersetzt, und das Ergebnis wird für die Auswertung
exportiert (ATLAS.ti, MAXQDA, NVivo über REFI-QDA; enrich; WebVTT,
CSV, Text, Markdown, Word). Videoaufnahmen (MP4/MOV) nimmt sie ebenfalls
an: der Ton wird ausgelesen, das Video bleibt unverändert beim
Transkript und verlässt den Rechner nur, wenn man es beim
REFI-QDA-Export ausdrücklich mitgibt. Alles davon geschieht auf dem
eigenen Mac.

## Welche KI hier was macht

| Baustein | Aufgabe | Herkunft, Lizenz | Läuft wo |
|---|---|---|---|
| whisper.cpp 1.8.2 mit Modell `large-v3-turbo` | Spracherkennung: Audio → Text mit Zeitmarken | Modell von OpenAI (MIT), Laufzeit whisper.cpp (MIT) | lokal, als Hilfsprogramm aus dem App-Paket, auf der Grafikeinheit des Macs (Metal) |
| Silero VAD 5.1.2 (in whisper.cpp) | Sprachaktivität: erkennt, wo überhaupt gesprochen wird. Nur bei ausgeschalteter Sprechertrennung; sonst schneidet die Sprechertrennung die Blöcke | MIT | lokal, im selben Hilfsprogramm |
| SpeakerKit (Argmax) mit den Modellen pyannote segmentation-3.0, WeSpeaker ResNet34 und pyannote community-1 | Sprechertrennung: erkennt Sprecherwechsel samt Überlappung und gruppiert die Stimmen; abschaltbar | Modelle aus pyannote speaker-diarization-community-1 (CC BY 4.0), von Argmax nach Core ML umgewandelt; Laufzeit SpeakerKit von Argmax (MIT) | lokal, in der App, über Core ML |

Alle Modelle liegen im Programmpaket; die App lädt weder Modelle noch
Programmteile nach. Den Ton liest macOS selbst (AVFoundation), MP3
schreibt LAME (LGPL, dynamisch gelinkt). Es gibt keinen Zugang zu
einem KI-Dienst, kein Konto, keinen Schlüssel. Wer ein anderes
whisper.cpp-Modell einsetzen will, legt es selbst in den Ordner
«Modelle» der Bibliothek; ein solches Modell ist nicht Teil dieser
Liste, und im Journal jedes Transkripts steht, womit es entstand.

**Kein Zusammenfassen, kein Umformulieren.** Die App fasst nichts
zusammen und formuliert nichts um. Die Modelle lernen nicht aus den
Aufnahmen.

**Grenze der Spracherkennung.** Die Spracherkennung ist ein KI-Modell.
Wo es nichts versteht (Nebengeräusche, Dialekt, Überlappungen), kann es
Wörter setzen, die nicht gesagt wurden. Ein Transkript aus
ResearchTranscript ist ein **Rohtranskript**, das gegen die Aufnahme geprüft
werden muss; der Editor ist dafür gebaut. Standarddeutsch, Französisch,
Italienisch und Englisch werden gut erkannt, Schweizerdeutsch lückenhaft
— die Sprecher werden trotzdem sauber getrennt.

## Wo der Code liegt

- Quellcode: <https://github.com/bias-city/ResearchTranscript>
- Lizenz: AGPL-3.0-or-later, mit einer Zusatzerlaubnis für den Vertrieb
  über den App Store — freie Software, darf genutzt, geprüft, verändert
  und weitergegeben werden
- Entwickelt am B/IAS – Basel Institut für angewandte Stadtforschung,
  Beckenweg 6, 4056 Basel, <https://bias.city>
- Installationspaket (DMG): signiert und notarisiert mit Apple
  Developer ID, bei den Releases auf GitHub, mit Prüfsumme
- Wer der Binärdatei nicht traut: Das Repository enthält die
  vollständige Build-Kette, die App lässt sich selbst bauen

## Das Transkript verlässt den Rechner nicht

- Die App überträgt **keine Aufnahmen, Texte oder Nutzungsdaten**: kein
  Konto, keine Telemetrie, keine Update-Prüfung, keine eigenen
  Absturzberichte, kein Nachladen von Modellen. Die Netzberechtigung
  von macOS ist nur gesetzt, weil die eingebaute Web-Ansicht sie
  verlangt; eine Firewall oder `nettop` zeigt, dass keine Verbindung
  entsteht.
- Es gibt keinen internen Dienst: kein Server, kein offener Port. Die
  Anwendungslogik läuft eingebettet in der App. Nachlesbar für jede
  Person: Die Shell `frontend/src-tauri/src/lib.rs` startet keinen
  Server und öffnet keinen Port.
- Die App läuft in der App Sandbox von macOS: Zugriff nur auf Ordner,
  die im Dialog gewählt wurden, und auf hineingezogene Dateien. Die
  Berechtigungen stehen in `frontend/src-tauri/entitlements.plist`.
- Aufnahme und Transkript liegen im gewählten Bibliotheksordner, je
  Transkript ein Unterordner: `transkript.json` (Wortlaut, Sprecher,
  Memos, Journal, Zotero-Angaben), eine Kopie der Aufnahme, bei Video
  auch die Videodatei, `wellenform.json`, dazu `ausgang.json` (Stand,
  wie ihn die Maschine oder eine importierte Datei lieferte) und
  `history/` (die letzten 30 Stände). Gelöschtes bleibt im Ordner
  `_papierkorb` der Bibliothek, bis er im Finder geleert wird.
  Einstellungen und App-Protokoll liegen im App-Container des
  Benutzerkontos.
- Kein Cloud-Dienst, kein Benutzerkonto, kein Auftragsverarbeiter, kein
  Drittlandtransfer — weil nichts übermittelt wird.

Was damit **nicht** abgedeckt ist: Backups des Macs (Time Machine,
iCloud Drive für den Dokumente-Ordner) und die Absturzberichte von macOS
selbst folgen den Systemeinstellungen, nicht der App. Wer den
Bibliotheksordner in einen synchronisierten Ordner legt, synchronisiert
die Aufnahmen.

## Namen pseudonymisieren

- **Sprecher umbenennen:** Ein Name im Sprecher-Panel gilt für alle
  Segmente dieser Person — aus «Sprecher 1» wird «B3» in einem Schritt.
- **Namen im Text:** «Suchen und Ersetzen» findet einen Namen in allen
  Segmenten, zeigt jeden Treffer im Zusammenhang und ersetzt einzeln
  oder alle auf einmal — auch, wenn das Transkript den Namen über eine
  Zeile getrennt hat.
- **Was die App nicht entscheidet:** welche Angaben zu ersetzen sind —
  Orte, Arbeitgeber, Ereignisse. Das bleibt eine Entscheidung der
  Forschenden.
- **Die Aufnahme bleibt, was sie ist.** Pseudonymisiert wird der Text
  der Endfassung. `ausgang.json` und `history/` enthalten den Wortlaut
  vor einer Pseudonymisierung, die Aufnahme Stimme und Klarnamen.
- **Was Exporte enthalten.** Alle Textformate (VTT, CSV, TXT, Markdown,
  Word): Wortlaut, Sprechernamen, Zeitmarken; CSV, Markdown und Word
  zusätzlich die Memos; Markdown und Word bei Zotero-Verknüpfung einen
  Kopf mit Titel, Datum, Citekey und den Personen, deren Rollen gewählt
  wurden. REFI-QDA (`.qdpx.zip`): Text, Memos und die Tonaufnahme, also
  die Stimme; auf Wunsch die Videodatei. enrich-Dossier (`.enrich`):
  Text, Tonaufnahme als MP3, Journal (Kennung der Installation,
  freiwillig E-Mail), Zotero-Angaben; keine Memos. Wer nur
  pseudonymisierte Daten weitergeben will, gibt ein Textformat weiter
  und prüft Memos und Kopf.

## Für den Methodenteil

> Die Aufnahmen wurden mit ResearchTranscript 0.6.0 (B/IAS Basel,
> AGPL-3.0-or-later; Spracherkennung whisper.cpp mit dem Modell
> large-v3-turbo, Sprechertrennung SpeakerKit mit pyannote-Modellen)
> lokal auf einem Rechner der Forschungsgruppe transkribiert; die App
> überträgt dabei keine Daten. Die Rohtranskripte wurden anschliessend
> gegen die Aufnahme geprüft, korrigiert und im Text pseudonymisiert.

---

Quelle: <https://github.com/bias-city/ResearchTranscript> (Ordner
`site/docs`). Das Blatt steht unter CC BY 4.0: frei verwendbar und
anpassbar, auch kommerziell, sofern B/IAS genannt und Änderungen
gekennzeichnet werden.
