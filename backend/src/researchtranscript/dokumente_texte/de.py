"""Texte der Begleitdokumente — Deutsch (Quellsprache).

Schlüssel und Platzhalter `{…}` sind in allen Sprachen gleich. Mehrzeilige
Werte sind Listen: EIN Punkt je Zeile; «Feld :: Hinweis» trennt Spalten.
Sachform, keine Anrede. Offene Felder heissen `[ … ]`.
"""

T = {
    # ---- allgemein ----
    "feld": "Feld", "wert": "Wert", "datei": "Datei", "groesse": "Grösse", "nachweise": "Nachweise",
    "nicht_aufgezeichnet": "nicht aufgezeichnet", "dezimal": ",",
    "kopf.erzeugt": "Erzeugt von ResearchTranscript {v} am {datum}. Offene Felder sind mit `[ … ]` markiert "
                    "und von den Forschenden auszufüllen.",
    "modell.mitgeliefert": "mit der App geliefert", "modell.eigen": "eigenes Modell der Forschenden",
    "modell.unbekannt": "Herkunft nicht aufgezeichnet",
    "modell.heute": "— Herkunft nach heutigem Stand der Installation, beim Lauf nicht aufgezeichnet",
    "diar.aus": "keine (ausgeschaltet)", "diar.an": "SpeakerKit (Argmax) mit pyannote community-1, Core ML",
    "diar.auto": "automatisch", "diar.zahl": "Sprecherzahl:", "diar.trennung": "Schwelle der Gruppierung",
    "vad.aus": "nicht verwendet", "ort.lokal": "lokal auf dem Mac, im Prozess der App; keine Übertragung durch die App",

    "f.kennung": "Kennung", "f.name": "Name in der Bibliothek", "f.quelldatei": "Quelldatei",
    "f.dauer": "Dauer", "f.sprache": "Sprache (Einstellung)", "f.segmente": "Segmente",
    "f.sprecher": "Sprecher (Zahl)", "f.memos": "Memos (Zahl)", "f.datum": "Datum des Laufs",
    "f.app": "Software", "f.erkennung": "Spracherkennung", "f.modell": "Modell", "f.modell.satz": "Modell",
    "f.vad": "Sprachaktivitätserkennung", "f.trennung": "Sprechertrennung", "f.ort": "Ort der Verarbeitung",
    "f.sitzungen": "Bearbeitungssitzungen laut Journal", "f.zeitraum": "Zeitraum der Bearbeitung",
    "f.journal": "Geänderte Einträge laut Journal", "f.wer": "Bearbeitet von",
    "f.abgehoert": "Gegen die Aufnahme abgehört", "f.regeln": "Transkriptionsregeln",
    "f.pseudonym": "Pseudonymisierung",
    "journal.arten": "Text {text} · Sprecherzuordnung {sprecher} · Zeit {zeit} · neu {neu} · entfernt {weg} · "
                     "Sprecher umbenannt {name}",
    "offen.wer": "[ … ] (Name oder Rolle; die App zeichnet das nicht auf)",
    "offen.abgehoert": "[ vollständig / teilweise / nein ]",
    "offen.regeln": "[ … ] (z. B. Dresing & Pehl, einfach oder erweitert; eigene Regeln)",
    "offen.pseudonym": "[ … ] (was ersetzt wurde und nach welcher Regel; die Schlüsselliste wird getrennt aufbewahrt)",

    # ---- Dokumentationspaket ----
    "paket.ordner": "researchtranscript-dokumentation", "paket.liesmich": "LIESMICH",
    "paket.protokolle": "protokolle", "paket.titel": "Dokumentationspaket",
    "paket.text": "Begleitdokumente zu den gewählten Transkripten, jedes als Markdown und als Word-Datei. "
                  "Offene Felder `[ … ]` sind von den Forschenden auszufüllen. Das Paket enthält keine "
                  "Transkripte und keine Aufnahmen.",
    "paket.bib": "Zitierdatei für Zotero (Datei › Importieren): die Software und alle genannten Quellen",

    # ---- 1. Transkriptionsprotokoll ----
    "datei.protokoll": "transkriptionsprotokoll",
    "p.titel": "Transkriptionsprotokoll",
    "p.einleitung": "Dieses Protokoll hält fest, wie das Transkript entstand und wie stark es von Hand bearbeitet "
                    "wurde. Es gehört zur Dokumentation des einzelnen Datenobjekts und kann dem Datenpaket "
                    "beiliegen. Die Angaben stammen aus dem Journal des Transkripts; das Protokoll nennt keine "
                    "Namen von Sprechenden.",
    "p.aufnahme": "Aufnahme und Transkript", "p.maschine": "Maschinelle Transkription",
    "p.importiert": "Dieses Transkript wurde nicht in der App transkribiert, sondern importiert aus `{datei}`. "
                    "Der Ausgangsstand ist die Datei, wie sie kam.",
    "p.hand": "Bearbeitung von Hand", "p.mass": "Eingriffsmass", "p.dateien": "Dateien",
    "dateien.hinweis": "Dateien im Ordner des Transkripts mit Prüfsumme. `ausgang.json` ist der unveränderte "
                       "Ausgangsstand, an dem das Eingriffsmass gemessen wird.",

    "mass.kopf.mass": "Mass", "mass.kopf.basis": "Grundlage",
    "mass.norm": "Korrekturrate Wortebene, normalisiert",
    "mass.orth": "Korrekturrate Wortebene, orthografisch",
    "mass.sdi": "{s} ersetzt, {d} gelöscht, {i} eingefügt; {n} Wörter in der Endfassung",
    "mass.sprechzeit": "Neu zugeordnete Sprechzeit",
    "mass.sprechzeit.basis": "verglichene Sprechzeit {zeit}; {a} Sprecher im Ausgangsstand, {b} in der Endfassung",
    "mass.sprechzeit.mehrheit": "davon ohne zusammengeführte Sprecher",
    "mass.sprechzeit.mehrheit.text": "Zuordnung mehrerer Maschinen-Sprecher auf dieselbe Person erlaubt: "
                                     "das Zusammenführen zweier Stimmen zählt hier nicht",
    "mass.ohne_maschine": "die Maschine hat keine Sprecher vergeben; alle Zuordnungen stammen von Hand",
    "mass.fehlt": "Für dieses Transkript ist kein Ausgangsstand mehr vorhanden (angelegt vor Version 0.6.0, der "
                  "Verlauf reicht nicht mehr zurück). Eine Korrekturrate lässt sich nicht berechnen. Als "
                  "Anhaltspunkt: {n} von {gesamt} Segmenten ({anteil}) tragen den Vermerk «von Hand geändert».",
    "mass.aus_verlauf": "Der Ausgangsstand stammt aus dem ältesten Stand im Verlauf, den noch niemand bearbeitet hatte.",
    "mass.definition": "**Definitionen.** Korrekturrate = (ersetzte + gelöschte + eingefügte Wörter) ÷ Wörter der "
                       "Endfassung, berechnet wie die Wortfehlerrate (WER) mit der Endfassung als Referenz und "
                       "dem Ausgangsstand als Hypothese. *Normalisiert*: klein geschrieben, ohne Satz- und "
                       "Sonderzeichen, Umlaute und Akzente bleiben. *Orthografisch*: Wörter wie geschrieben, "
                       "Gross-/Kleinschreibung und Satzzeichen zählen. Neu zugeordnete Sprechzeit = Anteil der "
                       "Sprechzeit, deren Sprecher in der Endfassung ein anderer ist als im Ausgangsstand, bei "
                       "bestmöglicher Eins-zu-eins-Zuordnung der Sprecher; das entspricht der "
                       "Verwechslungskomponente der Diarization Error Rate, ohne Toleranzfenster. Verpasste oder "
                       "fälschlich erkannte Sprache wird nicht erfasst.",
    "mass.vorbehalt": "Eingriffsmass, kein Genauigkeitsmass. Die Rate enthält jede Änderung von Hand, auch "
                      "Pseudonymisierung, Glättung und Transkriptionsregeln. Fehler, die niemand bemerkt hat, "
                      "erfasst sie nicht. Sie beziffert, wie stark bearbeitet wurde — nicht, wie gut die Maschine "
                      "oder die Endfassung ist.",

    # ---- 2. Methodenbaustein ----
    "datei.methoden": "methodenbaustein-transkription",
    "m.titel": "Methodenbaustein: Transkription",
    "m.einleitung": "Ein Methodenteil beschreibt das Korpus, nicht das einzelne Interview. Dieser Baustein fasst die "
                    "gewählten Transkripte zusammen: Umfang, Verfahren und wie stark die maschinellen "
                    "Rohtranskripte von Hand bearbeitet wurden. Darunter steht ein Absatz zum Übernehmen und "
                    "eine Liste dessen, was nur die Forschenden wissen.",
    "m.korpus": "Korpus", "m.n": "Transkripte", "m.importiert": "davon {n} importiert, nicht in der App transkribiert",
    "m.gesamt": "Gesamtdauer", "m.mittel": "Dauer: Mittelwert (Spanne)",
    "m.eigen": "darunter ein eigenes Modell der Forschenden, nicht Teil der mit der App gelieferten Liste",
    "m.diar": "bei {n} von {gesamt} Transkripten (SpeakerKit, pyannote community-1)",
    "m.zeitraum": "Zeitraum der maschinellen Läufe",
    "m.mass": "Eingriffsmass über das Korpus",
    "m.mass.text": "Berechnet für {n} von {gesamt} Transkripten (für die übrigen ist kein Ausgangsstand vorhanden).",
    "m.median": "Median (Spanne)",
    "m.absatz": "Absatz für den Methodenteil",
    "m.absatz.hinweis": "Zum Übernehmen und Anpassen. Eckige Klammern sind zu ersetzen.",
    "m.absatz.text": "Die Aufnahmen (n = {n}; Gesamtdauer {gesamt}; Mittelwert {mittel}, Spanne {spanne}) wurden mit "
                     "ResearchTranscript {version} (B/IAS Basel, AGPL-3.0) vollständig lokal [ auf einem Rechner "
                     "der Forschungsgruppe ] transkribiert; die App übermittelt dabei nichts an externe Dienste. Die "
                     "Spracherkennung nutzte whisper.cpp {whisper} mit dem Modell {modell} (Radford et al., 2022)."
                     "{diar} Die Rohtranskripte wurden anschliessend von [ wem ] [ vollständig / stichprobenweise ] "
                     "gegen die Aufnahme geprüft, nach [ Transkriptionsregeln ] korrigiert [ und im Text "
                     "pseudonymisiert ]. Die Korrekturrate auf Wortebene (berechnet wie die Wortfehlerrate, "
                     "Endfassung als Referenz, normalisiert) betrug im Median {norm}. Die Rate misst den "
                     "Eingriff einschliesslich Pseudonymisierung, nicht die Genauigkeit.",
    "m.absatz.diar": " Die Sprecher wurden mit SpeakerKit und dem Modell pyannote community-1 getrennt (Plaquet & "
                     "Bredin, 2023); der Anteil von Hand neu zugeordneter Sprechzeit betrug im Median {sprechzeit}.",
    "m.offen": "Was nur die Forschenden wissen",
    "m.offen.wer": "Wer korrigiert hat, mit welcher Qualifikation, und ob vollständig gegen die Aufnahme abgehört wurde.",
    "m.offen.regeln": "Nach welchen Transkriptionsregeln gearbeitet wurde (Wortlaut, Glättung, Pausen, Dialekt).",
    "m.offen.pseudonym": "Was pseudonymisiert wurde und nach welcher Regel; wo die Schlüsselliste liegt.",
    "m.offen.einwilligung": "Ob die Einwilligung der Befragten die Art der Verarbeitung und eine spätere Weitergabe deckt.",
    "m.je": "Je Transkript",

    # ---- 3. Verfahrensbaustein ----
    "datei.verfahren": "verfahrensbaustein-researchtranscript",
    "v.titel": "Baustein für Verzeichnis der Bearbeitungstätigkeiten, Datenschutz-Folgenabschätzung und Ethikantrag",
    "v.einleitung": "Diese Dokumente beschreiben eine Bearbeitungstätigkeit oder ein Projekt, nicht die einzelne "
                    "Aufnahme. Der Baustein liefert dazu die Tatsachen über die App, so wie sie auf diesem Rechner "
                    "installiert ist. Alles, was nur die verantwortliche Stelle weiss, steht unten als offenes "
                    "Feld. Der Baustein ist keine Rechtsberatung und keine Aussage zur Rechtmässigkeit.",
    "v.schritte": "Was die App mit einer Aufnahme tut", "v.schritt": "Schritt", "v.werkzeug": "Werkzeug",
    "v.wo": "Wo",
    "v.s1.a": "Tonspur lesen und nach 16 kHz mono wandeln", "v.s1.b": "macOS AVFoundation",
    "v.s1.c": "lokal, im Prozess der App",
    "v.s2.a": "Sprachaktivität erkennen", "v.s2.b": "Silero VAD {silero} in whisper.cpp", "v.s2.c": "lokal",
    "v.s3.a": "Spracherkennung: Ton zu Text mit Zeitmarken",
    "v.s3.b": "whisper.cpp {whisper} (Hilfsprogramm im App-Paket), Modell nach Wahl",
    "v.s3.c": "lokal, Grafikeinheit (Metal)",
    "v.s4.a": "Sprechertrennung (abschaltbar)", "v.s4.b": "SpeakerKit (Argmax) mit pyannote community-1, Core ML",
    "v.s4.c": "lokal, Neural Engine",
    "v.s5.a": "Korrektur im Editor; Verlauf und Journal je Transkript", "v.s5.b": "ResearchTranscript",
    "v.s5.c": "lokal",
    "v.s6.a": "Export (VTT, CSV, TXT, Markdown, Word, REFI-QDA, enrich-Dossier; MP3 über LAME)",
    "v.s6.b": "ResearchTranscript", "v.s6.c": "lokal, in den Ordner, den die Person wählt",
    "v.modelle": "Zurzeit verfügbare Modelle der Spracherkennung auf diesem Rechner:", "v.herkunft": "Herkunft",
    "v.nicht": "Was die App nicht tut",
    "v.nicht.punkte": "Sie baut keine Netzverbindungen auf: kein Konto, keine Telemetrie, keine Update-Prüfung, keine eigenen Absturzberichte. Links (Datenschutzerklärung, Quellcode) öffnet sie nur auf Klick im Browser.\n"
                      "Sie lädt keine Modelle und keine Programmteile nach.\n"
                      "Sie betreibt keinen Server und keinen Netzwerkdienst; die Verarbeitung läuft im Prozess der App.\n"
                      "Sie läuft in der App Sandbox von macOS und liest nur Ordner, die die Person gewählt hat, und Dateien, die sie hineinzieht.\n"
                      "Sie enthält keine generative KI: nichts wird zusammengefasst, umformuliert oder gedeutet.\n"
                      "Sie liest Zotero nur nach ausdrücklicher Freischaltung und verändert es nie.",
    "v.ablage": "Wo Daten liegen",
    "v.ablage.punkte": "Im Bibliotheksordner, den die Person wählt; je Transkript ein Unterordner mit `transkript.json`, einer Kopie der Aufnahme (bei Video zusätzlich der Videodatei) und `wellenform.json`.\n"
                       "`ausgang.json` hält den unveränderten maschinellen Ausgangsstand fest, `history/` die letzten 30 Stände vor jedem Speichern. Beide enthalten den Wortlaut VOR einer Pseudonymisierung.\n"
                       "Gelöschte Transkripte liegen im Ordner `_papierkorb` der Bibliothek, bis er im Finder geleert wird.\n"
                       "Einstellungen und das Protokoll der App liegen im App-Container des Benutzerkontos; das Protokoll kann Dateinamen und Fehlermeldungen enthalten.\n"
                       "Wo der Bibliotheksordner liegt und ob er gesichert oder synchronisiert wird, weiss die App nicht.",
    "v.export": "Was Exporte enthalten",
    "v.export.punkte": "VTT, TXT: nur Text. CSV, Markdown, Word: Text und die Memos der Forschenden.\n"
                       "REFI-QDA (`.qdpx.zip`) und enrich-Dossier (`.enrich`): zusätzlich die Tonaufnahme, also die Stimme; mit Video auf Wunsch die Videodatei.\n"
                       "enrich-Dossier: ausserdem das Journal (mit der E-Mail-Adresse, falls in den Einstellungen hinterlegt) und verknüpfte Zotero-Metadaten.",
    "v.offen": "Von der verantwortlichen Stelle auszufüllen",
    "v.offen.text": "Die App kann diese Angaben nicht kennen. Ohne sie ist der Eintrag unvollständig.",
    "v.eintrag": "Eintrag", "v.hinweis": "Hinweis",
    "v.offen.felder": "Verantwortliche Stelle :: Institution, Projektleitung, Kontakt\n"
                      "Datenschutzberatung :: zuständige Person oder Stelle\n"
                      "Zweck der Bearbeitung :: Forschungsprojekt, Fragestellung\n"
                      "Rechtsgrundlage und anwendbares Recht :: je nach Träger kantonales Recht, Bundesrecht oder DSGVO; die App weiss das nicht\n"
                      "Betroffene Personen :: Befragte; im Gespräch erwähnte Dritte\n"
                      "Kategorien von Personendaten :: Stimme, Aussagen; gegebenenfalls besonders schützenswerte Daten\n"
                      "Empfänger :: wer Aufnahmen, Transkripte oder Exporte erhält\n"
                      "Bekanntgabe ins Ausland :: durch die App keine; durch Weitergabe von Exporten oder Cloud-Ablage möglich\n"
                      "Aufbewahrung und Löschung :: Fristen; auch für Papierkorb, Verlauf, Ausgangsstand und Backups\n"
                      "Speicherort des Bibliotheksordners :: interne Platte, verschlüsseltes Laufwerk, Netzlaufwerk\n"
                      "Backup und Synchronisation :: Time Machine, iCloud Drive, andere Dienste — sie erfassen den Ordner, wenn er dort liegt\n"
                      "Geräteschutz :: FileVault, Bildschirmsperre, getrennte Benutzerkonten\n"
                      "Zugriffsberechtigte :: wer am Rechner und am Ordner arbeiten darf\n"
                      "Information und Einwilligung der Befragten :: deckt sie Aufnahme, Transkription, Aufbewahrung, Weitergabe?",
    "v.warnung": "Worauf zu achten ist",
    "v.warnung.punkte": "Pseudonymisiert ist nicht anonymisiert: pseudonymisierte Daten bleiben Personendaten.\n"
                        "Pseudonymisiert wird der Text der Endfassung. Aufnahme, Ausgangsstand und Verlauf enthalten weiterhin Stimme und Klarnamen; wer sie nicht mehr braucht, löscht sie im Finder.\n"
                        "«Lokal» ist eine Eigenschaft der App, nicht des Speicherorts: ein synchronisierter Ordner überträgt die Daten.\n"
                        "Eigene Modelle der Forschenden sind nicht Teil der mit der App gelieferten und dokumentierten Liste.",

    # ---- 4. Repositoriums-Datenblatt ----
    "datei.repositorium": "repositoriums-datenblatt",
    "r.dok": "Repositoriums-Datenblatt",
    "r.einleitung": "Vorbereitung für die Ablage von {n} Transkript(en) als Forschungsdaten mit DOI. Die Felder folgen "
                    "DataCite 4 und dem Formular von Zenodo, ergänzt um das, was Facharchive für qualitative Daten "
                    "verlangen. Was die App aus Zotero und den Transkripten kennt, ist eingetragen und als "
                    "Vorschlag markiert; alles andere ist offen. Das Blatt ersetzt weder die Beratung durch das "
                    "Archiv noch eine Rechtsberatung.",
    "r.warnung": "Zuerst lesen",
    "r.warnung.punkte": "Die Tonaufnahme enthält die Stimme und ist ein Personendatum. Sie wird nicht offen veröffentlicht, auch nicht mit Pseudonym.\n"
                        "Pseudonymisiert heisst nicht anonym; das Datenschutzrecht gilt weiter.\n"
                        "Zenodo verlangt in seinen Nutzungsbedingungen, dass sensible Personendaten vor offener Verbreitung angemessen anonymisiert oder durch Einwilligung gedeckt sind, und verweist für nicht anonymisierte sensible Daten auf Fachplattformen. Die Verantwortung liegt bei der Person, die hochlädt.\n"
                        "Metadaten (Titel, Beschreibung, Schlagworte, Dateinamen) sind immer öffentlich, auch wenn die Dateien gesperrt sind. Sie dürfen keine Personendaten enthalten.\n"
                        "Ein veröffentlichter DOI-Eintrag lässt sich nicht spurlos löschen.\n"
                        "Befragte erscheinen nie als Urheber. Die App schlägt aus Zotero nur Personen vor, die nicht zur befragten Seite gehören; jeder Vorschlag ist zu prüfen.\n"
                        "Das Transkript ist maschinell erzeugt und von Hand bearbeitet; der Korrekturstand gehört in die Dokumentation (Transkriptionsprotokoll, Methodenbaustein).",
    "r.status": "Status", "r.erlaeuterung": "Erläuterung", "r.vorschlag": "Vorschlag, prüfen",
    "r.st.pflicht": "Pflicht", "r.st.empfohlen": "empfohlen", "r.st.optional": "optional",
    "r.st.archiv": "von Facharchiven verlangt",
    "r.befragte_weg": "(Personen der befragten Seite aus Zotero sind bewusst nicht aufgeführt.)",
    "r.g.beschreibung": "Beschreibung", "r.g.personen": "Personen und Rollen", "r.g.rechte": "Rechte und Zugang",
    "r.g.methode": "Inhalt und Methode", "r.g.dateien": "Dateien", "r.g.ethik": "Ethik und Datenschutz",
    "r.titel": "Titel des Datensatzes", "r.titel.e": "Beschreibend, ohne Namen von Befragten.",
    "r.typ": "Ressourcentyp", "r.typ.e": "Ein Paket aus Transkripten und Dokumentation gilt als Dataset.",
    "r.pubdatum": "Publikationsdatum", "r.pubdatum.e": "Datum der Veröffentlichung im Repositorium, nicht des Interviews.",
    "r.abstract": "Beschreibung", "r.abstract.e": "Worum es geht, wer befragt wurde (allgemein gehalten) und wozu.",
    "r.schlagworte": "Schlagworte", "r.schlagworte.e": "Drei bis acht Begriffe, möglichst aus einem Fachvokabular.",
    "r.sprache": "Sprache(n)", "r.sprache.e": "Sprache der Interviews als ISO-Code.",
    "r.erhebung": "Erhebungszeitraum", "r.erhebung.e": "Im Zweifel nur Jahr oder Monat: ein genaues Datum kann Personen erkennbar machen.",
    "r.ort": "Ort oder Region", "r.ort.e": "Nur so genau, dass niemand erkennbar wird.",
    "r.version": "Version", "r.version.e": "Nach Korrekturen eine neue Version anlegen.",
    "r.publisher": "Repositorium", "r.publisher.e": "Name des gewählten Repositoriums (bei Zenodo automatisch).",
    "r.verwandt": "Verwandte Publikationen", "r.verwandt.e": "DOI der Artikel, die auf den Daten beruhen.",
    "r.foerderung": "Förderung", "r.foerderung.e": "Geldgeber und Nummer der Bewilligung; SNF und DFG erwarten die Angabe.",
    "r.creators": "Urheber:innen (Creators)", "r.creators.e": "Die Forschenden, die den Datensatz verantworten, mit ORCID und Institution. Nie die Befragten.",
    "r.contributors": "Mitwirkende mit Rolle", "r.contributors.e": "z. B. DataCollector, ProjectLeader, Supervisor (Rollen nach DataCite).",
    "r.kontakt": "Kontaktperson", "r.kontakt.e": "Wer Zugriffsanfragen auch in einigen Jahren beantwortet.",
    "r.rechteinhaber": "Rechteinhaber", "r.rechteinhaber.e": "Meist die Hochschule oder die Forschenden.",
    "r.lizenz": "Lizenz", "r.lizenz.e": "Für offene Dateien Pflicht, z. B. CC BY 4.0 für die Dokumentation; für sensible Dateien ein Nutzungsvertrag statt einer offenen Lizenz.",
    "r.zugang": "Zugangsstufe je Datei", "r.zugang.e": "Offen, eingeschränkt oder gesperrt — getrennt für Dokumentation, Transkript und Aufnahme.",
    "r.embargo": "Embargo bis", "r.embargo.e": "Aufschub mit Begründung, z. B. bis zur Publikation.",
    "r.bedingungen": "Bedingungen für Zugriffsanfragen", "r.bedingungen.e": "Wer unter welchen Auflagen Zugriff erhält.",
    "r.methode": "Erhebungsmethode", "r.methode.e": "z. B. leitfadengestütztes Interview, vor Ort oder online.",
    "r.sampling": "Auswahl der Befragten", "r.sampling.e": "Grundgesamtheit und wie ausgewählt wurde.",
    "r.umfang": "Umfang", "r.umfang.e": "Technische Eckdaten aus den Transkripten.",
    "r.umfang.wert": "{n} Interview(s), Gesamtdauer {dauer}",
    "r.technik": "Transkriptionsverfahren", "r.technik.e": "Maschinell erzeugt, von Hand bearbeitet; Korrekturstand aus dem Methodenbaustein ergänzen.",
    "r.technik.wert": "ResearchTranscript {version}, whisper.cpp {whisper}, Modell {modell}; lokal",
    "r.konventionen": "Transkriptionskonventionen", "r.konventionen.e": "Notation für Pausen, Überlappungen, Unverständliches; hier ergänzen, was über das Format hinausgeht.",
    "r.konventionen.wert": "Zeitmarken hh:mm:ss je Äusserung, Sprecher als eigene Angabe; [ Regeln ergänzen ]",
    "r.anonymisierung": "Anonymisierung", "r.anonymisierung.e": "Was ersetzt wurde und wie; die Schlüsselliste selbst wird nie abgelegt.",
    "r.begleit": "Begleitmaterial", "r.begleit.e": "Leitfaden, Informationsblatt, Einwilligungsvorlage, Methodenbericht, README.",
    "r.dateien.text": "Dateien, wie sie in der Bibliothek liegen, mit Prüfsumme (SHA-256). Für die Ablage werden "
                      "daraus Exporte erzeugt; die Prüfsummen der Exporte sind nach dem Export zu bilden.",
    "r.formate": "Zu den Formaten:",
    "r.formate.punkte": "Transkripte zusätzlich zu Word und REFI-QDA in einem offenen Textformat ablegen (TXT, Markdown, CSV); Archive bevorzugen einfache, offene Formate.\n"
                        "REFI-QDA ist ein Austauschformat mit möglichem Verlust zwischen Programmen, kein alleiniges Archivformat.\n"
                        "Die MP3 in den Paketen der App ist eine Nutzungskopie. Als Archivmaster empfehlen Archive FLAC oder WAV — also die Originalaufnahme.\n"
                        "Jedes Transkript braucht einen Kopf mit Kennung, Datum und Kontext; der Markdown- und Word-Export der App schreibt ihn.",
    "r.ethik.text": "Nur von den Forschenden zu beantworten. Solange ein Punkt offen ist, wird nichts veröffentlicht.",
    "r.pruefpunkt": "Prüfpunkt", "r.erledigt": "erledigt",
    "r.ethik.punkte": "Die Einwilligung deckt Archivierung und Nachnutzung. :: Ohne dokumentierte Einwilligung keine Weitergabe.\n"
                      "Die Einwilligung deckt die Weitergabe der Tonaufnahme. :: Die Stimme ist ein Personendatum.\n"
                      "Ein Ethikvotum oder eine Auflage liegt vor. :: Nummer und Stelle angeben.\n"
                      "Direkte und indirekte Merkmale sowie erwähnte Dritte sind geprüft. :: Kombinationen wie Beruf, Ort und Alter beachten.\n"
                      "Titel, Beschreibung, Schlagworte und Dateinamen sind frei von Personendaten. :: Metadaten sind immer öffentlich.\n"
                      "Die Schlüsselliste der Pseudonyme wird getrennt aufbewahrt. :: Sie gehört nie in die Ablage.\n"
                      "Ausgangsstand und Verlauf bleiben draussen. :: `ausgang.json` und `history/` enthalten den Wortlaut vor der Pseudonymisierung.\n"
                      "Das Repositorium passt zu den Daten. :: Für sensible Daten ein Facharchiv mit Zugangskontrolle.\n"
                      "Vorgaben von Förderer und Hochschule sind geprüft. :: Ausnahmen vom offenen Zugang im Datenmanagementplan begründen.",
    "r.wohin": "Welches Repositorium", "r.repo": "Repositorium", "r.repo.fuer": "Eignung",
    "r.repos": "Zenodo :: Allgemein, DOI sofort; Dateien sperrbar, Metadaten immer offen. Für Dokumentation, Instrumente und wirklich anonymisierte Texte; nicht für Aufnahmen. :: https://zenodo.org\n"
               "SWISSUbase (FORS) :: Schweiz, Sozialwissenschaften; nimmt qualitative und sensible Daten mit Zugangskontrolle und Nutzungsvertrag; DOI. :: https://www.swissubase.ch\n"
               "Qualiservice :: Deutschland, qualitative Daten; Beratung, Hilfe bei Anonymisierung, Zugang nur auf Antrag; DOI. :: https://www.qualiservice.org\n"
               "AUSSDA :: Österreich, Sozialwissenschaften; eigene Richtlinie für qualitative Daten. :: https://aussda.at\n"
               "UK Data Service :: Vereinigtes Königreich; gestufter Zugang (open, safeguarded, controlled). :: https://ukdataservice.ac.uk",
    "r.quellen": "Grundlagen",
    "r.quellen.punkte": "DataCite Metadata Schema 4: <https://schema.datacite.org>\n"
                        "Zenodo: Felder <https://help.zenodo.org/docs/deposit/describe-records/>, Richtlinien <https://about.zenodo.org/policies/>, Bedingungen <https://about.zenodo.org/terms/>\n"
                        "CESSDA Data Management Expert Guide: <https://dmeg.cessda.eu>\n"
                        "FORS Guide Nr. 20, Anonymisierung qualitativer Daten: <https://doi.org/10.24449/FG-2023-00020>\n"
                        "SNF, Open Research Data: <https://www.snf.ch/de/FAiWVH4WvpKvohw9/thema/forschungsdaten>\n"
                        "DFG, Umgang mit Forschungsdaten: <https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/forschungsdaten>\n"
                        "README-Vorlage der Cornell University (CC0): <https://data.research.cornell.edu/data-management/sharing/readme/>",
    # ---- Methodenbaustein für EIN Transkript (der Regelfall) ----
    'm.einleitung.eins': 'Dieser Baustein beschreibt, wie dieses eine Transkript entstand und wie stark das maschinelle Rohtranskript von Hand bearbeitet wurde. Die Aussagen gelten für dieses Dokument. Darunter steht ein Absatz zum Übernehmen und eine Liste dessen, was nur die Forschenden wissen.',
    'm.korpus.eins': 'Transkript',
    'm.mass.fehlt': 'Für dieses Transkript ist kein Ausgangsstand mehr vorhanden; das Eingriffsmass lässt sich nicht berechnen (siehe Transkriptionsprotokoll).',
    'm.absatz.text.eins': 'Die Aufnahme (Dauer {gesamt}) wurde mit ResearchTranscript {version} (B/IAS Basel, AGPL-3.0) vollständig lokal [ auf einem Rechner der Forschungsgruppe ] transkribiert; die App übermittelt dabei nichts an externe Dienste. Die Spracherkennung nutzte whisper.cpp {whisper} mit dem Modell {modell} (Radford et al., 2022).{diar} Das Rohtranskript wurde anschliessend von [ wem ] [ vollständig / stichprobenweise ] gegen die Aufnahme geprüft, nach [ Transkriptionsregeln ] korrigiert [ und im Text pseudonymisiert ]. Die Korrekturrate auf Wortebene (berechnet wie die Wortfehlerrate, Endfassung als Referenz, normalisiert) betrug {norm}. Die Rate misst den Eingriff einschliesslich Pseudonymisierung, nicht die Genauigkeit.',
    'm.absatz.diar.eins': ' Die Sprecher wurden mit SpeakerKit und dem Modell pyannote community-1 getrennt (Plaquet & Bredin, 2023); von Hand neu zugeordnet wurden {sprechzeit} der Sprechzeit.',
}
