# ResearchTranscript — Beschreibung der Datenverarbeitung

Textbaustein zum Einfügen in ein Verfahrensverzeichnis, eine
Datenschutz-Folgenabschätzung, einen Ethikantrag oder einen
Datenmanagementplan. Stand 23. September 2026, ResearchTranscript 0.6.2.
Angaben in `[eckigen Klammern]` ergänzt die verantwortliche Stelle.

Der Text beschreibt, was die Software tut und was sie nicht tut. Die
rechtliche Einordnung der eigenen Verarbeitung — nach DSGVO oder
revidiertem Schweizer DSG — nimmt die verantwortliche Stelle vor; der
Text ersetzt keine Rechtsberatung.

Dieser Text ist die allgemeine Vorlage. Seit 0.6.0 erzeugt die App
selbst die Fassung zum einzelnen Transkript (Editor › Export ›
«Dokumentationspaket (.zip) …»): Transkriptionsprotokoll mit dem
tatsächlich verwendeten Modell samt Version und dem gemessenen Mass der
Bearbeitung von Hand, Methodenabsatz, Tatsachen für den Datenschutz,
Datenblatt für das Repositorium und Zitierdatei.

---

## 1. Eingesetzte Software

ResearchTranscript, Version `[0.6.2]`. Freie Software unter
AGPL-3.0-or-later (mit einer Zusatzerlaubnis für den Vertrieb über den
App Store), entwickelt am B/IAS – Basel Institut für angewandte
Stadtforschung. Quellcode öffentlich unter
<https://github.com/bias-city/ResearchTranscript>; das signierte und
notarisierte Installationspaket (DMG) liegt dort bei den Releases. Die
Software läuft als lokale Anwendung auf macOS (Apple Silicon) in der
App Sandbox von macOS und wird von der verantwortlichen Stelle selbst
installiert und betrieben.

## 2. Zweck der Verarbeitung

Umwandlung von Audioaufnahmen `[z. B. leitfadengestützte Interviews im
Projekt …]` in Text mit Zeitmarken und Sprecherzuordnung, zur
anschliessenden qualitativen Auswertung `[in ATLAS.ti / MAXQDA / NVivo /
enrich / …]`.

## 3. Betroffene Personen und Datenkategorien

Betroffen sind die aufgenommenen Personen `[Interviewpartner:innen,
Teilnehmende an Gruppengesprächen, …]`. Verarbeitet werden
Sprachaufnahmen (Stimme und Gesprächsinhalt) sowie die daraus erzeugten
Transkripte mit Zeitmarken und Sprecherzuordnung. Je nach
Gesprächsinhalt können besondere Kategorien personenbezogener Daten
betroffen sein `[ja / nein: …]`.

## 4. Datenfluss einer Transkription

1. **Eingabe.** Die Audio- oder Videodatei wird vom lokalen Dateisystem
   des Endgeräts eingelesen (Audio: MP3, WAV, M4A, OGG, FLAC; Video:
   MP4, MOV, M4V mit H.264/HEVC — aus Video wird nur die Tonspur
   gelesen, das Video wird nie umgewandelt). Den Ton liest macOS
   AVFoundation. Die App Sandbox von macOS erlaubt den Zugriff nur auf
   Ordner, die die Person im Dialog wählt, und auf hineingezogene
   Dateien.
2. **Verarbeitung.** Die Anwendungslogik läuft eingebettet in der App.
   Die Spracherkennung (whisper.cpp 1.8.2, Modell large-v3-turbo) läuft
   als Hilfsprogramm aus dem App-Paket auf der Grafikeinheit (Metal).
   Die Sprechertrennung (SpeakerKit von Argmax mit den Modellen
   pyannote segmentation-3.0, WeSpeaker ResNet34 und pyannote
   community-1, von Argmax nach Core ML umgewandelt) läuft in der App
   über Core ML und ist abschaltbar. Die Sprachaktivitätserkennung
   (Silero VAD 5.1.2 in whisper.cpp) wird nur verwendet, wenn die
   Sprechertrennung ausgeschaltet ist; sonst schneidet die
   Sprechertrennung die Blöcke. Sämtliche Modelle sind im Programmpaket
   enthalten; die Anwendung lädt weder Modelle noch Programmteile nach.
   Eigene whisper.cpp-Modelle kann die Anwenderin nur von Hand in den
   Ordner «Modelle» der Bibliothek legen. Die Modelle lernen nicht aus
   den Aufnahmen. Die Anwendung fasst nichts zusammen und formuliert
   nichts um; die Spracherkennung ist ein KI-Modell und kann Wörter
   setzen, die nicht gesagt wurden, darum ist das Transkript gegen die
   Aufnahme zu prüfen.
3. **Ablage.** Je Transkript entsteht ein Unterordner im gewählten
   Bibliotheksordner `[Pfad]` mit `transkript.json` (Wortlaut, Sprecher,
   Memos, Journal, Zotero-Angaben), einer Kopie der Aufnahme (bei Video
   auch der unveränderten Videodatei) und `wellenform.json`.
   `ausgang.json` hält den Stand fest, wie ihn die Maschine oder eine
   importierte Datei lieferte; `history/` hält die letzten 30 Stände.
   **Beide enthalten den Wortlaut vor einer Pseudonymisierung.**
   Einstellungen und App-Protokoll liegen im App-Container des
   Benutzerkontos. Das Journal vermerkt eine Kennung der Installation
   und, freiwillig, eine E-Mail-Adresse der bearbeitenden Person.
4. **Netz.** Die Software überträgt keine Aufnahmen, Texte oder
   Nutzungsdaten: kein Konto, keine Telemetrie, keine Update-Prüfung,
   keine eigenen Absturzberichte, kein Nachladen von Modellen. Es gibt
   keinen internen Dienst, keinen Server und keinen offenen Port. Die
   Netzberechtigung von macOS ist nur gesetzt, weil die eingebaute
   Web-Ansicht sie verlangt; eine Firewall oder `nettop` zeigt, dass
   keine Verbindung entsteht. Absturzberichte des Betriebssystems macOS
   unterliegen dessen Systemeinstellungen, nicht der Software.
5. **Ausgabe.** Exportdateien werden dorthin geschrieben, wo die
   bedienende Person sie speichert. Alle Textformate (VTT, CSV, TXT,
   Markdown, Word) enthalten Wortlaut, Sprechernamen und Zeitmarken;
   CSV, Markdown und Word zusätzlich die Memos; Markdown und Word bei
   Zotero-Verknüpfung einen Kopf mit Titel, Datum, Citekey und den
   Personen, deren Rollen gewählt wurden. **REFI-QDA (`.qdpx.zip`)
   enthält Text, Memos und die Tonaufnahme, also die Stimme, auf Wunsch
   die Videodatei; das enrich-Dossier (`.enrich`) Text, Tonaufnahme als
   MP3 (über LAME), Journal mit Kennung der Installation und E-Mail
   sowie Zotero-Angaben, keine Memos.** Ihre Weitergabe ist eine
   Weitergabe der Aufnahme. Mit Zotero-Einwilligung liest die Anwendung
   die lokale `zotero.sqlite` nur lesend und nur auf Anfrage. Bei einer
   Videoaufnahme liegt die Videodatei unverändert im Ordner des
   Transkripts (Gesichter sind personenbezogene, bei Identifizierbarkeit
   biometrische Daten).

## 5. Ort der Verarbeitung

Ausschliesslich auf dem Endgerät `[Gerät, Standort]` in der Sitzung der
angemeldeten Person. Es gibt keinen Server, keinen offenen Port, keinen
Cloud-Dienst und kein Benutzerkonto.

## 6. Empfänger, Auftragsverarbeitung, Drittlandübermittlung

Keine. Da keine Daten übermittelt werden, gibt es weder Empfänger noch
Auftragsverarbeiter noch eine Übermittlung in ein Drittland. Eine
Weitergabe findet nur statt, wenn die verantwortliche Stelle
Exportdateien selbst weitergibt `[an …, auf dem Weg …]`.

## 7. Speicherdauer und Löschung

Aufbewahrung der Aufnahmen und Transkripte: `[Frist, Grundlage]`.
Löschen in der Anwendung verschiebt einen Eintrag in einen
Papierkorb-Ordner innerhalb der Bibliothek (`_papierkorb`); endgültig
entfernt wird er erst durch Leeren dieses Ordners im Finder `[durch wen,
wann]`. `ausgang.json` und die Stände in `history/` liegen im Ordner des
jeweiligen Transkripts und werden mit ihm gelöscht. Sicherungskopien
des Endgeräts `[Time Machine, …]` unterliegen der Löschregel der
Stelle.

## 8. Technische und organisatorische Massnahmen

Von der verantwortlichen Stelle zu erbringen, da die Software selbst
keine Zugriffssteuerung mitbringt:

- Verschlüsselung des Datenträgers, z. B. FileVault: `[aktiv seit …]`
- Zugriffsschutz des Endgeräts (Anmeldung, Bildschirmsperre): `[…]`
- Pseudonymisierung vor jeder Weitergabe — im Editor der Anwendung
  lassen sich Sprecher umbenennen und Namen im Text per Suchen und
  Ersetzen tauschen; die Entscheidung, was zu ersetzen ist, trifft die
  bearbeitende Person: `[Verfahren, Zuständigkeit]`
- Regel für Sicherungskopien: `[…]`
- Regel für die Weitergabe von Exportdateien, insbesondere solcher mit
  Audio: `[…]`

## 9. Rechtsgrundlage und Information der Betroffenen

`[Einwilligung / berechtigtes Interesse / Forschungsprivileg nach …;
Informationsschreiben vom …]`. Die Software trägt hierzu nichts bei.

## 10. Nachprüfbarkeit

Die Aussagen in Abschnitt 4 lassen sich am Quellcode prüfen: Die Shell
`frontend/src-tauri/src/lib.rs` startet keinen Server und öffnet keinen
Port; die Sandbox-Berechtigungen stehen in
`frontend/src-tauri/entitlements.plist`. Das Repository enthält die
vollständige Build-Kette bis zum signierten Installationspaket; wer der
ausgelieferten Binärdatei nicht traut, kann sie selbst erzeugen.

---

Quelle dieses Textes: <https://github.com/bias-city/ResearchTranscript>
(Ordner `site/docs`). Er steht unter CC BY 4.0: frei verwendbar und
anpassbar, auch kommerziell, sofern B/IAS genannt und Änderungen
gekennzeichnet werden.
