<!-- Erzeugt am 2026-09-16 aus einem Multi-Agenten-Lauf: sechs Untersuchungen,
     sechs adversariale Gegenprüfungen, eine Verdichtung. Aufwände sind
     Schätzungen. Vor dem Umsetzen: Phase 0 zuerst. -->

# ResearchTranscript in den Mac App Store bringen

Stand 2026-09-16, Version 0.4.0. Grundlage: sechs geprüfte Dimensionen (Sandbox, Entitlements, Lizenzen, Bau-Kette, Review, Datenablage). Aufwände sind Schätzungen in Personentagen (PT), sofern nicht anders gesagt.

## 1. Kurzfassung

- **Tor 1 – Sandbox:** Die heutige Arbeitsteilung «Hülle sammelt Pfade, Python-Kind öffnet sie» ist im App Sandbox tot: ein Kindprozess erbt nur statische Rechte, keine Powerbox-/Drop-Freigaben (Apple-Doku, DTS-Thread 111125). Dazu: `lsof`/`ps`/`kill` geblockt, `venv_fixen` schreibt ins versiegelte Bundle (App startet im MAS gar nicht), Executables in `Contents/Resources`.
- **Tor 2 – Lizenzen:** Der gebündelte ffmpeg ist ein GPLv3-Build (libx264/libx265). Fremdes GPL lässt sich nicht per eigener Ausnahme heilen. Die eigene AGPL ist als Alleinrechteinhaber per §7-Zusatzerlaubnis lösbar.
- **Sicherer Ablehnungsgrund, leicht behebbar:** keine Datenschutzerklärung als URL + In-App-Link (5.1.1(i)).
- **Gesamtaufwand:** ca. 18–25 PT Entwicklung plus Zertifikate, Rechtsprüfung, TestFlight-Zyklen (Schätzung).
- **Grösstes Risiko:** Kein belegter MAS-Freigabefall für Tauri + eingebettetes CPython + lokalem HTTP-Server; GeoLibre wurde unter 2.4.5 wegen `network.server` für einen Loopback-Server abgelehnt. Technische Machbarkeit ist von Apple DTS bestätigt, der Review-Ausgang nicht.
- **Empfehlung:** Phase 0 (Spike, 1–2 Tage) zuerst; dann Container-Bibliothek als MAS-Standard, LGPL-ffmpeg für **beide** Kanäle, Helfer im `Resources`-Layout vorsigniert (vermeidet Tauris Signierkonflikt), ein früher TestFlight-Build vor dem vollständigen Umbau der Datei-Flüsse. Developer-ID-DMG bleibt Hauptkanal, bis der Store-Build durch den Review ist.

## 2. Phase 0 «Sandbox-Versuch» (Branch `mas-spike`, 1–2 PT)

`tauri dev` honoriert Sandbox-Entitlements nicht (Tauri-Issue 15144) — alles läuft am **signierten Build**.

1. Zertifikat «Apple Development» genügt; `entitlements.spike.plist` mit `app-sandbox`, `network.server`, `network.client`, `files.user-selected.read-write`. Über `tauri build --config src-tauri/tauri.spike.conf.json` bündeln (nur `bundle.macOS.entitlements` überschreiben).
2. `scripts/sign-resources.mjs --entitlements entitlements.child.plist --no-hardened` mit einer Datei, die **exakt** `app-sandbox` + `inherit` enthält, auf `python3.13`, `whisper-cli`, `ffmpeg`, `argmax-cli`; dylib/.so ohne `--entitlements`.
3. In `frontend/src-tauri/src/lib.rs` temporär: `venv_fixen` überspringen, Backend als `python-runtime/bin/python3 -m uvicorn` mit `PYTHONPATH=<venv site-packages>`, `PYTHONDONTWRITEBYTECODE=1`.
4. Messen (je ja/nein, mit `log stream --predicate 'sender == "Sandbox"'`):
   - M1 Backend startet, `/api/health` antwortet, WebView lädt (kein weisser Bildschirm).
   - M2 Ordner per Open-Panel wählen → Kommando spawnt `/bin/ls <Ordner>` → Exit-Code (Kernfrage: erbt ein nach dem Grant gespawntes Kind den Zugriff? Apple sagt nein).
   - M3 Datei aus dem Finder droppen → Hülle `std::fs::copy` in `$HOME/tmp` (Tregaskis-Effekt bei wrys `draggingEntered`-Lesen?).
   - M4 Python löst einen von der Hülle erzeugten Bookmark per `ctypes`/CoreFoundation auf und liest die Datei; danach ffmpeg als Enkel auf dieselbe Datei (Enkel-Schranke).
   - M5 Transkription + Diarisierung mit Bibliothek im Container (`$HOME/Documents/ResearchTranscript`), ohne die vier `cs.*`-Ausnahmen.
   - M6 `ordner_oeffnen` via `/usr/bin/open` vs. `tauri-plugin-opener::reveal_item_in_dir`.
5. **Abbruchkriterium:** M1 oder M5 scheitern nach einem Tag Fehlersuche → Store-Vorhaben pausieren, Befund dokumentieren. M2/M3/M4 entscheiden nur die Architektur der Datei-Flüsse (Kopie vs. Bookmark), nicht das Ob.

## 3. Phase 1 «Umbauten» (ca. 10–14 PT)

### 3.1 Prozessmodell (`frontend/src-tauri/src/lib.rs`, 3 PT, Abhängigkeit: Phase 0 M1)

| Änderung | Detail |
|---|---|
| `lsof`/`ps`/`kill` entfernen | `port_halter`, `ps_zeile`, `ist_eigenes_backend`, `vorgaenger_laeuft`, `beende_pid`, `pid_lebt` streichen. Im Sandbox liefert `pid_lebt` für eine lebende Zweitinstanz `false` — die Logik ist nicht nur blockiert, sondern falsch. |
| Kind-Handle | `Mutex<Option<std::process::Child>>`; beim Exit erst tokengeschützter `POST /api/shutdown` (2 s), dann `child.kill()` + `wait()`. Signale an eigene Kinder sind erlaubt. |
| Port-Konflikt | `TcpListener::bind("127.0.0.1:5628")`; bei `EADDRINUSE` `/api/health` lesen — Health trägt `app`, `version`, `token_hash`. Eigenes Token → Waise übernehmen, sonst Fehlermeldung. Optional robuster: Listener behalten, `FD_CLOEXEC` per `libc::fcntl` löschen, `uvicorn --fd`. |
| Kein Schreiben ins Bundle | `venv_fixen` streichen; Start `python-runtime/bin/python3 -s -B -m uvicorn …` mit `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPYCACHEPREFIX=$HOME/Library/Caches/…`. Environment **nicht** leeren (`HOME`, `TMPDIR`, `APP_SANDBOX_CONTAINER_ID` müssen durch) — Kommentar im Code. |
| Finder-Reveal | `/usr/bin/open` → `tauri_plugin_opener::reveal_item_in_dir`. |
| Devtools | `tauri = { features = ["devtools"] }` nutzt private APIs; für den Store-Build als Cargo-Feature abschaltbar machen, Capability `core:webview:allow-internal-toggle-devtools` aus `capabilities/default.json` im MAS-Profil entfernen. |
| Bookmarks | Kommandos `bookmark_erzeugen(pfad)` / `bookmark_persistieren` / `bookmark_wiederherstellen` via `objc2-foundation` (`NSURL bookmarkDataWithOptions:`, `startAccessingSecurityScopedResource`, Stop beim Exit). Die Crates `tauri-plugin-scoped-bookmarks` / `apple-scoped-bookmarks` (0.1.0, 17.08.2026, gleiches Repo) sind zu jung. Nur nötig für Zotero-Ordner und optionale externe Bibliothek. |

`backend/src/researchtranscript/main.py` (1 PT): `POST /api/shutdown` mit `X-LT-Token` (Env `LT_TOKEN` vom Spawn); Health um `app`/`version`/`token_hash` ergänzen; Eltern-Watchdog-Thread (`os.getppid() == 1` → sauber beenden). Empfehlung: Token für **alle** Endpunkte, weil `network.server` das UI und die API jedem lokalen Prozess öffnet (`host_wache` prüft nur den Host-Header).

### 3.2 Datei-Flüsse (4–5 PT, Abhängigkeit: Phase 0 M2–M4)

Entscheidung für den MAS-Build: **Bibliothek im Container**. `default_library_root()` = `Path.home()/Documents/ResearchTranscript` landet unter Sandbox von selbst in `~/Library/Containers/city.bias.researchtranscript/Data/Documents/ResearchTranscript` — `config.py` braucht dafür keine Änderung; nur «Ordner wählen» verschwindet. Vorteil: Python, ffmpeg, whisper-cli, argmax-cli sehen den Ordner ohne Bookmark; eigene Modelle unter `<Bibliothek>/Modelle` funktionieren unverändert.

| Datei | Änderung |
|---|---|
| `lib.rs` | `datei_uebernehmen(pfad)`: kopiert Datei/`.enrich`-Package (APFS-Clone auf demselben Volume) nach `$HOME/tmp/rt-eingang/<ulid>/`, gibt Container-Pfad zurück. `datei_ablegen(quelle, ziel)`: schreibt per `std::fs::copy` **direkt** in den Save-Panel-Pfad (kein `rename`, keine Nachbar-Tempdatei). `RunEvent::Opened` läuft durch dieselbe Übernahme. `LT_SANDBOX=1` ans Backend. |
| `frontend/src/lib/tauri.ts`, `AiTranscriptModule.tsx`, `HumanEditorModule.tsx`, `App.tsx` | Pfade aus `pickAudio`, `pickTranskript`, `onFileDrop`, `geoeffneteDateien` vor `/api/transcribe-path` und `/api/import-path` durch `dateiUebernehmen` schleusen (Fortschritt + Abbruch, da Cross-Volume-Kopie echte Kopie ist). Export-Knöpfe: Backend-Rückgabepfad per `dateiAblegen` ans Ziel. |
| `main.py` | Bei `LT_SANDBOX`: `settings.library_root` nicht setzbar (409); Nachbarsuche `p.with_suffix(endung)` in `import_path` überspringen (Powerbox-Grant gilt nur für die gewählte Datei); `export_datei` schreibt nach `$HOME/tmp/rt-export/<ulid>/`; `transcribe_path` nutzt `jobs.starte(..., quelle_ist_temp=True)`. |
| `jobs.py`, `diarize.py`, `video.py` | Falls Phase 2 «externe Bibliothek» je kommt: ffmpeg/argmax-cli nur auf Temp-Pfade loslassen (Kopie statt Symlink `ton.<ext>`). Für die Container-Bibliothek nicht nötig. |
| `EinstellungenModule.tsx`, `i18n.ts` | Speicherort-Karte nur Anzeige + «Im Finder zeigen»; viersprachige Strings (Container-Hinweis, Kopie läuft, Export abgelegt). |
| `config.py` | `_find_executable`: im Bundle-Modus keine Homebrew-/`which`-Fallbacks (2.4.5(ii)); `get_models_dir`-Fallback `~/whisper-models` nur im Dev-Modus. |

Nachteil, offen zu kommunizieren: die Bibliothek liegt im Container, nicht in iCloud Drive; DMG-Nutzer starten im MAS-Build mit leerer Bibliothek — ein «Bibliothek übernehmen»-Weg (Ordner wählen + Kopie durch die Hülle) ist sinnvoll (1 PT).

### 3.3 Zotero (1–2 PT)

Die Automatik (`~/Zotero`, `prefs.js`, `/Volumes/*/Zotero` in `enrich_core.find_zotero_dir`) ist im Container blind. Drei Wege, Entscheidung offen:

1. **Ordnerdialog + app-scoped Bookmark** in der Hülle; Hülle klont `zotero.sqlite` nach `$HOME/Library/Caches/ResearchTranscript/zotero/` (mtime-Vergleich) und setzt `zotero_dir` auf den Cache. `zotero.py`: `status()` ohne Automatik, `needs_folder: true`; keine Änderung an `enrich_core` (explizite `zotero_dir` gewinnt).
2. **Zotero-7-Local-API** (`http://localhost:23119/api/`, nur `network.client`): kein Bookmark, kein Spiegel — aber zweite Datenquelle neben sqlite in der Zotero-Schicht, Zotero muss laufen.
3. Temporary-Exception-Entitlement für `~/Zotero` — Review-Ablehnung möglich (unsicher), nicht empfohlen.

### 3.4 Entitlements und Signatur (1 PT)

- `entitlements.mas.plist` (Hülle): `app-sandbox`, `application-identifier` = `CCRJ4A42D3.city.bias.researchtranscript`, `developer.team-identifier`, `network.server`, `network.client`, `files.user-selected.read-write`, `files.bookmarks.app-scope`. Keine `cs.*`-Ausnahmen: alle 27 Mach-O tragen dieselbe Team-ID (Library Validation besteht), CPython ist `--enable-experimental-jit=yes-off`, niemand setzt `DYLD_*`. Auch für den Developer-ID-Build empfohlen: leeres Dict — nach Laufzeittest.
- `entitlements.child.plist`: **exakt** `app-sandbox` + `inherit` für `python3.13`, `whisper-cli`, `argmax-cli`, `ffmpeg`. Bibliotheken ohne Entitlements (codesign bettet sie in dylib/.so ohnehin nicht ein).
- **Layout-Entscheidung:** Helfer bleiben im `Resources`-Layout und werden **vor** `tauri build` mit dem Kind-Plist signiert. Tauri fasst `resources/` nicht an — würde man sie zu `externalBin`, signierte Tauri sie mit den Hüllen-Entitlements neu → Kind-Abbruch. Der Umzug nach `Contents/MacOS`/`Frameworks` (Apple-Empfehlung, TN2206) ist Phase 2, falls `--validate-app` oder Review das verlangt (unsicher).
- `sign-resources.mjs`: Parameter `--identity`, `--entitlements`, `--no-hardened`, `--requirements "=designated => anchor apple generic and identifier \"city.bias.researchtranscript\" …"` (Tauri-Issue 15230); Mach-O-Typ auswerten; `xattr -cr resources/` und Rechte-Check (`find -not -perm -o+r`) **vor** dem Bundling; veraltete Kommentare («253 Mach-O», «244 dylib/so, torch») korrigieren.
- `hole-argmax.mjs`: LC_RPATH auf `/Applications/Xcode.app/…/swift-6.2` per `install_name_tool -delete_rpath` strippen.
- `bundle-resources.mjs` (2 PT, optional aber empfohlen): venv abschaffen, Pakete direkt in `python-runtime` installieren — kein `pyvenv.cfg`, keine doppelte `libpython`, keine dereferenzierten Interpreter-Kopien; Tcl/Tk, `_tkinter`, `_dbm`, `pip`, `idle` entfernen (pip kann Code nachladen — schwächt das 2.5.2-Argument). Nützt auch dem DMG-Build, der heute nach dem ersten Start sein Siegel bricht.

### 3.5 Tests (1 PT)

`backend/tests/test_sandbox_modus.py` mit `LT_SANDBOX=1` + `LT_CONFIG_DIR`-Scratch: Default-Bibliothek ohne Konfiguration, `settings_post` lehnt `library_root` ab, `import_path` ohne Nachbarsuche, `export_datei` liefert Container-Pfad, `zotero.status` ohne Automatik, `/api/shutdown` nur mit Token. Drift-Guard und die 19 Backend-Tests grün halten.

## 4. Phase 2 «Lizenzen» (2–3 PT + Rechtsprüfung)

| Bestandteil | Lizenz | MAS-Verdikt |
|---|---|---|
| Eigener Code (Backend, Frontend, Hülle, vendored `turns.py`) | AGPL-3.0-or-later | OK mit §7-Zusatzerlaubnis; Alleinurheberschaft per `git shortlog` bestätigt |
| enrich-core 0.1.0 | MIT | OK |
| whisper.cpp / libwhisper / libggml | MIT | OK |
| ggml-large-v3-turbo (OpenAI) | MIT | OK |
| silero-vad (`venv/…/researchtranscript/vad/silero-v5.1.2.bin`) | MIT | OK — im Inventar an diesem Ort führen |
| argmax-cli (SpeakerKit) | MIT + swift-transformers-Teile Apache-2.0 | OK — NOTICE mitführen |
| SpeakerKit-Modelle | Segmenter pyannote/segmentation-3.0 **MIT (CNRS)**; Embedder WeSpeaker **CC BY 4.0**; Clusterer VBx: Code Apache-2.0, Gewichte unklar; Argmax gesamt CC BY 4.0 | OK — Namensnennung komponentengenau (In-App-Text «pyannote community-1» ist falsch) |
| **ffmpeg 9.0.1 (martin-riedl, `--enable-gpl --enable-libx264 --enable-libx265`)** | **GPLv3** (allein wegen x264/x265; zvbi ist kein Trigger, OpenSSL 3 mit `version3` zulässig) | **NICHT OK** |
| CPython 3.13 (python-build-standalone) | PSF-2.0; OpenSSL Apache-2.0 statisch; libedit statt readline; kein gdbm | OK |
| 23 Python-Pakete | MIT / BSD-3 / Apache-2.0 (python-multipart) / PSF | OK |
| 85 npm-Pakete | MIT / ISC / 0BSD | OK |
| 445 Rust-Crates | MIT/Apache-2.0; MPL-2.0: cssparser, cssparser-macros, dtoa-short, option-ext, selectors; kein GPL/LGPL-Zwang | OK |
| CC BY 4.0 generell | FairPlay verschlüsselt nur Mach-O, Modelle bleiben Ressourcen | OK (Ableitung aus Reverse-Engineering-Quellen, unsicher) |

**ffmpeg-Entscheidung:** LGPL-Build für beide Kanäle. Alle sechs Aufrufstellen (`jobs.py:178/194`, `main.py:595`, `video.py:45/89`, `exporte.py:95`) brauchen nur LGPL-Kern + libmp3lame. MP3-Kodierung geht mit Apple-Frameworks nicht, ein Verzicht auf ffmpeg scheitert an «.enrich-Audio IMMER mp3». Belegte Quelle: Nothing-Software/FFmpeg-Builds (LGPL-2.1-or-later inkl. LAME, Source-Tarballs je Release). Vor Übernahme `-buildconf` prüfen: kein `--enable-gpl`, kein `--enable-nonfree`, kein `--enable-openssl` (löst zugleich die Export-Compliance-Frage für ffmpeg), kein `--enable-securetransport` (2.5.1). Lizenz-Wächter in `bundle-resources.mjs` (Z. 61–77) entsprechend erweitern; korrespondierenden Quell-Tarball auf `bias.city/localtranscript` neben dem Download hosten — das schliesst auch die heutige GPL-§6-Lücke des DMG-Releases (Release v0.4.0 hat keine Quell-Links).

**AGPL-Ausnahme** (`LICENSE-EXCEPTION`, formale §7-Erlaubnis nach Dorkroom-Muster, Abschnitte 0–6), Vorschlag der Kernklausel:

> Additional permission under GNU AGPL version 3 section 7. Als alleiniger Rechteinhaber von ResearchTranscript erteilt B/IAS – Basel Institut für angewandte Stadtforschung die zusätzliche Erlaubnis, das Programm über eine «Managed Distribution Platform» (Apple App Store, Mac App Store, Apple TestFlight) zu verbreiten, auch wenn deren Nutzungsbedingungen den Empfängern Beschränkungen auferlegen, die §6 (Installation Information), §10 (keine weiteren Beschränkungen) oder §12 der AGPL widersprechen. Unberührt bleiben die Pflicht zur Bereitstellung des Quelltexts (§§4–6, §13), das Copyleft und alle übrigen Bedingungen; die Erlaubnis gilt nur für von B/IAS selbst eingereichte Builds und darf von jedem Empfänger gemäss §7 entfernt werden.

Hinweis in den Einstiegsdateien (`main.py`, `main.tsx`, `lib.rs`); `turns.py` per Pfadnennung in `LICENSE-EXCEPTION` (Vendor-Datei bleibt unangetastet). CONTRIBUTING-Regel: Fremdbeiträge nur mit Zustimmung zur Ausnahme.

**Juristisch prüfen lassen** (z. B. FSFE Legal Network, wie Nextcloud): Text der Ausnahme; eigene EULA in App Store Connect (Apples Mindestbedingungen, **kein** Reverse-Engineering-Verbot, Open-Source-Vorbehalt, Nennung FFmpeg/LAME); Restrisiko LGPL vs. Apple-Terms (FSF-Position: «any true copyleft license»). Neu ins Bundle: `resources/licenses/` mit allen Lizenztexten/NOTICES, Knopf «Lizenzen» im Über-Dialog.

## 5. Phase 3 «Bau- und Upload-Kette» (2–3 PT)

Istzustand: Tauri 2.11.5 / CLI 2.11.4, Xcode 26.5, altool 26.40.1, Transporter nicht installiert, im Schlüsselbund nur Apple Development + Developer ID.

1. **Einmalig im Portal:** App-ID `city.bias.researchtranscript` mit Capability App Sandbox; Zertifikate «Apple Distribution» (App) und «Mac Installer Distribution» (pkg; CN «3rd Party Mac Developer Installer: ben pohl (CCRJ4A42D3)», nach Erzeugen per `security find-identity -v -p macappstore` verifizieren); Provisioning Profile «Mac App Store Connect» nach `frontend/src-tauri/profiles/` (gitignore: `profiles/`, `*.provisionprofile`, `*.p8`, `*.pkg`). TN3125 sagt, das Profil sei bei ausschliesslich unrestricted Entitlements nicht nötig, der Tauri-Guide verlangt es — mitliefern schadet nicht. API-Schlüssel nach `~/.appstoreconnect/private_keys`.
2. **`frontend/src-tauri/tauri.macos-appstore.conf.json`** (Overlay, Arrays werden ersetzt): `bundle.category: "Productivity"`, `bundle.targets: ["app"]`, `bundle.macOS.signingIdentity: "Apple Distribution: …"`, `entitlements: "entitlements.mas.plist"`, `hardenedRuntime: false` (für MAS nicht nötig; bewusst dokumentieren), `bundleVersion` (steigend), `files: {"embedded.provisionprofile": "profiles/…"}`. `Info.plist`: `ITSAppUsesNonExemptEncryption` (siehe Phase 4).
3. **`scripts/release-mas.mjs`:** `bundle-resources` → `sign-resources --mas` → `tauri build --no-bundle --features mas` → `tauri bundle --bundles app --features mas --config …` (gleiche Features, ohne `APPLE_*`-Variablen, sonst notarisiert Tauri) → `.app` nach `target/release/bundle/mas/` kopieren → Prüfungen (`codesign --verify --deep --strict`, Entitlements der Hülle und von `python3`, Profil im Bundle, world-readable) → `xcrun productbuild --sign "<Installer-CN>" --component App.app /Applications App.pkg` → `pkgutil --check-signature` → `xcrun altool --validate-app` → mit `--upload` `altool --upload-package … --api-key … --api-issuer …`. Die genauen altool-Flags (`-t macos`, `--apple-id`) erst mit `--validate-app` austesten; altool ist für Uploads weiterhin gültig (nur Notarisierung abgeschaltet). Keine Notarisierung im Store-Pfad.
4. `package.json`: `release:mas` neben `release`; Reihenfolge erst DMG, dann MAS (beide Läufe signieren `resources/` neu — im Log unübersehbar machen).
5. **TestFlight:** Tester macOS 13+, erster Build durch Beta App Review, 90 Tage gültig. Der Store-Build ist der TestFlight-Build. Frühe Einreichung nach Phase 3.1–3.4 (noch vor vollständigen Datei-Flüssen) liefert die Antwort auf `Resources`-Layout und ITMS-90296.
6. arm64-only ist zulässig (Apple 1.9.2026: ab macOS 13; `minimumSystemVersion` 14.0). Grösse 1,7 GB gegen 200-GB-Limit unkritisch. CI erst nach lokalem Erstupload (resources/ 1,7 GB aus drei Quellen).

## 6. Phase 4 «App Store Connect» (1–2 PT)

**Metadaten-Checkliste**

| Feld | Vorgabe | Stand |
|---|---|---|
| Name | «ResearchTranscript» (18/30 Z.) | Suche ohne Treffer; verbindlich nur der App-Record |
| Untertitel | ≤30 Z., keine Fremd-Apps, keine Preise (2.3.7) | z. B. «Lokale Interview-Transkription» |
| Kategorie | Primär Productivity, sekundär Business; muss mit `LSApplicationCategoryType` im Bundle übereinstimmen | fehlt in `tauri.conf.json` |
| Preis | 0 | – |
| Altersfreigabe | 4+ (neuer Fragebogen) | – |
| App Privacy | «Data Not Collected» — `user_email`/`install_id` bleiben lokal, nur in selbst exportierten Dossiers | korrekt; in Notes erklären |
| Privacy-Policy-URL | Pflicht in ASC **und** In-App-Link (5.1.1(i)) | **fehlt** → `site/privacy.html` viersprachig + Knopf in `EinstellungenModule.tsx` (Karte `st.datenschutz`, Z. 202–203) und im `UeberDialog` (`App.tsx`, Z. 201–211) |
| Support-URL | «actual contact information» | `#contact` hat nur LinkedIn/GitHub → E-Mail ergänzen |
| Copyright | «2026 B/IAS – Basel Institut für angewandte Stadtforschung» | – |
| Keywords | ohne MacWhisper/Aiko/Buzz | – |
| Export-Compliance | OpenSSL ist **enthalten** (libpython 3.5.6 statisch, ffmpeg 3.6.1) → ASC «uses encryption: yes», Standardalgorithmen = exempt; `ITSAppUsesNonExemptEncryption=false` vermutlich richtig; französische Deklaration bei FR-Vertrieb, Self-Classification-Report klären (unsicher) | LGPL-ffmpeg ohne OpenSSL halbiert das Thema |
| EULA | Custom EULA mit Apples Mindestbedingungen, ohne RE-Verbot | – |

**Screenshots:** 1–10, 16:10, exakt 1280×800 / 1440×900 / 2560×1600 / 2880×1800, PNG/JPG ohne Alpha, «App in Benutzung», 4+-tauglich. Motive aus `docs/screenshots` (6 PNG, erfundenes Interview): Batch, Bibliothek, Editor, Suchen/Ersetzen, Export, Einstellungen; je Sprache de/en/fr/it; Pixelmasse vor Upload nachmessen.

**Review-Notes-Entwurf (≤4000 Byte):**

> ResearchTranscript works fully offline: no account, no login, no server, no telemetry. Architecture: the UI is a WKWebView; the transcription backend is a bundled child process (Python/uvicorn) listening only on 127.0.0.1:5628 (hence com.apple.security.network.server/client); it is started and terminated by the app itself and cannot be reached from the network. All speech models (whisper.cpp large-v3-turbo, SpeakerKit) ship inside the bundle; the app never downloads code or models. The optional e-mail field is written only into dossier files the user exports themselves; it is never transmitted. Zotero integration is optional, read-only and local. Demo: the attached zip contains a 2-minute synthetic interview (two invented speakers). Steps: drag the file into the "AI Transcript" tab → speakers: 2 → Start → about one minute on Apple silicon. Requires Apple silicon (Neural Engine for diarisation), macOS 14+. Licence: AGPL-3.0 with an App Store additional permission; FFmpeg (LGPL) sources linked from the About dialog. Contact: +41 … 

## 7. Risiken und offene Fragen (priorisiert)

1. **Review-Ausgang lokaler HTTP-Server + CPython** (unbelegt; GeoLibre unter 2.4.5 abgelehnt). Klärung: früher TestFlight-Build; in Notes den Loopback-Zweck vorab erklären; Token auf allen Endpunkten.
2. **Doppelte Dateizugriffs-Schranke** (Hülle→Python, Python→ffmpeg/argmax). Klärung: Phase 0 M2–M4; Container-Bibliothek umgeht sie vollständig.
3. **Executables in `Contents/Resources`** vs. Tauris Signierkonflikt bei `externalBin`. Klärung: `altool --validate-app` mit vorsigniertem Resources-Layout; sonst Nachsignieren nach `tauri build` + Bundle neu versiegeln.
4. **ffmpeg-Wechsel** auf LGPL: Regressionstest der sechs Aufrufstellen, Prüfung LAME/securetransport/openssl im Buildconf.
5. **Bibliothek im Container** ist für Nutzer unsichtbar, nicht in iCloud; Bestandsnutzer starten leer. Klärung: Import-Weg + Erklärung in Einstellungen; externe Bibliothek per Bookmark als Phase 2 nach Spike.
6. **Zotero**: Bookmark-Spiegel vs. Local-API — Entscheidung des Users nach M4.
7. **Zwei Builds, gleiche Bundle-ID** (Developer ID vs. Apple Distribution) lösen ab macOS 14 die Container-Nachfrage aus. Klärung: eigene Bundle-ID für den Dev-Build oder akzeptieren.
8. **Export-Compliance / OpenSSL**: BIS-Self-Classification klären; ffmpeg ohne OpenSSL beziehen.
9. **Modell-Nachladen** wäre nach 2.4.5(iv) («resources to add functionality») heikel — Modelle bleiben im Bundle.
10. **Drag&Drop im Sandbox** (Tregaskis-Effekt, unsicher): M3; Fallback Open-Panel.
11. **Hardened Runtime aus** im Store-Build: zulässig, ungewöhnlich; falls Review nachfragt, mit `cs.*`-freien Entitlements wieder einschalten (Test M5 zeigt, dass keine Ausnahme nötig ist).

## 8. Reihenfolge und Zeitplan

| Woche | Schritte | Ergebnis | Entscheidungspunkt |
|---|---|---|---|
| 1 | Phase 0 Spike; Zertifikate/Profil beantragen; Privacy-Seite + Support-E-Mail; `bundle.category` | M1–M6 dokumentiert; Portal bereit | **Weiter oder pausieren** (M1/M5) |
| 2 | 3.1 Prozessmodell, 3.4 Entitlements/Signatur, venv abschaffen; LGPL-ffmpeg beziehen und regressionstesten | Sandbox-Build startet, Backend token-gesichert | Layout Resources vs. MacOS (nach `--validate-app`) |
| 3 | 3.2 Datei-Flüsse (Container-Bibliothek, Übernahme/Ablage), 3.5 Tests; `release-mas.mjs`; erster TestFlight-Upload | Interner TestFlight-Build | ITMS-Fehler / Beta-Review-Rückmeldung |
| 4 | 3.3 Zotero; `LICENSE-EXCEPTION`, `resources/licenses/`, i18n-Lizenztexte korrigieren; Rechtsprüfung anstossen; Screenshots, Metadaten, Review-Notes | Einreichfähiger Build | Rechtsfreigabe Ausnahme + EULA |
| 5–6 | Review-Einreichung; Nacharbeiten; DMG-Release mit LGPL-ffmpeg + Quell-Tarball parallel | Store-Freigabe oder begründete Ablehnung | Parallelvertrieb DMG/MAS dauerhaft? |

## 9. Quellen

- Apple, Entitlement Key Reference (Sandbox-Vererbung, «exactly two keys», Bookmark-Übergabe): https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/EnablingAppSandbox.html
- Apple, Accessing files from the macOS App Sandbox: https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox
- Apple, Embedding a helper tool in a sandboxed app: https://developer.apple.com/documentation/xcode/embedding-a-helper-tool-in-a-sandboxed-app
- Apple, Embedding nonstandard code structures / Placing content in a bundle / TN2206: https://developer.apple.com/documentation/xcode/embedding-nonstandard-code-structures-in-a-bundle · https://developer.apple.com/documentation/bundleresources/placing-content-in-a-bundle · https://developer.apple.com/library/archive/technotes/tn2206/_index.html
- Apple DTS (Quinn) zu ps/lsof/kill, Sandbox-Extensions, Loopback, Env-Weitergabe: https://developer.apple.com/forums/thread/776473 · /691857 · /664479 · /678819 · /111125 · /703358 · /766290 · /799357 · /654579 · /706390 · /763498
- Apple, Entitlements network.server, cs.* : https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.network.server · …/com.apple.security.cs.disable-library-validation · …/com.apple.security.cs.allow-jit
- App Store Review Guidelines: https://developer.apple.com/app-store/review/guidelines/
- App Store Connect Help (Upload, TestFlight, Grössen, Screenshots, Export-Compliance, Privacy): https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds · https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview · https://developer.apple.com/help/app-store-connect/reference/maximum-build-file-sizes/ · https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications/ · https://developer.apple.com/help/app-store-connect/reference/app-information/export-compliance-documentation-for-encryption/ · https://developer.apple.com/app-store/app-privacy-details/
- TN3147 (altool nur für Notarisierung abgeschaltet): https://developer.apple.com/documentation/technotes/tn3147-migrating-to-the-latest-notarization-tool
- Apple, arm64-only im Mac App Store: https://developer.apple.com/app-store/whats-new/
- Tauri: App-Store-Guide, Config, Sidecar, Issues 3716 / 13118 / 15144 / 15230, tauri-docs 3171: https://v2.tauri.app/distribute/app-store/ · https://v2.tauri.app/develop/configuration-files/ · https://github.com/tauri-apps/tauri/issues/3716 · /13118 · /15144 · /15230 · https://github.com/tauri-apps/tauri-docs/issues/3171
- Tauri-Bundler/Sign-Quellen: https://raw.githubusercontent.com/tauri-apps/tauri/tauri-cli-v2.11.4/crates/tauri-bundler/src/bundle/macos/app.rs · …/sign.rs · https://raw.githubusercontent.com/tauri-apps/tauri/dev/crates/tauri-macos-sign/src/keychain.rs
- wry Drag&Drop / Tregaskis: https://github.com/tauri-apps/wry/blob/dev/src/wkwebview/drag_drop.rs · https://wadetregaskis.com/mac-app-sandboxing-interferes-with-drag-drop/
- GeoLibre MAS-Erfahrung: https://geolibre.app/mac-app-store/
- Twocanoes / Timac / MailVault (Helfer-Signatur, Bookmarks): https://twocanoes.com/adding-a-command-line-tool-helper-to-a-mac-app-store-app/ · https://blog.timac.org/2021/0516-mac-app-store-embedding-a-command-line-tool-using-paths-as-arguments/ · https://mailvaultapp.com/blog/sandbox-signing-saga.html
- Lizenzen: https://www.fsf.org/news/2010-05-app-store-compliance · https://www.fsf.org/blogs/licensing/left-wondering-why-vlc-relicensed-some-code-to-lgpl · https://www.videolan.org/press/lgpl-libvlc.html · https://www.apple.com/legal/macapps/minterms/ · https://www.apple.com/legal/internet-services/itunes/dev/stdeula/ · https://www.gnu.org/licenses/gpl-faq.en.html · https://raw.githubusercontent.com/narrowstacks/dorkroom/main/LICENSE-EXCEPTION · https://raw.githubusercontent.com/nextcloud/ios/master/COPYING.iOS · https://ffmpeg.org/legal.html · https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/configure · https://github.com/Nothing-Software/FFmpeg-Builds · https://huggingface.co/pyannote/segmentation-3.0/blob/main/LICENSE · https://github.com/wenet-e2e/wespeaker/blob/master/docs/pretrained.md · https://raw.githubusercontent.com/argmaxinc/argmax-oss-swift/main/NOTICES · https://raw.githubusercontent.com/astral-sh/python-build-standalone/main/docs/running.rst
- Zotero Local API: https://www.zotero.org/support/dev/web_api/v3/local_api
- uvicorn `--fd` / `--port 0`: https://uvicorn.dev/settings/
