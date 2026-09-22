# App Store — Einreichung: Metadaten, Review-Notizen, Checkliste

Stand 17.9.2026, ResearchTranscript 0.6.0 (Branch `eingebettet-spike`).
Gehört zu `docs/appstore-plan.md` §6. Texte sind Vorschläge zum
Einfügen in App Store Connect; Grenzen (Zeichen) stehen dabei.

## 1. Was du im Portal anlegst (einmalig)

| Schritt | Wo | Wert |
|---|---|---|
| App-ID mit App Sandbox | developer.apple.com → Identifiers | `city.bias.researchtranscript` (explizit, nicht Wildcard) |
| Zertifikat «Apple Distribution» | Certificates | im Schlüsselbund als «Apple Distribution: ben pohl (CCRJ4A42D3)» |
| Zertifikat «Mac Installer Distribution» | Certificates | für `productbuild` |
| Provisioning-Profil (Mac App Store) | Profiles | nach `frontend/src-tauri/profiles/ResearchTranscript.provisionprofile` |
| API-Schlüssel (App Store Connect API) | Users and Access → Integrations | `~/.appstoreconnect/private_keys/AuthKey_<ID>.p8`; `APPLE_API_KEY_ID`, `APPLE_API_ISSUER` |
| App-Eintrag | App Store Connect → Apps → + | Name, Bundle-ID, SKU `researchtranscript`, Primärsprache Deutsch |

Danach: `node scripts/release-mas.mjs` (baut, signiert, prüft, paketiert)
und `node scripts/release-mas.mjs --upload` (validiert und lädt hoch).
Erster Build zuerst nach **TestFlight** (intern), nicht direkt in die Review.

## 2. Metadaten (App Store Connect → App-Informationen / Version)

**Name:** ResearchTranscript (30 Zeichen max.)

**Untertitel** (30 Zeichen):
- de: Interviews offline transkribieren
- en: Transcribe interviews offline
- fr: Transcrire hors ligne
- it: Trascrivere offline

**Kategorie:** Produktivität (primär), Bildung (sekundär).
**Preis:** 0. **Altersfreigabe:** 4+. **Copyright:** 2026 B/IAS – Basel Institut für angewandte Stadtforschung.

**URLs:**
- Support: https://bias.city/researchtranscript/
- Marketing: https://bias.city/researchtranscript/
- Datenschutz: https://bias.city/researchtranscript/privacy.html

**App-Datenschutz (Fragebogen):** «Daten werden nicht erfasst» — die App
erhebt nichts, überträgt nichts, hat kein Konto.

**Exportkonformität:** Die App nutzt keine eigene Verschlüsselung; die
gebündelte CPython-Laufzeit enthält OpenSSL statisch (Standard-
Bibliothek, ungenutzt). `ITSAppUsesNonExemptEncryption = false` steht in
der Info.plist → die Frage wird beim Upload nicht mehr gestellt. Falls
doch gefragt: «Nein, keine nicht-freigestellte Verschlüsselung».

**Schlagwörter** (100 Zeichen, kommagetrennt):
- de: Transkription,Interview,Whisper,Sprecher,Diarisierung,qualitativ,Forschung,QDA,ATLAS.ti,offline
- en: transcription,interview,whisper,speaker,diarization,qualitative,research,QDA,ATLAS.ti,offline
- fr: transcription,entretien,whisper,locuteur,diarisation,qualitatif,recherche,QDA,hors ligne
- it: trascrizione,intervista,whisper,parlante,diarizzazione,qualitativo,ricerca,QDA,offline

**Werbetext** (170 Zeichen, optional):
- de: Aufnahme rein, Transkript mit Sprechern raus — auf deinem Mac, ohne Cloud. Für Interviews, Gruppengespräche und Feldaufnahmen in der Forschung.
- en: Recording in, speaker-labelled transcript out — on your Mac, no cloud. For interviews, group discussions and field recordings in research.

**Beschreibung** (4000 Zeichen):

de:
> ResearchTranscript transkribiert Interviews, Gruppengespräche und Feldaufnahmen vollständig auf deinem Mac. Die Aufnahme verlässt den Rechner nie: keine Cloud, kein Konto, keine Netzverbindung.
>
> • Spracherkennung mit whisper.cpp (Modell large-v3-turbo, mitgeliefert), Deutsch, Englisch, Französisch, Italienisch und weitere Sprachen
> • Sprechertrennung auf der Neural Engine (SpeakerKit, pyannote) — die Zahl der Sprechenden gibst du je Aufnahme vor oder lässt sie erkennen
> • Mehrere Dateien in eine Warteliste ziehen, Sprecherzahl je Datei wählen, starten
> • Editor mit Wellenform, Turn-Navigation per Tastatur, Zwischenrufe an der Abspielposition einfügen, Timecodes bearbeiten, Sprecher umbenennen, umfärben, zusammenführen
> • Video (MP4, MOV mit H.264/HEVC) als Quelle — der Ton wird gelesen, das Bild läuft stumm mit
> • Exporte: WebVTT, CSV, Text, REFI-QDA (.qdpx für ATLAS.ti, MAXQDA, NVivo), enrich-Dossier
> • Zotero-Metadaten (Titel, Datum, Interviewende, Citekey) auf Wunsch aus der lokalen Bibliothek
> • Eigene whisper.cpp-Modelle (z. B. Schweizerdeutsch-Feintuning) in den Modelle-Ordner legen
>
> Für Forschende, die Datenschutzauflagen ernst nehmen: fertige Textbausteine für Verfahrensverzeichnis, Ethikantrag und Methodenteil liegen auf der Website. Freie Software (AGPL), Quellcode auf GitHub. Entwickelt am B/IAS – Basel Institut für angewandte Stadtforschung.
>
> Voraussetzungen: Mac mit Apple Silicon, macOS 14 oder neuer, rund 2 GB freier Speicher für die App.

en:
> ResearchTranscript transcribes interviews, group discussions and field recordings entirely on your Mac. The recording never leaves your computer: no cloud, no account, no network connection.
>
> • Speech recognition with whisper.cpp (large-v3-turbo model included) — German, English, French, Italian and many more languages
> • Speaker separation on the Neural Engine (SpeakerKit, pyannote) — set the number of speakers per recording or let the app detect it
> • Drop several files into a waiting list, choose the speaker count per file, start
> • Editor with waveform, keyboard turn navigation, interjections inserted at the playhead, editable timecodes, speakers renamed, recoloured, merged
> • Video (MP4, MOV with H.264/HEVC) as a source — the audio is read, the picture follows silently
> • Exports: WebVTT, CSV, text, REFI-QDA (.qdpx for ATLAS.ti, MAXQDA, NVivo), enrich dossier
> • Zotero metadata (title, date, interviewers, citekey) from your local library on request
> • Your own whisper.cpp models (e.g. a Swiss German fine-tune) in the model folder
>
> Built for researchers who take data protection seriously: ready-made text for records of processing, ethics applications and methods sections is on the website. Free software (AGPL), source code on GitHub. Developed at B/IAS – Basel Institut für angewandte Stadtforschung.
>
> Requirements: Mac with Apple silicon, macOS 14 or later, about 2 GB of free space for the app.

fr und it: aus de/en übersetzen, wenn die deutsche Fassung steht (die
Website-Texte in `site/index.html` sind die Vorlage).

**Neuerungen in dieser Version** (0.6.0): «Erste Fassung im Mac App Store.»

## 3. Screenshots

1280×800 bis 2880×1800, Seitenverhältnis 16:10, PNG, je Sprache 1–10.
Motive aus `docs/screenshots/` (01 Warteliste, 02 Bibliothek, 03 Editor,
04 Suchen/Ersetzen, 05 Export) — mit der Screenshot-Pipeline gegen das
Demo-Backend neu aufnehmen (Commit 6a36053 beschreibt den Lauf), in der
neuen Optik (Pillen, Wellenform) und im Hell-Modus, Fenster 1440×900 →
2880×1800 (Retina).

## 4. Review-Notizen (App Review Information → Notes, ≤ 4000 Zeichen)

> ResearchTranscript works fully offline: no account, no login, no server, no telemetry. The network-client entitlement is present only because WebKit requires it to render the app's own bundled pages; the app opens no network connections (you can verify with Little Snitch or `nettop`: none).
>
> Architecture: the UI is a WKWebView; the application logic is written in Python and runs inside the app process through an embedded CPython 3.13 interpreter linked as a framework (no socket, no interpreter child process). The interpreter executes only the scripts shipped in the bundle; the app never downloads code, models or resources (Guideline 2.5.2). Since 0.6.1 the runtime no longer carries pip, venv or build tooling at all (see CHANGELOG 0.6.1 and appstore/texte/antwort-review-2-5-2-en.txt). Audio decoding uses AVFoundation; MP3 encoding uses the bundled LAME library (LGPL, dynamically linked, source shipped with the app). Speaker diarisation (SpeakerKit, Core ML) runs in-process. Speech recognition uses one bundled helper, `whisper-cli` (whisper.cpp, Metal), launched by the app with the sandbox `inherit` entitlement; it reads only a temporary file inside the app container and the model file, and terminates with the job.
>
> Files are accessed only through the Open/Save panels, drag & drop, or the library folder the user chooses on first launch (kept as a security-scoped bookmark). The optional e-mail field is written only into dossier files the user exports; it is never transmitted. Zotero integration is optional, read-only, local, and requires the user to pick the Zotero folder.
>
> Demo: the attached zip contains a 2-minute synthetic interview (two invented speakers, synthesised with macOS `say`). Steps: open the app → choose any folder as library → drag the mp3 into the "AI Transcript" tab → speakers: 2 → Start → about 30 seconds on Apple silicon → "Human Editor" shows the transcript.
>
> Requires Apple silicon, macOS 14+. Licence: AGPL-3.0 with an App Store additional permission (LICENSE-EXCEPTION in the repository). Contact: [Support-E-Mail].

Anhang: `docs/demo/researchtranscript-demo.zip` (mp3 + Referenztext).

## 5. Checkliste vor dem Upload

- [ ] `LICENSE-EXCEPTION` im Repo, in README verlinkt
- [ ] `THIRD_PARTY_LICENSES.md` erzeugt (`python3 scripts/gen-licenses.py`), im Bundle, Knopf «Lizenzen» in den Einstellungen
- [ ] Über-Dialog in der Store-Fassung (Cargo-Feature `mas`, setzt `release-mas.mjs`): kein Knopf «Releases», dafür Datenschutzerklärung (Guideline 5.1.1), Zusatzerlaubnis, Lizenzliste, Quellcode-Links (AGPL/LGPL-Angebot)
- [ ] `site/privacy.html` hochgeladen, URL im Portal eingetragen
- [ ] LAME-Tarball unter bias.city/researchtranscript/quellen/ (LGPL-Angebot)
- [ ] Zertifikate, Profil, API-Schlüssel vorhanden
- [ ] `node scripts/release-mas.mjs` läuft durch (Prüfungen 4/6)
- [ ] TestFlight-Build getestet: Erststart (Ordnerdialog), Transkription per Drop, Export in fremden Ordner, Zotero-Ordner, Neustart (Bookmarks)
- [ ] Screenshots je Sprache, Beschreibung, Schlagwörter, Datenschutz-Fragebogen
- [ ] Review-Notizen mit Demo-Zip
