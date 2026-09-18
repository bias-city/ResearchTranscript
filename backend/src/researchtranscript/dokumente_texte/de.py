"""Texte des Dokumentationspakets — Deutsch (Quellsprache).

Schlüssel und Platzhalter `{…}` sind in allen Sprachen gleich. Mehrzeilige
Werte sind Listen: EIN Punkt je Zeile; « :: » trennt Tabellenspalten.
Sachform ohne Anrede, ein Gedanke je Satz. Offene Felder heissen `[ … ]`.
Stand nach Faktenprüfung, Lektorat und Nutzersicht vom 18.9.2026
(docs/begleitdokumente.md): kurze Einzeldokumente, nichts doppelt.
"""

T = {
    # ---- allgemein ----
    "feld": "Feld", "wert": "Wert", "datei": "Datei", "groesse": "Grösse", "hinweis": "Hinweis",
    "eintrag": "Eintrag", "dezimal": ",", "nicht_aufgezeichnet": "nicht aufgezeichnet",
    "fuss": "Erzeugt von ResearchTranscript {v} am {datum} für «{name}». Offene Felder `[ … ]` füllen die Forschenden aus.",
    "von": "{n} von {gesamt} ({anteil})",

    # ---- Ordner und Dateinamen (ASCII, klein, Bindestriche) ----
    "paket.ordner": "dokumentation", "ordner.methoden": "1-methoden", "ordner.datenschutz": "2-datenschutz",
    "ordner.ablage": "3-datenablage", "ordner.zitieren": "zitieren",
    "datei.liesmich": "LIESMICH", "datei.protokoll": "transkriptionsprotokoll",
    "datei.absatz": "methodenabsatz", "datei.tatsachen": "app-tatsachen",
    "datei.stelle": "angaben-der-stelle", "datei.datensatz": "datenblatt-datensatz",
    "datei.interview": "datenblatt-interview", "datei.ethik": "ethik-checkliste",
    "datei.repos": "repositorien-und-vorgaben",

    # ---- LIESMICH ----
    "l.titel": "Dokumentationspaket",
    "l.text": "Begleitdokumente zu einem Transkript, erzeugt aus den Werten, die die App kennt. Das Paket enthält weder Transkript noch Aufnahme.",
    "l.wofuer": "Wofür",
    "l.zeilen": "{methoden}/{protokoll} :: Wie das Transkript entstand und wie stark es von Hand bearbeitet wurde. Gehört zur Datendokumentation.\n"
                "{methoden}/{absatz} :: Absatz für den Methodenteil, kurz und ausführlich.\n"
                "{datenschutz}/{tatsachen} :: Was die App tut und nicht tut. Für Verzeichnis der Bearbeitungstätigkeiten, Folgenabschätzung, Ethikantrag.\n"
                "{datenschutz}/{stelle} :: Was nur die verantwortliche Stelle weiss, als Formular.\n"
                "{ablage}/{datensatz} :: Felder für Zenodo und DataCite, einmal je Datensatz.\n"
                "{ablage}/{interview} :: Angaben zu diesem einen Interview.\n"
                "{ablage}/{ethik} :: Prüfpunkte vor einer Veröffentlichung.\n"
                "{ablage}/{repos} :: Welches Repositorium, welche Formate, welche Vorgaben.\n"
                "{zitieren}/researchtranscript.bib :: Software und Modelle als Einträge für Zotero (Datei › Importieren).",
    "l.vorher": "Vor der Weitergabe",
    "l.vorher.punkte": "Name des Transkripts, Quelldatei und Dateinamen in diesem Paket können Personen nennen. Vor der Weitergabe prüfen.\n"
                       "Die Tonaufnahme enthält die Stimme und ist ein Personendatum.\n"
                       "Pseudonymisiert ist nicht anonymisiert. Das Datenschutzrecht gilt weiter.\n"
                       "`ausgang.json`, `history/` und die Aufnahme enthalten den Wortlaut vor einer Pseudonymisierung.\n"
                       "Die Dokumente sind keine Rechtsberatung.",

    # ---- 1a Transkriptionsprotokoll ----
    "p.titel": "Transkriptionsprotokoll",
    "p.einleitung": "Das Protokoll hält fest, wie dieses Transkript entstand und wie stark es von Hand bearbeitet wurde. Die Angaben stammen aus dem Transkript und seinem Journal.",
    "p.transkript": "Transkript", "p.maschine": "Maschinelle Transkription", "p.hand": "Bearbeitung von Hand",
    "p.eingriff": "Eingriff gegenüber dem maschinellen Transkript", "p.dateien": "Dateien",
    "p.software": "Software und Modelle",
    "f.name": "Name in der Bibliothek", "f.quelldatei": "Quelldatei", "f.dauer": "Dauer des Transkripts",
    "f.sprache": "Sprache (Einstellung)", "f.segmente": "Segmente", "f.sprecher": "Sprecher in der Endfassung",
    "f.memos": "Memos", "f.zotero": "Zotero", "zotero.ja": "verknüpft", "zotero.nein": "nicht verknüpft",
    "f.datum": "Datum des Laufs", "f.app": "App", "f.erkennung": "Spracherkennung",
    "f.vad": "Sprachaktivitätserkennung", "f.trennung": "Sprechertrennung", "f.ort": "Ort der Verarbeitung",
    "app.vorgaenger": "{name} {version} (Vorgängername von ResearchTranscript; die Zählung begann mit 0.4.0 neu)",
    "erkennung.wert": "whisper.cpp {whisper}, Modell `{modell}` ({herkunft})",
    "erkennung.alt": "whisper.cpp, Modell `{modell}`; Programmversion beim Lauf nicht aufgezeichnet",
    "modell.mitgeliefert": "mit der App geliefert", "modell.eigen": "eigenes Modell der Forschenden",
    "modell.unbekannt": "Herkunft nicht aufgezeichnet",
    "vad.an": "Silero VAD {silero} in whisper.cpp", "vad.aus": "nicht verwendet",
    "vad.diar": "nicht verwendet; die Sprechertrennung schneidet die Blöcke",
    "diar.aus": "ausgeschaltet",
    "diar.an": "SpeakerKit (Argmax); Modelle pyannote segmentation-3.0, WeSpeaker ResNet34 und pyannote community-1, von Argmax nach Core ML umgewandelt. Sprecherzahl: {zahl}",
    "diar.auto": "automatisch", "diar.schwelle": "Schwelle der Gruppierung {wert}",
    "ort.neu": "lokal auf dem Mac; Spracherkennung in einem Hilfsprogramm aus dem App-Paket",
    "ort.alt": "lokal auf dem Mac",
    "p.importiert": "Dieses Transkript wurde importiert aus `{datei}`, nicht in der App transkribiert. Der Ausgangsstand ist die Datei, wie sie kam.",
    "f.sitzungen": "Bearbeitungssitzungen", "f.zeitraum": "Zeitraum", "f.wer": "Bearbeitet von (Sitzungen)",
    "f.rolle": "Rolle der Bearbeitenden", "f.abgehoert": "Gegen die Aufnahme abgehört",
    "f.regeln": "Transkriptionsregeln", "f.pseudonym": "Pseudonymisierung",
    "sitzungen.text": "{n} (Speicherfolgen derselben Installation mit weniger als zehn Minuten Pause)",
    "wer.eintrag": "{wer} ({n})", "wer.install": "Installation {kennung}",
    "offen.rolle": "[ … ]", "offen.abgehoert": "[ vollständig / teilweise / nein ]",
    "offen.regeln": "[ … ] (z. B. Dresing & Pehl, einfach oder erweitert)",
    "offen.pseudonym": "[ … ] (was ersetzt wurde, nach welcher Regel)",
    "e.journal": "Laut Journal, je Segment",
    "e.journal.text": "Das Journal vermerkt je Sitzung, welche Segmente geändert wurden. Gezählt sind verschiedene Segmente; hat ein Segment in einer Sitzung mehrere Änderungen, gilt die letzte. Die Anteile sind darum Mindestwerte.",
    "e.j.text": "Wortlaut geändert", "e.j.sprecher": "Sprecher neu zugeordnet", "e.j.zeit": "Zeit geändert",
    "e.j.summe": "Segmente mit mindestens einer Änderung",
    "e.j.weitere": "Ausserdem: {neu} Einträge neu angelegt, {weg} entfernt, {name} Sprecher umbenannt.",
    "e.wort": "Gegen den maschinellen Ausgangsstand, je Wort",
    "e.wort.fehlt": "Eine Rate je Wort ist für dieses Transkript nicht berechenbar. Es entstand mit einer Version, die den maschinellen Rohstand noch nicht aufbewahrte.",
    "e.wort.verlauf": "Der Ausgangsstand stammt aus dem ältesten unbearbeiteten Stand im Verlauf.",
    "mass.kopf": "Mass", "mass.basis": "Grundlage",
    "mass.norm": "Korrekturrate, normalisiert", "mass.orth": "Korrekturrate, orthografisch",
    "mass.sdi": "{s} ersetzt, {d} gelöscht, {i} eingefügt; {n} Wörter in der Endfassung",
    "mass.sprechzeit": "Neu zugeordnete Sprechzeit",
    "mass.sprechzeit.basis": "gemeinsam belegte Sprechzeit {zeit}; {a} Sprecher im Ausgangsstand, {b} in der Endfassung",
    "mass.mehrheit": "davon ohne zusammengeführte Sprecher",
    "mass.mehrheit.text": "das Zusammenführen zweier Stimmen zählt hier nicht",
    "mass.ohne_maschine": "die Maschine hat keine Sprecher vergeben",
    "mass.definition": "Korrekturrate = (ersetzte + gelöschte + eingefügte Wörter) ÷ Wörter der Endfassung. Gezählt wird wie bei der Wortfehlerrate, mit der Endfassung als Referenz, ausgerichtet je Segment. *Normalisiert*: klein geschrieben, ohne Satz- und Sonderzeichen. *Orthografisch*: wie geschrieben. Neu zugeordnete Sprechzeit = Anteil der von beiden Ständen belegten Sprechzeit mit anderem Sprecher, bei bestmöglicher Eins-zu-eins-Zuordnung.",
    "mass.vorbehalt": "Eingriffsmass, kein Genauigkeitsmass. Es zählt jede Änderung von Hand, auch Pseudonymisierung und Glättung. Unbemerkte Fehler erfasst es nicht.",
    "dateien.text": "Dateien im Ordner des Transkripts, mit SHA-256.",
    "dateien.ausgang": "`ausgang.json` ist der unveränderte Ausgangsstand. Er enthält den Wortlaut vor einer Pseudonymisierung.",
    "software.punkte": "whisper.cpp (MIT): <https://github.com/ggml-org/whisper.cpp>\n"
                       "Whisper large-v3-turbo (OpenAI, MIT): <https://huggingface.co/openai/whisper-large-v3-turbo>\n"
                       "SpeakerKit, Argmax OSS (MIT): <https://github.com/argmaxinc/argmax-oss-swift>\n"
                       "pyannote speaker-diarization-community-1 (CC BY 4.0): <https://huggingface.co/pyannote/speaker-diarization-community-1>\n"
                       "Silero VAD (MIT): <https://github.com/snakers4/silero-vad>\n"
                       "ResearchTranscript (AGPL-3.0-or-later): <https://github.com/bias-city/ResearchTranscript>",

    # ---- 1b Methodenabsatz ----
    "a.titel": "Absatz für den Methodenteil",
    "a.einleitung": "Zum Übernehmen und Anpassen. Eckige Klammern sind zu ersetzen. Der Absatz gilt für dieses eine Transkript.",
    "a.kurz": "Kurzfassung", "a.lang": "Ausführlich, für Anhang oder Datenmanagementplan",
    "a.app.neu": "ResearchTranscript {version}", "a.app.alt": "{name} {version} (heute ResearchTranscript)",
    "a.s1": "Die Aufnahme (Dauer {dauer}) wurde mit {app} lokal [ auf einem Rechner der Forschungsgruppe ] transkribiert; die App überträgt dabei keine Daten.",
    "a.s2": "Die Spracherkennung nutzte whisper.cpp mit dem Modell {modell}.",
    "a.s3": "Die Sprecher trennte SpeakerKit mit pyannote-Modellen.",
    "a.s4": "Das Rohtranskript wurde von [ wem ] [ vollständig / stichprobenweise ] gegen die Aufnahme geprüft und nach [ Transkriptionsregeln ] korrigiert [ und im Text pseudonymisiert ].",
    "a.s5.wort": "Die Korrekturrate auf Wortebene betrug {norm} (normalisiert, Endfassung als Referenz){sprechzeit}.",
    "a.s5.sprechzeit": "; von Hand neu zugeordnet wurden {wert} der Sprechzeit",
    "a.s5.journal": "Laut Journal wurde in mindestens {text} der Segmente der Wortlaut geändert und in {sprecher} der Sprecher neu zugeordnet.",
    "a.s6": "Die Werte messen den Eingriff, nicht die Genauigkeit.",
    "a.k1": "Die Aufnahme wurde mit {app} lokal transkribiert (whisper.cpp, Modell {modell}) und anschliessend von [ wem ] gegen die Aufnahme geprüft und korrigiert.",
    "a.offen": "Noch zu ergänzen",
    "a.offen.punkte": "Wer korrigiert hat und ob vollständig abgehört wurde.\n"
                      "Nach welchen Transkriptionsregeln gearbeitet wurde.\n"
                      "Was pseudonymisiert wurde und nach welcher Regel.",
    "a.zitieren": "Zitieren",
    "a.zitieren.text": "Pohl, B. ({jahr}). ResearchTranscript (Version {v}) [Software]. B/IAS – Basel Institut für angewandte Stadtforschung. <https://bias.city/researchtranscript/> Die Datei `researchtranscript.bib` im Ordner `{zitieren}` enthält diesen Eintrag und die Modelle für Zotero.",

    # ---- 2a App-Tatsachen ----
    "t.titel": "ResearchTranscript: Tatsachen für Datenschutz und Ethikantrag",
    "t.einleitung": "Tatsachen über die App, zum Übernehmen in ein Verzeichnis der Bearbeitungstätigkeiten, eine Folgenabschätzung oder einen Ethikantrag. Für alle Transkripte gleich. Gilt für ResearchTranscript {v}; wie ein älterer Lauf entstand, steht im Transkriptionsprotokoll.",
    "t.schritte": "Was die App mit einer Aufnahme tut", "t.schritt": "Schritt", "t.werkzeug": "Werkzeug", "t.wo": "Wo",
    "t.schritte.zeilen": "Tonspur lesen, nach 16 kHz mono wandeln :: macOS AVFoundation :: lokal, in der App\n"
                         "Sprechertrennung, abschaltbar :: SpeakerKit (Argmax) mit pyannote- und WeSpeaker-Modellen, Core ML :: lokal, in der App\n"
                         "Spracherkennung :: whisper.cpp {whisper}, Modell nach Wahl; ohne Sprechertrennung mit Silero VAD {silero} :: lokal, Hilfsprogramm aus dem App-Paket, Grafikeinheit\n"
                         "Korrektur im Editor, mit Verlauf und Journal :: ResearchTranscript :: lokal\n"
                         "Export in Text-, Tabellen- und Archivformate; MP3 über LAME :: ResearchTranscript :: lokal, in den gewählten Ordner",
    "t.schutz": "Schutzmassnahmen, die die App bietet",
    "t.schutz.punkte": "App Sandbox von macOS: Zugriff nur auf Ordner, die die Person im Dialog wählt, und auf hineingezogene Dateien.\n"
                       "Kein Server, kein offener Port, kein Konto.\n"
                       "Speichern in einem Schritt; vor jedem Speichern ein Stand im Verlauf (30 Stände).\n"
                       "Löschen verschiebt in den Papierkorb der Bibliothek, nichts geht sofort verloren.\n"
                       "Journal je Transkript: wer (Kennung der Installation, freiwillig E-Mail) wann was geändert hat.\n"
                       "Zotero wird nur gelesen, nur nach Freischaltung.\n"
                       "Quellcode offen, App signiert.",
    "t.nicht": "Was die App nicht tut",
    "t.nicht.punkte": "Sie überträgt keine Aufnahmen, Texte oder Nutzungsdaten: keine Telemetrie, keine Update-Prüfung, keine eigenen Absturzberichte. Die Netzberechtigung von macOS ist gesetzt, weil die eingebaute Web-Ansicht sie verlangt; eine Firewall zeigt, dass keine Verbindung entsteht. Absturzberichte von macOS folgen den Systemeinstellungen.\n"
                      "Sie lädt weder Modelle noch Programmteile nach.\n"
                      "Die Modelle lernen nicht aus den Aufnahmen.\n"
                      "Sie fasst nichts zusammen und formuliert nichts um. Die Spracherkennung ist ein KI-Modell und kann Wörter setzen, die nicht gesagt wurden; darum wird gegen die Aufnahme geprüft.",
    "t.ablage": "Wo Daten liegen",
    "t.ablage.punkte": "Im gewählten Bibliotheksordner, je Transkript ein Unterordner: `transkript.json` (Wortlaut, Sprecher, Memos, Journal, Zotero-Angaben), eine Kopie der Aufnahme, bei Video die Videodatei, `wellenform.json`.\n"
                       "`ausgang.json` hält den Stand fest, wie ihn die Maschine oder eine importierte Datei lieferte. `history/` hält die letzten 30 Stände. Beide enthalten den Wortlaut vor einer Pseudonymisierung.\n"
                       "Gelöschte Transkripte bleiben im Ordner `_papierkorb`, bis er im Finder geleert wird.\n"
                       "Während eines Laufs liegen Arbeitskopien des Tons im temporären Ordner der App.\n"
                       "Einstellungen und App-Protokoll liegen im App-Container des Benutzerkontos. Das Protokoll enthält Zeitstempel, Befehle, Ordner- und Dateinamen sowie Fehlermeldungen.",
    "t.person": "Was die App über Forschende speichert",
    "t.person.punkte": "Eine zufällige Kennung der Installation, ohne Bezug zu Gerät oder Person.\n"
                       "Freiwillig eine E-Mail-Adresse. Beide stehen im Journal jedes Transkripts und gehen mit dem enrich-Dossier mit.",
    "t.export": "Was Exporte enthalten",
    "t.export.punkte": "Alle Textformate (VTT, CSV, TXT, Markdown, Word): Wortlaut, Sprechernamen, Zeitmarken. CSV, Markdown und Word zusätzlich die Memos.\n"
                       "Markdown und Word: bei Zotero-Verknüpfung ein Kopf mit Titel, Datum, Citekey und den Personen, deren Rollen gewählt wurden.\n"
                       "REFI-QDA (`.qdpx.zip`): Text, Memos und die Tonaufnahme, also die Stimme; auf Wunsch die Videodatei.\n"
                       "enrich-Dossier (`.enrich`): Text, Tonaufnahme als MP3, Journal mit Kennung und E-Mail, Zotero-Angaben. Keine Memos.",

    # ---- 2b Angaben der Stelle ----
    "s.titel": "Angaben der verantwortlichen Stelle",
    "s.einleitung": "Diese Angaben kann die App nicht kennen. Ohne sie ist ein Eintrag im Verzeichnis der Bearbeitungstätigkeiten unvollständig.",
    "s.felder": "Verantwortliche Stelle :: Institution, Projektleitung, Kontakt\n"
                "Datenschutzberatung :: zuständige Person oder Stelle\n"
                "Zweck :: Forschungsprojekt, Fragestellung\n"
                "Rechtsgrundlage, anwendbares Recht :: je nach Träger kantonales Recht, Bundesrecht oder DSGVO\n"
                "Betroffene Personen :: Befragte, erwähnte Dritte, die Forschenden selbst (Journal)\n"
                "Kategorien von Personendaten :: Stimme, Aussagen, gegebenenfalls besonders schützenswerte Daten\n"
                "Empfänger :: wer Aufnahmen, Transkripte oder Exporte erhält\n"
                "Bekanntgabe ins Ausland :: durch die App keine; durch Weitergabe oder Cloud-Ablage möglich\n"
                "Aufbewahrung und Löschung :: Fristen, auch für Papierkorb, Verlauf, Ausgangsstand, Backups\n"
                "Speicherort der Bibliothek :: interne Platte, verschlüsseltes Laufwerk, Netzlaufwerk\n"
                "Backup und Synchronisation :: Time Machine, iCloud Drive und andere erfassen den Ordner, wenn er dort liegt\n"
                "Geräteschutz :: FileVault, Bildschirmsperre, getrennte Benutzerkonten\n"
                "Zugriffsberechtigte :: wer am Rechner und am Ordner arbeitet\n"
                "Information und Einwilligung :: deckt sie Aufnahme, Transkription, Aufbewahrung, Weitergabe",
    "s.achten": "Worauf zu achten ist",
    "s.achten.punkte": "«Lokal» ist eine Eigenschaft der App, nicht des Speicherorts. Ein synchronisierter Ordner überträgt die Daten.\n"
                       "Pseudonymisiert wird der Text der Endfassung. Aufnahme, Ausgangsstand und Verlauf enthalten weiter Stimme und Klarnamen.\n"
                       "Eigene Modelle der Forschenden gehören nicht zur dokumentierten Liste der App.",
    "s.entfernen": "Ein Interview vollständig entfernen",
    "s.entfernen.text": "Zum Beispiel nach einem Widerruf. Die App löscht nichts endgültig; diese Orte sind einzeln zu prüfen.",
    "s.entfernen.punkte": "Transkript in der App löschen, dann den Ordner `_papierkorb` der Bibliothek im Finder leeren und den Papierkorb von macOS.\n"
                          "Exporte an allen Orten, an die sie gespeichert oder weitergegeben wurden.\n"
                          "Backups und synchronisierte Kopien des Bibliotheksordners.\n"
                          "Die Originalaufnahme ausserhalb der Bibliothek.\n"
                          "Wer nur den Wortlaut vor der Pseudonymisierung entfernen will, löscht `ausgang.json` und `history/`. Danach ist kein Eingriffsmass je Wort mehr berechenbar.",

    # ---- 3 Datenablage ----
    "r.status": "Status", "r.st.pflicht": "Pflicht", "r.st.empfohlen": "empfohlen", "r.st.optional": "optional",
    "r.vorschlag": "Vorschlag aus Zotero, prüfen",
    "d.titel": "Datenblatt: Angaben zum Datensatz",
    "d.einleitung": "Einmal je Datensatz auszufüllen, auch wenn er mehrere Interviews umfasst. Reihenfolge und Feldnamen folgen dem Formular von Zenodo; der Status nennt Zenodo und DataCite 4.",
    "d.zeilen": "Resource type :: pflicht :: Dataset :: Transkripte samt Dokumentation.\n"
                "Title :: pflicht :: [ … ] :: Beschreibend, ohne Namen von Befragten.\n"
                "Publication date :: pflicht :: [ … ] :: Datum der Veröffentlichung, nicht des Interviews.\n"
                "Creators :: pflicht :: {creators} :: Die Forschenden mit ORCID und Institution. Nie die Befragten.\n"
                "Description :: empfohlen :: [ … ] :: Worum es geht, wer befragt wurde (allgemein gehalten), wozu.\n"
                "Licence :: pflicht :: [ … ] :: Bei Zenodo Pflicht für offene Dateien. Für sensible Dateien ein Nutzungsvertrag statt einer offenen Lizenz.\n"
                "Access :: pflicht :: [ … ] :: Gilt bei Zenodo je Eintrag. Offene Dokumentation und gesperrte Transkripte als getrennte, verknüpfte Einträge.\n"
                "Contributors :: empfohlen :: [ … ] :: Rollen nach DataCite, z. B. ContactPerson, DataCollector, RightsHolder.\n"
                "Keywords :: empfohlen :: [ … ] :: Drei bis acht Begriffe, möglichst aus einem Fachvokabular.\n"
                "Languages :: optional :: {sprachen} :: ISO-Code der Interviewsprache.\n"
                "Dates (Collected) :: empfohlen :: [ … ] :: Erhebungszeitraum. Im Zweifel nur das Jahr.\n"
                "Version :: optional :: 1.0 :: Nach Korrekturen eine neue Version.\n"
                "Funding :: optional :: [ … ] :: Geldgeber und Nummer der Bewilligung.\n"
                "Related works :: empfohlen :: {dois} :: DOI der Artikel, die auf den Daten beruhen.",
    "d.befragte": "Personen der befragten Seite aus Zotero sind bewusst nicht aufgeführt.",
    "d.archiv": "Facharchive fragen zusätzlich",
    "d.archiv.punkte": "Erhebungsmethode, z. B. leitfadengestütztes Interview.\n"
                       "Grundgesamtheit und Auswahl der Befragten.\n"
                       "Begleitmaterial: Leitfaden, Informationsblatt, Einwilligungsvorlage, Methodenbericht.",
    "i.titel": "Datenblatt: Angaben zu diesem Interview",
    "i.einleitung": "Was die App über dieses eine Interview weiss, und was für die Ablage dazu gehört.",
    "i.umfang": "Umfang", "i.umfang.wert": "Dauer {dauer}, {segmente} Segmente, {sprecher} Sprecher",
    "i.sprache": "Sprache", "i.jahr": "Erhebungsjahr", "i.verfahren": "Transkriptionsverfahren",
    "i.verfahren.wert": "{app}, whisper.cpp, Modell {modell}; lokal; von Hand bearbeitet (siehe Transkriptionsprotokoll)",
    "i.konventionen": "Transkriptionskonventionen",
    "i.konventionen.wert": "Zeitmarken hh:mm:ss je Äusserung, Sprecher als eigene Angabe; [ Regeln ergänzen ]",
    "i.pseudonym": "Pseudonymisierung", "i.pseudonym.wert": "[ … ] (die Schlüsselliste wird nie abgelegt)",
    "i.formate": "Dateien für die Ablage",
    "i.formate.punkte": "Transkript in einem offenen Textformat (TXT, Markdown, CSV), zusätzlich zu Word und REFI-QDA. Prüfsummen nach dem Export bilden.\n"
                        "REFI-QDA ist ein Austauschformat mit möglichem Verlust zwischen Programmen, kein alleiniges Archivformat.\n"
                        "Als Archivfassung der Aufnahme dient die Originaldatei, nicht umkodiert. Die MP3 in den Paketen der App ist eine Nutzungskopie.\n"
                        "Der Kopf im Markdown- und Word-Export nennt die in Zotero gewählten Personen. Vor der Ablage prüfen.\n"
                        "Das Transkriptionsprotokoll kann beiliegen. `ausgang.json` und `history/` bleiben draussen.",
    "e.titel": "Prüfpunkte vor einer Veröffentlichung",
    "e.einleitung": "Nur die Forschenden können diese Punkte beantworten. Was nicht zutrifft, wird so vermerkt.",
    "e.punkt": "Prüfpunkt", "e.ja": "erfüllt", "e.nz": "trifft nicht zu",
    "e.punkte": "Die Einwilligung deckt Archivierung und Nachnutzung. :: Sonst Rücksprache mit Ethikkommission oder Datenschutzberatung.\n"
                "Die Einwilligung deckt die Weitergabe der Tonaufnahme. :: Die Stimme ist ein Personendatum.\n"
                "Ein Ethikvotum liegt vor. :: Nummer und Stelle angeben.\n"
                "Direkte und indirekte Merkmale sowie erwähnte Dritte sind geprüft. :: Kombinationen wie Beruf, Ort und Alter beachten.\n"
                "Titel, Beschreibung, Schlagworte und Dateinamen nennen keine Personen. :: Metadaten sind bei Zenodo immer öffentlich.\n"
                "Die Schlüsselliste der Pseudonyme liegt getrennt. :: Sie gehört nie in die Ablage.\n"
                "Das Repositorium passt zu den Daten. :: Für sensible Daten ein Facharchiv mit Zugangskontrolle.\n"
                "Vorgaben von Förderer und Hochschule sind geprüft. :: Ausnahmen vom offenen Zugang im Datenmanagementplan begründen.",
    "o.titel": "Repositorien, Formate, Vorgaben",
    "o.einleitung": "Für alle Transkripte gleich. Die Angaben ersetzen nicht die Beratung durch das Archiv.",
    "o.zenodo": "Was Zenodo verlangt",
    "o.zenodo.punkte": "Sensible Personendaten müssen vor offener Verbreitung angemessen anonymisiert oder durch Einwilligung gedeckt sein. Für nicht anonymisierte sensible Daten verweist Zenodo auf Fachplattformen. Verantwortlich ist die Person, die hochlädt.\n"
                       "Metadaten sind immer öffentlich, auch bei gesperrten Dateien.\n"
                       "Ein veröffentlichter DOI-Eintrag lässt sich nicht spurlos löschen.\n"
                       "Grenzen: 50 GB und 100 Dateien je Eintrag.",
    "o.repos": "Repositorien", "o.repo": "Repositorium", "o.fuer": "Eignung",
    "o.repos.zeilen": "Zenodo :: Allgemein, DOI sofort. Für Dokumentation, Instrumente und wirklich anonymisierte Texte, nicht für Aufnahmen. :: https://zenodo.org\n"
                      "SWISSUbase :: Schweiz. Nimmt qualitative und sensible Daten, mit Zugangskontrolle und Nutzungsvertrag. DOI. :: https://www.swissubase.ch\n"
                      "Qualiservice :: Deutschland, qualitative Daten. Beratung, Hilfe bei der Anonymisierung, Zugang auf Antrag. DOI. :: https://www.qualiservice.org\n"
                      "AUSSDA :: Österreich, Sozialwissenschaften. Eigene Richtlinie für qualitative Daten. :: https://aussda.at\n"
                      "UK Data Service :: Vereinigtes Königreich. Gestufter Zugang. :: https://ukdataservice.ac.uk",
    "o.vorgaben": "Vorgaben und Anleitungen",
    "o.vorgaben.punkte": "Zenodo, Felder: <https://help.zenodo.org/docs/deposit/describe-records/>\n"
                         "Zenodo, Richtlinien und Bedingungen: <https://about.zenodo.org/policies/> · <https://about.zenodo.org/terms/>\n"
                         "DataCite Metadata Schema 4: <https://schema.datacite.org>\n"
                         "SWISSUbase und FORS, Daten ablegen: <https://forscenter.ch/deposit-data/>\n"
                         "FORS Guide Nr. 20, Anonymisierung qualitativer Daten: <https://doi.org/10.24449/FG-2023-00020>\n"
                         "Qualiservice, Daten teilen: <https://www.qualiservice.org/de/daten-teilen.html>\n"
                         "CESSDA Data Management Expert Guide: <https://dmeg.cessda.eu>\n"
                         "SNF, Open Research Data: <https://www.snf.ch/de/FAiWVH4WvpKvohw9/thema/forschungsdaten>\n"
                         "DFG, Umgang mit Forschungsdaten: <https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/forschungsdaten>\n"
                         "README-Vorlage der Cornell University (CC0): <https://data.research.cornell.edu/data-management/sharing/readme/>",
}
