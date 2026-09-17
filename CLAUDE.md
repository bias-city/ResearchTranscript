# ResearchTranscript (vormals LocalTranscript, dann TurnScript)

Umbenennungen 2026-09-14/16 (User): LocalTranscript → TurnScript →
ResearchTranscript, Versionszählung neu ab 0.4.0 (wie enrich-core 0.1.0,
PrepareAudio 0.2.0). Bundle `city.bias.researchtranscript`, Python-Paket
`researchtranscript`, Repo github.com/bias-city/ResearchTranscript.
KEINE Übernahme alter Einstellungen (User-Entscheid): die App startet
frisch und fragt nach dem Bibliotheksordner.
Unverändert und bewusst: Port 5628 (nur noch Dev-Server), `LT_*`-Umgebungsvariablen,
`lt.*`-Speicherschlüssel, die QDPX-GUID-Namensräume
(`localtranscript:refi-*`), `EIGENE_TOOLS` mit beiden Altnamen und das
Schlüsselbund-Profil `localtranscript`. Diese Stellen NIE pauschal
umbenennen — `tests/test_kompatibilitaet.py` wacht darüber.

Side-Projekt von enrich (User-Auftrag 2026-08-30): Neubau des
Electron-Prototyps `../whisper-web` als Tauri-App. Plan:
~/.claude/plans/localtranscript-tauri.md. README.md = Architektur.

## Eiserne Regeln (geerbt aus enrich, gelten hier)

- UI NUR über `frontend/src/components/ui.tsx` (enrich-Kit-Kopie);
  Icons nur über `components/icons.tsx`; Strings nur über
  `lib/i18n.ts` — VIERSPRACHIG de/en/fr/it, de = Quellsprache.
- Timecodes IMMER hh:mm:ss (User: „unbedingt").
- `transkript.json` ist die kanonische Wahrheit; Exporte sind
  abgeleitet. Schreiben immer atomar + history/-Snapshot; Löschen =
  `_papierkorb/`, nie destruktiv.
- `backend/src/researchtranscript/enrich_export/turns.py` ist VENDOR-Code
  (nur noch turns.py — textsatz/schrift/fonts sind seit 2.3.0 weg, der
  Export setzt kein PDF mehr, FORMAT.md §5)
  (enrich@3d2b131): nie formatieren/fixen (ruff-exclude!), Drift-Guard
  `tests/test_drift_guard.py` vergleicht gegen `../enrich`. Bei
  enrich-Änderungen an textsatz/textimport: neu vendoren (Kopf-
  kommentar sagt wie).
- Seit 0.5.0 (Branch `eingebettet-spike`, Plan docs/appstore-plan.md)
  läuft Python IM PROZESS der Hülle (PyO3): kein Port, kein Kind
  `python3`, keine Merkdatei. Die Oberfläche ruft `invoke("api",
  {name, args})`; `main.py` ist nur noch Dev-Server/Test-Hülle auf
  5628 („LOCT", `LT_SERVE_PORT`). Regeln in `src-tauri/src/python.rs`-
  Kopf: nie `Python::attach` auf dem Hauptthread, Befehle `async` →
  `spawn_blocking`, nie `Py_FinalizeEx`. Jede Transport-/Medien-/
  Dialog-Änderung im gebauten Bundle prüfen (nicht nur im Browser).
  Bauen: `node scripts/bundle-resources.mjs` (python/site-packages,
  kein venv) → `sign-resources.mjs` → `PYO3_CONFIG_FILE=… tauri build`.
- Recursive-Fonts (nur noch auf der Website, site/fonts): SIL OFL 1.1 — Nennung dort und
  bei jeder Veröffentlichung.

## Stand 2026-08-30 (Erstbau, eine Session)

Backend komplett (15 Tests grün, whisper-/ffmpeg-frei über Fakes):
bibliothek/jobs/transcribe/diarize/ausgabe/exporte/main. v1-Bugs
gefixt statt portiert: .wav-Resample-Bypass, nicht-idempotentes
Sprecher-Umbenennen (strukturell weg), Job-Abbruch killt Prozesse.
Frontend komplett (tsc+vite grün, Playwright-verifiziert an echtem
3,4-h-Workshop: 1148 Segmente/8 Sprecher). enrich-Export am selben
Material: 8 s, 73-Seiten-PDF, Zeitkarte, Kette narrativ. Tauri-Shell
kompiliert; Bundle über scripts/bundle-resources.mjs (übernimmt
python-runtime/bin/lib/models aus ../whisper-web, venv frisch).

Bewusst NICHT portiert: HF-Token-Screen (tot), PyWebView (app.py),
~⅔ von merge.py (tote Token-Matching-Architektur), Glossar/NER
(war im UI unerreichbar; Wiederaufnahme möglich — Code in
../whisper-web/backend/glossary.py).

## Test/Dev

`cd backend && uv run pytest` · `uv run ruff check src tests` ·
Frontend `npx tsc && npm run build`. Browser-Demo: uvicorn auf 5628
mit `LT_CONFIG_DIR`-Scratch (Muster in tests/conftest.py). App-Test
ohne echte Bibliothek: `LT_CONFIG_DIR=<scratch> <App>/Contents/MacOS/
researchtranscript-app`; Protokoll unter
~/Library/Logs/city.bias.researchtranscript/researchtranscript.log.
Echte Transkript-Beispiele: ~/Documents/LocalTranscript/<stamp>/.

## Abend-Runde 2026-08-30 (Live-Feedback + Multi-Agent-Review)

Multi-Agent-Review (36 Agenten, 6 Dimensionen + adversariale
Gegenprüfung): 30 Befunde, 25 bestätigt (19 nach Dedup), 5 widerlegt —
ALLE behoben. Schwerste: Autosave-Verlust beim Verlassen (Flush beim
Unmount), fehlendes CORS (Tauri-Origin tauri://localhost ist
CROSS-origin zu 127.0.0.1:5628 — Allowlist in main.py; der
Vite-Proxy kaschierte das im Browser-Dev!), Export-Pfad konnte
beliebige Dateien überschreiben (Format-Endung Pflicht) + Host-Wache
gegen DNS-Rebinding (421). Shell: Quit beendet NUR Selbstgestartetes,
backend_starten async, venv_fixen laut. Bundle: Tauri DEREFERENZIERT
venv-Symlinks — libpython3.13.dylib liegt zusätzlich in venv/lib
(sonst dyld-Abbruch); bundle-resources.mjs spielt researchtranscript+
enrich-core bei JEDEM Lauf frisch ein.
Live-Befunde des Users: Datenschutz-Karte (lokal, keine Cloud — v1s
„24h"-Zeile war irreführend) · UI auch via http://127.0.0.1:5628
(dist in Resources) · Dateinamen mittig gekürzt (kuerze()) ·
.enrich-Audio IMMER mp3 (ffmpeg q2) · VTT-Export mit Standard-
Voice-Tags <v Name> statt Text-Präfix (Import kann beide Stile) ·
EDITOR-PERF 22,5 s → 55 ms je 6 Zeichen bei 1148 Zeilen (Autohöhe nur
Mount+Input, memo mit abgeleiteten Props, leichter Badge-Knopf + EIN
geteiltes Sprecher-Menü statt Radix-Select je Zeile, Umbenennen
debounced-Commit). 19 Backend-Tests grün.
