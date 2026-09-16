<!-- Erzeugt am 2026-09-17 aus dem zweiten Multi-Agenten-Lauf (sechs Dimensionen,
     sechs adversariale Gegenprüfungen) für Variante A. Ersetzt docs/appstore-plan.md
     in den Abschnitten Prozessmodell, Sandbox-Spike und Datei-Flüsse; übernimmt
     dessen Lizenzen, Entitlements, Bau-Kette, Metadaten und Review-Notizen.
     Aufwände sind Schätzungen in Personentagen (PT). -->

# ResearchTranscript, Variante A: eingebettetes Python und Motor-Schicht, Mac App Store

Stand 2026-09-17, Version 0.4.0. Gebaut wird **nur der Mac** (Apple silicon, macOS 14+). Windows und Linux werden in Abschnitt 7 offen gehalten, nicht gebaut.

## 1. Kurzfassung

- **Zielbild:** Tauri-Hülle + React bleiben. CPython 3.13 (python-build-standalone, schon im Bundle) läuft per PyO3 **im Prozess der Hülle**; die Oberfläche ruft Tauri-Befehle statt HTTP. Whisper, Sprechertrennung und Ton laufen hinter einer Motor-Schicht (Rust-Traits) mit je **einer** Umsetzung: whisper-rs/Metal, SpeakerKit/Core ML, AVFoundation + LAME.
- **Es fällt weg:** Port 5628 in der App, uvicorn/FastAPI im Bundle, `network.server/client`, Kindprozesse `python3`/`whisper-cli`/`ffmpeg` (GPLv3-Problem gelöst), die Vererbungsschranke Hülle→Kind (Powerbox-/Drop-Freigaben gelten im Prozess auch für Python), `lsof/ps/kill`, Merkdatei, `venv_fixen`, Host-Wache, CORS, alle vier `cs.*`-Ausnahmen (im Spike ohne sie verifiziert).
- **Belegt:** Ein PyO3-0.29-Spike startet die gebündelte Laufzeit isoliert in 4–22 ms, importiert `researchtranscript` + `pydantic_core` + `enrich_core` in ~50 ms, lässt `jobs.py`-Threads neben Rust laufen und bricht Jobs ab — signiert mit Hardened Runtime, ohne Entitlements.
- **Gesamtaufwand nur Mac:** ca. 34–43 PT Entwicklung (Phase 0: 2, Phase 1: 12–14, Phase 2: 12–16, Phase 3: 8–11) plus Zertifikate, Rechtsprüfung, TestFlight-Zyklen. Schätzung.
- **Grösstes Risiko:** Kein belegter Store-Freigabefall für «Tauri + eingebettetes CPython». Belegt sind nur die Teile: GeoLibre (Tauri, App Sandbox, ohne `network.server`) ist freigegeben, CPython sieht den Store in seiner Doku (§5.5.4) ausdrücklich vor. Zweitgrösstes: ein Absturz in C/C++/Swift reisst jetzt die ganze App mit.
- **Empfehlung:** Phase 0 (2 Tage) zuerst; dann in dieser Reihenfolge Brücke (0.5.0, DMG), Motoren (0.6.0), Store (0.7.0). Früher TestFlight-Build nach Phase 1, nicht erst nach Phase 2. Kompromisse zugunsten des Mac sind gewollt und je markiert **[Kompromiss]**.

## 2. Zielarchitektur

```
React (frontend/src)            invoke("api", {name,args}) · listen("job") · rtmedia://localhost/<eid>/audio
   │
Tauri-Befehle (src-tauri/src/lib.rs, python.rs, medien.rs)   async fn → spawn_blocking → Python::attach
   │
PyO3-Brücke (python.rs)          PyConfig isoliert · PyOnceLock<api-Modul> · JSON rein/raus · Beobachter-Callback
   │
Python-Logik (backend/src/researchtranscript)   api.py (Fassade) · jobs · bibliothek · exporte · format2 · qdpx · zotero
   │                                            main.py bleibt dünne HTTP-Hülle für Browser-Dev und pytest
Motor-Schicht (src-tauri/src/motoren/*)          #[pymodule] researchtranscript_motoren via append_to_inittab
   ├─ Ton:          AVFoundation (Dekodierung, Sondierung) + libmp3lame (MP3)        [Kompromiss]
   ├─ Whisper:      whisper-rs 0.16, Feature metal, statisch
   └─ Sprecher:     SpeakerKit (Core ML) — Swift-Shim im Prozess ODER argmax-cli als Kind (E5)
```

**Rust-Trait-Skizze** (Eingabe immer f32-Samples 16 kHz mono; Fortschritt und Abbruch einheitlich; jede Rechnung läuft in `py.detach`):

```rust
pub type Abbruch = Arc<AtomicBool>;
pub struct Fortschritt { pub anteil: f32, pub text: Option<String> }
pub struct MedienInfo { pub video_codec: Option<String>, pub audio_codec: Option<String>,
                        pub breite: Option<u32>, pub hoehe: Option<u32>, pub dauer_s: Option<f64> }
pub struct Segment { pub start: f64, pub end: f64, pub text: String, pub no_speech_prob: f32 }
pub struct SprecherSegment { pub start: f64, pub end: f64, pub sprecher: String }

pub trait Ton: Send + Sync {
    fn sondiere(&self, pfad: &Path) -> Result<MedienInfo>;                                   // video.sondiere
    fn dekodiere_16k(&self, pfad: &Path, ab: &Abbruch, f: &mut (dyn FnMut(Fortschritt) + Send)) -> Result<Vec<f32>>; // jobs._konvertiere
    fn nach_mp3(&self, pfad: &Path, ziel: &Path, vbr_q: u8, ab: &Abbruch) -> Result<()>;    // video.ton_befehl, exporte
    fn schreibe_wav16k(&self, a: &[f32], ziel: &Path) -> Result<()>;                        // Hörprobe, Kind-Eingabe
}
pub struct TranskriptionsOptionen { pub sprache: String, pub vad_modell: Option<PathBuf>, pub threads: usize, pub live_text: bool }
pub trait Transkription: Send + Sync {
    fn lade(&mut self, ggml: &Path) -> Result<()>;                                           // Kontext je Modell cachen
    fn transkribiere(&self, a: &[f32], zeit_offset: f64, o: &TranskriptionsOptionen, ab: &Abbruch,
                     f: &mut (dyn FnMut(Fortschritt) + Send)) -> Result<Vec<Segment>>;      // eigener whisper_state je Job
}
pub struct TrennOptionen { pub sprecher: Option<u32>, pub ui_schwelle: f32 /* 0,25..0,7 */, pub exklusiv: bool }
pub trait Sprechertrennung: Send + Sync {
    fn trenne(&self, a: &[f32], o: &TrennOptionen, ab: &Abbruch, f: &mut (dyn FnMut(Fortschritt) + Send)) -> Result<Vec<SprecherSegment>>;
    fn name(&self) -> &'static str;                                                          // → by.diarization
}
pub struct Motoren { pub ton: Box<dyn Ton>, pub whisper: Box<dyn Transkription>, pub sprecher: Option<Box<dyn Sprechertrennung>> }
pub fn motoren() -> Motoren { /* heute genau eine Zusammenstellung: Mac */ }
```

**Bundle-Layout der Mac-App** (Apple «Placing content in a bundle»):

| Ort | Inhalt |
|---|---|
| `Contents/MacOS/ResearchTranscript` | Hülle mit statischem whisper.cpp/ggml-Metal (Shader eingebettet), Motor-Schicht, ggf. Swift-Shim; `LC_RPATH @executable_path/../Frameworks` |
| `Contents/Frameworks/` | `libpython3.13.dylib` (Install-Name schon `@rpath/…`), `libmp3lame.dylib`; über `bundle.macOS.frameworks` (Tauri kopiert .dylib-Pfade dorthin, nur im Bundler-Quellcode belegt) |
| `Contents/Resources/python/` | Stdlib `.py` + vorkompilierte `.pyc` (`compileall --invalidation-mode unchecked-hash`, weil `write_bytecode=0` und Bundle versiegelt), `site-packages` mit pydantic, pydantic_core (**einziges Mach-O in Resources**), enrich_core, researchtranscript; ohne pip (an beiden Orten), tk/tcl, `_tkinter`, `_dbm`, idlelib, ensurepip, `bin/` |
| `Contents/Resources/models/` | `ggml-large-v3-turbo.bin`, `vad/silero-v5.1.2.bin` (Umzug aus dem Python-Paket), `speakerkit/*.mlmodelc` |
| `Contents/Resources/bin/` | nur falls E5 = Kindprozess: `argmax-cli` mit `entitlements.child.plist` — sonst leer, kein Executable in Resources |

## 3. Phase 0 «Versuchs-Branch» (`eingebettet-spike`, 1–2 PT)

`tauri dev` honoriert Sandbox-Entitlements nicht (Tauri-Issue 15144) — alles am **signierten Build** messen, Zertifikat «Apple Development» genügt, `log stream --predicate 'sender == "Sandbox"'` mitlaufen lassen.

**F1 – Eingebettetes Python im signierten Sandbox-Bundle.** Den gesicherten Spike `spike/pyo3/` (`src/main.rs`: `PyConfig_InitIsolatedConfig`, `home`, `module_search_paths_set=1`, `site_import=0`, `write_bytecode=0`, `Py_InitializeFromConfig`, `PyEval_SaveThread`) in `frontend/src-tauri` übernehmen; `PYO3_CONFIG_FILE` auf die gebündelte Laufzeit; `build.rs` mit rpath `@executable_path/../Frameworks`; libpython über `bundle.macOS.frameworks`; `entitlements.spike.plist` = `app-sandbox` + `files.user-selected.read-write`, **ohne** `cs.*`, **ohne** `network.*`; Hardened Runtime an. Messen: Befehl `health` liefert die Version; Fenster < 2 s nach Klick; Import von `researchtranscript.api` + `enrich_core`; ein Fake-Job (`jobs.py`, 4 parallel) läuft, Polling alle 500 ms, Abbruch < 1 s, 20 min ohne Hänger; Ordner per Open-Panel wählen → Python (nicht Rust!) listet und schreibt darin (Vererbung im Prozess); `codesign -d --entitlements -` auf Hülle und Frameworks.

**F2 – Medienwiedergabe mit Seeking in WKWebView.** Eigenes Schema `rtmedia://localhost/<eid>/audio|video` per `register_asynchronous_uri_scheme_protocol`, Range-Handler nach `examples/streaming/main.rs`, aber: `Accept-Ranges: bytes` setzen, Blockdeckel 4 MB, bei Anfrage **ohne** Range nur den ersten Block als 206 liefern (nicht die ganze Datei — asset.rs und das Beispiel tun genau das); eid→Pfad aus einer Rust-Map, die der `api`-Befehl beim Öffnen füllt (kein Python im Handler-Thread). Handler-Logging jeder Anfrage. Messen am 3,4-h-Workshop-mp3 und am 4K-HEVC-Video (`preload="auto"` wie heute in `EditorModule.tsx:1234`): schickt WebKit beim ersten Laden Range? Sprünge an fünf Stellen ohne Stall, Bild folgt dem Ton < 0,25 s (BACKLOG Nr. 8). Gegenprobe: `asset://` mit `convertFileSrc` (1-MB-Deckel) am selben Material.

**F3 – SpeakerKit im Prozess oder als Kind.** Ein Tag für ein SwiftPM-Paket `swift/SpeakerKitShim` (hängt an argmax-oss-swift Commit `ea872ff` wie `hole-argmax.mjs`), `@_cdecl("rt_diarize")(samples, n, num_speakers, threshold, exclusive, model_dir, progress_cb) -> JSON`, `async diarize` per Semaphore synchronisiert, `progressCallback` durchgereicht (existiert: `PyannoteDiarizer` meldet 0–100 ohne Rücksprünge); Linken über `swift-rs 1.0.8` in `build.rs`. Messen: gleiche RTTM wie `argmax-cli` an der 5-min-Feldaufnahme vom 13.9., Laufzeit ≤ 1,5×, Core ML unter Sandbox ohne Entitlement. Parallel: `argmax-cli` als Kind mit exakt `app-sandbox` + `inherit` auf ein WAV in `$TMPDIR` (liegt im Container) — läuft das?

**Nebenmessung M4 (Ton):** `AVAssetReader` liefert 16-kHz-mono-f32 aus m4a/mp3/flac/mov; `AVAsset`-Tracks liefern Codec-Tag, Masse, Dauer; **MP3-Kodierung** über `libmp3lame.dylib` aus `Contents/Frameworks` unter Sandbox. Zusatz: `AudioConverter` mit `kAudioFormatMPEGLayer3` als Encoder probieren (Apples Formattabelle sagt «decode only», Quelle alt — falls Apple doch kodiert, entfällt LAME).

**Abbruchkriterium:** F1 scheitert nach einem dokumentierten Tag → Variante A pausieren, Befund in `docs/`, zurück zum Kindprozess-Plan. F2 scheitert → eigenes Schema durch `asset://` ersetzen; scheitert auch das, bleibt Medien-per-HTTP nur für den DMG-Kanal tragbar und blockiert den Store — Entscheid vor Phase 1. F3: Shim in einem Tag nicht lauffähig → **Kindprozess** (E5), Shim wird Backlog.

## 4. Phase 1 «Brücke und Befehle» (12–14 PT)

Ergebnis: 0.5.0 im DMG-Kanal — eingebettetes Python, keine HTTP-Verbindung in der App, Motoren noch als Kinder hinter dem Motor-Protokoll. Jeder Punkt einzeln mergebar.

| # | Datei | Änderung | PT | Abhängigkeit |
|---|---|---|---|---|
| 1.1 | `backend/tests/vertrag/*.json`, `scripts/vertrag-pruefen.mjs` (neu) | Vertrag einfrieren: Golden-JSON je Route aus `TestClient` (25 Routen, davon 3 Medien/Download ohne Befehl); Drift-Wächter Routen(`main.py`) ↔ Fassade(`api.py`) ↔ `api.ts` | 0,5 | – |
| 1.2 | `backend/src/researchtranscript/api.py` (neu), `main.py` | Funktions-Fassade über alle Routen (`health, models, settings_get/post, transcribe_path, jobs_liste, job_cancel, import_path, transcripts…, audio_pfad/video_pfad` (liefern Pfade), `sprecher_probe_bytes` (WAV-Bytes statt Temp-Datei), `export_datei`, `zotero_*`); Fehler `ApiFehler(status, detail)` mit **sechs** Statuscodes (400/404/409/422/424/500; 421 entfällt); Pydantic-Modelle hierher (Settings behält `extra="allow"`); **kein `fastapi`-Import in `api.py`**. `main.py` wird dünne HTTP-Hülle (Browser-Dev, Playwright, 49 der 86 Tests + `eintrag`-Fixture) | 1,5 | – |
| 1.3 | `backend/pyproject.toml` | `requires-python >=3.13`, `uv python pin 3.13` (Dev-venv ist heute 3.12, Bundle 3.13); `dependencies = [pydantic>=2.7, enrich-core]`; Extra `serve = [fastapi, uvicorn (ohne [standard]), python-multipart]`; Dev-Gruppe zieht `serve` (sonst bricht `conftest.py`) | 0,2 | – |
| 1.4 | `backend/src/researchtranscript/motor.py` (neu), `jobs.py`, `transcribe.py`, `diarize.py`, `video.py`, `exporte.py`, `main.py` | Motor-Protokoll (`dekodiere_16k, sondiere, nach_mp3, schreibe_wav16k, transkribiere, trenne`) mit **erster Umsetzung = heutige Kindprozesse**, byteidentisch; deckt alle **zehn** Aufrufstellen (6 `Popen`, 4 `subprocess.run` — die `run`-Stellen sind heute nicht abbrechbar); das vorhandene `_CANCEL`-Event wird an den Motor durchgereicht; Tests faken das Protokoll (`LT_MOTOR=kind|fake`) statt privater Funktionen | 2,5 | 1.2 |
| 1.5 | `jobs.py` | `_setze()` ruft optionalen Beobachter `setze_beobachter(cb)` **gedrosselt** (≤ 10 Hz je Job; `partial_text` bis 4000 Zeichen je whisper-Zeile würde den IPC fluten); Threads `daemon=False`; `alle_abbrechen()` (Events, Kinder killen, join mit Frist) für den Exit | 0,3 | 1.4 |
| 1.6 | `config.py` | `get_app_root()`: `sys.frozen`-Zweig raus, `LT_APP_ROOT`/`LT_BUNDLED` **Pflicht** (von Rust vor `Py_InitializeFromConfig` gesetzt — `os.environ` friert beim `os`-Import ein); `is_embedded()`; jede `sys.executable`-Nutzung verboten (zeigt auf die Hülle); `PORT` nur für `main.py` | 0,2 | – |
| 1.7 | `frontend/src-tauri/Cargo.toml`, `build.rs`, `.cargo/config.toml`, `pyo3-config.txt` (erzeugt, gitignore) | `pyo3 = "0.29"` **ohne** `auto-initialize` (ein früher `Python::attach` würde mit Default-Pfadsuche initialisieren); `pyo3-build-config` (resolve-config); `PYO3_CONFIG_FILE` relativ (Muster tauri-plugin-python), Datei schreibt `bundle-resources.mjs` (lib_dir absolut, weil sysconfig `/install/lib` meldet); `build.rs`: Release `-Wl,-rpath,@executable_path/../Frameworks`, Debug `add_libpython_rpath_link_args()`; `crate-type` auf `rlib` (kein `extension-module`); tauri-Features `devtools` als eigenes Cargo-Feature, `protocol-asset` nicht nötig | 0,5 | – |
| 1.8 | `src/python.rs` (neu) | Aus dem Spike: `init(runtime, site_paths)`; `PyConfig_SetBytesString` für Strings (umgeht `wchar_t`); `PyOnceLock<Py<PyModule>>` für `researchtranscript.api` (nie `std::OnceLock` — Deadlock); `rufe(name, args: Value) -> Result<Value, ApiFehler>` mit Traceback im Fehler; Beobachter-Closure (`PyCFunction::new_closure`) → `app.emit("job", sicht)`; `alle_abbrechen()`; Python-`logging` → Rust `log` → Console.app (Isolated-Config konfiguriert keine C-Stdio, sonst ist der Release-Check blind); **kein `Py_FinalizeEx`** | 1,0 | 1.7 |
| 1.9 | `src/lib.rs` | ≈320 Zeilen Prozessverwaltung streichen (`port`, Merkdatei, `pid_lebt`, `health_antwortet`, `port_halter`, `ps_zeile`, `ist_eigenes_backend`, `vorgaenger_laeuft`, `beende_pid`, `venv_fixen`, `backend_finden`, `backend_starten`, Exit-Kill). Neu: `env::set_var(LT_*)` → `python::init` (ms, vor dem Builder) → Import in `spawn_blocking` (UI zeigt «startet»); Befehle **alle `async fn`** (synchrone laufen auf dem Cocoa-Hauptthread): `api(name,args)`, `job_abbrechen`, `sprecher_probe` → `tauri::ipc::Response` (rohe WAV-Bytes), `medien_registrieren(eid)`; `RunEvent::Exit` → `alle_abbrechen()`; `ordner_oeffnen` → `tauri_plugin_opener::reveal_item_in_dir`/`open_url` (neue Abhängigkeit); Menü und `RunEvent::Opened` bleiben | 1,5 | 1.8 |
| 1.10 | `src/medien.rs` (neu), `tauri.conf.json` | `rtmedia`-Schema aus F2; CSP `media-src 'self' blob: rtmedia:`, `connect-src` ohne `http://127.0.0.1:*`; Hörprobe als Blob-URL (`URL.createObjectURL`, `revokeObjectURL` in `stopp()`), kein Temp-Leck mehr | 1,5 | F2 |
| 1.11 | `frontend/src/lib/api.ts`, `lib/tauri.ts` | Transport-Schalter hinter unveränderten Signaturen: `isTauri()` → `invoke("api", {name,args})` mit `ApiFehler` → `Error(detail)`; Browser → `fetch`; `apiUpload` nur Browser (Zweige in `AiTranscriptModule:139`, `HumanEditorModule:84` unter `isTauri()` unerreichbar machen); neu `medienUrl(eid, art)`, `sprecherProbe(eid, sid)`, `onJobs(cb)` (Tauri: `listen("job")`, Browser: Intervall); `backendStarten` entfällt; `API_BASE`/localStorage-Override nur im Browserzweig | 1,0 | 1.9 |
| 1.12 | `EditorModule.tsx` (Z. 519/588/1124/1235), `AiTranscriptModule.tsx` (Z. 69–75), `App.tsx` | vier `API_BASE`-Stellen → `medienUrl`/`sprecherProbe`; Polling durch `onJobs` ersetzen, `GET jobs` nur beim Mount; Start-Sequenz ohne `backendStarten`, Init-Fehler aus dem Befehl | 0,5 | 1.11 |
| 1.13 | `scripts/bundle-resources.mjs` | venv abschaffen: `uv pip install --python resources/python-runtime/bin/python3 --exact enrich-core backend` direkt in `site-packages` (geprüft: uv erkennt die Laufzeit); Streichliste aus Abschnitt 2; Wächter: `find *.pth` → Abbruch (`site_import=0` verarbeitet keine), `otool -D libpython` muss `@rpath/…` sein; `compileall`; **App-Store-Compliance-Patch** (eine Zeile: `'itms-services'` aus `uses_netloc` in `urllib/parse.py`; python-build-standalone wendet ihn nicht an); `pyo3-config.txt` schreiben; `frameworks/`-Ordner; Smoke-Test per `cargo test` | 1,0 | 1.7 |
| 1.14 | `scripts/sign-resources.mjs`, `entitlements.plist` | Nur noch Mach-O in `python/` und `frameworks/` signieren, Bibliotheken ohne `--entitlements`; Zähler als Wächter (heute 27 Mach-O, danach ≈ 3 + ggf. `argmax-cli`); Kopfkommentar (253/torch) korrigieren; `entitlements.plist` = leeres Dict (Abschnitt 6) | 0,3 | 1.13 |
| 1.15 | `backend/tests/test_api.py` (neu), `src-tauri/tests/` | Fassade ohne HTTP (health, transcribe_path mit Fakes, Beobachter, `alle_abbrechen`); Rust-Integrationstest: `python::init` gegen `resources/python-runtime`, `api.health`; Vertragstest mit `tauri::test::mock_builder` + `get_ipc_response` gegen die Goldens | 1,0 | 1.1, 1.8 |
| 1.16 | `docs/`, `README.md`, `CLAUDE.md`, `vite.config.ts`, `i18n.ts:351` | Regel «UI auch via 127.0.0.1:5628» und «Shell beendet nur Selbstgestartetes» anpassen (Port bleibt Dev-Server); AGPL-§13-Text ohne Server; Proxy-Kommentar; Pflichtregel: jede Transport-/Medien-/Dialog-/Drop-Änderung in `tauri dev` prüfen (der Proxy hat CORS einmal kaschiert) | 0,5 | – |

**Route → Befehl:**

| Route (`main.py`) | Ziel in Variante A |
|---|---|
| GET health, models, settings; POST settings, transcribe-path, jobs/{id}/cancel, import-path; GET jobs, zotero/status, zotero/candidates?q=; POST/DELETE transcripts/{eid}/zotero; GET transcripts, transcripts/{eid}; PUT transcripts/{eid}; POST rename, delete, export (Pfad aus Save-Dialog) | `invoke("api", {name, args})` — dieselben Dicts, dieselben `{detail}`-Fehler |
| GET jobs (gepollt) | `api` beim Mount + Event `job` (gedrosselt) |
| GET jobs/{id} | vom Frontend ungenutzt — in der Fassade, kein Frontend-Code |
| GET transcripts/{eid}/audio, /video (FileResponse, Range) | `rtmedia://localhost/{eid}/audio|video` |
| GET …/sprecher/{sid}/sample (Temp-WAV + BackgroundTask) | Befehl `sprecher_probe` → `ipc::Response` → Blob-URL |
| POST transcribe, POST import (Multipart), GET …/export/{format} (Download), Static `/` | nur Browser-Betrieb, kein Befehl |

Grosse Nutzlasten (1148 Segmente) laufen durch vier JSON-Wandlungen; Latenz beim Editor-Öffnen messen, Ausweich `ipc::Response` mit rohem JSON-Text aus Python.

## 5. Phase 2 «Motor-Schicht, Mac» (12–16 PT)

Ergebnis: 0.6.0 — keine Kindprozesse ausser evtl. `argmax-cli`, kein ffmpeg im Bundle. Standardmotor bleibt `kind`, bis der Paritätstest grün ist (`LT_MOTOR`).

**Whisper im Prozess** (Entscheidung: **whisper-rs 0.16.0**, Feature `metal`, statisch; Kindprozess `whisper-cli` nur als Rückfall, 4–5 PT). Datei `src/motoren/whisper.rs`. Bindings hinken whisper.cpp hinterher (1.8.3 gegen 1.9.4; Bundle heute 1.8.2), Pflege auf Codeberg durch einen Maintainer — eigener Fork mit gepinntem whisper.cpp-Submodul ist wahrscheinlich Standardbetrieb, nicht Notfall. Flag-Äquivalenz: `WhisperContextParameters{use_gpu, flash_attn: true}` (**Bibliothek-Default ist false, CLI-Default true**), `set_language`, `BeamSearch{beam_size:5}`, `set_n_threads(4)`, `enable_vad` + `set_vad_model_path` + `WhisperVadParams::default()` (= CLI-Defaults), `set_progress_callback_safe`, `set_segment_callback_safe`, `set_abort_callback_safe` (vor jeder ggml-Berechnung geprüft). Segmentzugriff **nur** über `state.get_segment(i)` → `start_timestamp()/end_timestamp()` (Zentisekunden), `to_str_lossy()`, `no_speech_probability()`; Sprache `full_lang_id_from_state()` — die `full_get_segment_*`-API existiert in 0.16 nicht. `whisper_full` ist «not thread safe for same context»: bei `max_parallel` bis 4 je Job ein eigener `WhisperState` auf einem gecachten Kontext; Speicher (Modell 1,6 GB + Samples 3,4 h ≈ 780 MB f32) im Dauerlauf messen. Clip-Weg: Zeitstempel bei `set_offset_ms/set_duration_ms` sind absolut (whisper.cpp-Quelle); trotzdem Sample-Slices je Sprecherblock, damit VAD/Kontextgrenzen wie heute pro Block gelten — Gleichwertigkeit am 3,4-h-Workshop messen. Eigene ggml-Modelle (`<Bibliothek>/Modelle`, Magic `lmgg`, quantisierte q5_0/q8_0) bleiben unverändert; `get_vad_model()` auf `resources/models/vad/`. Kein Core ML für Whisper (1,17 GB Encoder, langsamer Erststart). **[Kompromiss]** Feature `metal`: ein Port setzt `vulkan`; alles andere ist plattformneutral. Build: `.cargo/config.toml` `-lc++ -l framework=Accelerate`, LLVM für bindgen.

**Sprechertrennung** (Entscheidung nach F3, **E5**). `src/motoren/sprecher_speakerkit.rs`.
(a) *Framework im Prozess* (Swift-Shim, 3–4 PT + 1 PT Signatur): kein Executable in `Resources`, kein Kind-Entitlement, echter Fortschritt, `clipTimestamps`/`minClusterSize` nutzbar; Risiken: kein belegter Tauri-macOS-Fall für swift-rs, Async-Brücke, Swift-Laufzeit-Linking (`LC_RPATH` auf die Xcode-Toolchain strippen wie heute in Plan §3.4), Core-ML-Inferenz nur kooperativ abbrechbar, Absturz reisst die App mit. Alternative mit fertiger C-FFI: `fluidaudio-rs 0.14.1` (andere Modellkopie, Qualitätsvergleich nötig).
(b) *Kindprozess* (`argmax-cli`, 0,5 PT): exakt `app-sandbox` + `inherit`, Eingabe ist ein 16-kHz-WAV, das die Motor-Schicht nach `$TMPDIR` (im Container) schreibt — das Kind berührt nie eine Nutzerdatei, die Vererbungsfrage entfällt; bleibt: ein Executable in `Contents/Resources` (Plan-Risiko 3, per `--validate-app` klären), Fortschritt zeitbasiert, `sign-resources.mjs` behält den Kind-Plist. Windows-Semantik von `returncode < 0` durch das Abbruch-Flag ersetzen.
Empfehlung: (a), wenn F3 in einem Tag steht; sonst (b) für 0.6.0 und (a) im Backlog. In beiden Fällen `_schwelle()` (UI 0,25–0,7 → VBx 0,45–0,75) nach Rust; `name()` → `by.diarization` = «SpeakerKit (pyannote-3.x-Segmenter + WeSpeaker + VBx)» — der In-App-Text «pyannote community-1» ist nicht sauber belegt (Segmenter/Embedder sind `pyannote-v3`, nur der Clusterer `pyannote-v4`). **[Kompromiss]** Core ML, Apple-silicon-only: ein Port bräuchte eine zweite Umsetzung des Traits.

**Ton** (Entscheidung: **AVFoundation + libmp3lame**, 4–5 PT; Datei `src/motoren/ton_avfoundation.rs`, Crate `objc2-av-foundation 0.3.2`). Begründung: AVFoundation dekodiert alles, was WKWebView spielt, dazu HE-AAC, ALAC, AMR (Diktier-Apps); `AVAsset`-Tracks ersetzen den `ffmpeg -i`-stderr-Regex in `video.sondiere` durch Codec-Tag/Masse/Dauer; kein Codec-Bundle, kein GPL/LGPL-ffmpeg, keine Neulink-Pflicht für 20–40 MB Shared-Libs. Grenze: MP3-Kodierung (Regel «.enrich-Audio IMMER mp3», Bibliotheks-Tonspur q2) kann Apple laut Formattabelle nicht («decode only», Quelle alt, in M4 gegenprüfen) → `libmp3lame.dylib` (LGPL, dynamisch in `Contents/Frameworks`, Quell-Tarball auf bias.city — vermeidet die LGPL-3-Relink-Pflicht von `mp3lame-sys` statisch) über `mp3lame-encoder`-API oder eigenes FFI. Sechs Aufrufstellen: `_konvertiere` → `dekodiere_16k` (Samples im Speicher, kein Temp-WAV), `_clip` → Sample-Slice, `ton_befehl`/`exporte` → `nach_mp3`, `sondiere` → `sondiere`, Hörprobe → Slice + `schreibe_wav16k`. Der Export (3,4 h MP3) läuft dann in einem Befehl: als Job führen oder in `detach`. `get_ffmpeg_cli` und der ffmpeg-Lizenzwächter entfallen; `.ogg`/Opus-Eingaben nur, wenn AVFoundation sie liest (Format-Matrix mit Fixtures, sonst CHANGELOG-Pflicht). **[Kompromiss]** AVFoundation ist macOS-only: ein Port ersetzt das Trait `Ton` durch LGPL-ffmpeg (`ffmpeg-next 9`, dynamisch) oder symphonia + rubato; die Schnittstelle bleibt.

**Weitere Regeln:** Jede Motorfunktion als `#[pyfunction]` kapselt die Rechnung in `py.detach` — sonst hält sie den GIL und friert jeden Befehl samt Abbruch ein. Abbruch = `AtomicBool`, den der Motor pollt (`Python::check_signals` ist ohne Signal-Handler wirkungslos). Zwei GPU-Nutzer (ggml-Metal, Core ML) neben der WebView im selben Prozess: `max_parallel` ggf. auf Prozessebene serialisieren. Autosave-Flush vor jedem Motorlauf (Absturz = App-Absturz). Tests: Fakes auf Ebene `researchtranscript_motoren`; Paritätsskript whisper-cli-JSON vs. In-Prozess-Segmente (Wortlaut, Zeitstempel ±50 ms, VAD wie 2.4.3); RTTM argmax-cli vs. Shim; Zahlen ins BACKLOG «Gemessen».

## 6. Phase 3 «Store-Fassung» (8–11 PT)

**Entitlements (zwei Dateien).** `frontend/src-tauri/entitlements.mas.plist` (Store): `com.apple.security.app-sandbox`, `com.apple.application-identifier` = `CCRJ4A42D3.city.bias.researchtranscript`, `com.apple.developer.team-identifier`, `com.apple.security.files.user-selected.read-write`, `com.apple.security.files.bookmarks.app-scope`. Keine `network.*` (GeoLibres Ablehnungsgrund, hier kein Socket), keine `cs.*` (alle Mach-O tragen die Team-ID, Library Validation besteht — im Spike verifiziert; CPython-JIT ist `yes-off` und unter Isolated-Config nicht einschaltbar — das im Code als Teil des Entitlement-Arguments kommentieren). Alle Schlüssel sind «unrestricted» (TN3125), Profil nur für TestFlight. `entitlements.plist` (Developer ID): **leeres Dict**, Hardened Runtime an — in beiden Kanälen (Plan-Risiko 11 entfällt); `allow-jit` nur nachrüsten, falls Metal/Core ML es im Laufzeittest verlangen (nicht erwartet, Systemdienste). Falls E5 = Kind: `entitlements.child.plist` exakt `app-sandbox` + `inherit` für `argmax-cli`. `codesign` bettet in dylibs keine Entitlements ein (empirisch geprüft) — Tauris `sign.rs` ist insofern harmlos. Tauri-Issue 15230 (Designated Requirement): `--requirements` nach `tauri build` auf die `.app` anwenden. Devtools: Cargo-Feature aus, Capability aus, Release-Profil (sonst bleibt der private `_inspector`-Code drin).

**Bookmarks im Prozess** (`src/bookmarks.rs`, `objc2-foundation`, 1,5 PT). Bibliothek **ausserhalb** des Containers ist jetzt möglich, weil `startAccessingSecurityScopedResource` die Sandbox des Prozesses erweitert — für Python, Core ML und Metal gleichermassen; Ordner-Freigaben gelten rekursiv (auch `<Bibliothek>/Modelle`). Empfehlung (User-Entscheid): beim ersten Start Ordnerdialog auf das echte `~/Documents/ResearchTranscript` + app-scoped Bookmark, Container-`Documents` nur als stiller Standard (für Nutzer unsichtbar, kein iCloud). Ein Start/Stop-Paar je Ordner und Sitzung (nie je Datei), Stop im `RunEvent::Exit`; gespeicherte Bookmarks erweitern die Sandbox **nicht** automatisch. Zotero: Ordnerdialog + Bookmark, `zotero_dir` explizit (gewinnt in `enrich_core.find_zotero_dir` immer), kein Spiegel, keine Local-API; `zotero.py`: `needs_folder: true` bis gesetzt, viersprachig. Drag&Drop (Tregaskis-Effekt in wrys `draggingEntered`) bleibt Prüfpunkt, Fallback Open-Panel. Export schreibt direkt an den Save-Panel-Pfad (`write_bytes`, `ZipFile(ziel)` — kein Temp+rename, geprüft). **[Kompromiss]** Bookmarks und Dateidialoge mit macOS-Mitteln: ein Port lässt `bookmarks.rs` als No-op (Pfade direkt).

**Bundle-Layout und Signierung:** wie Abschnitt 2; `sign-resources.mjs` signiert `pydantic_core.so` und Frameworks mit `--options runtime --timestamp`, ohne Entitlements; Kommentar korrigieren; Mach-O-Zähler als Wächter. Ob `--validate-app` das eine `.so` in `Resources` beanstandet, klärt nur der Probe-Upload (unsicher).

**Lizenzen** (Tabelle aus dem bisherigen Plan, angepasst):

| Bestandteil | Lizenz | Verdikt |
|---|---|---|
| Eigener Code (Backend, Frontend, Hülle, vendored `turns.py`) | AGPL-3.0-or-later | OK mit §7-Zusatzerlaubnis (Alleinurheberschaft per `git shortlog`) |
| enrich-core 0.1.0 · pydantic/pydantic-core · typing-extensions u. a. | MIT | OK |
| CPython 3.13 (python-build-standalone; OpenSSL statisch, libedit) | PSF-2.0 / Apache-2.0 | OK; Compliance-Patch anwenden |
| whisper.cpp/ggml (statisch via whisper-rs) · whisper-rs | MIT · Unlicense | OK |
| ggml-large-v3-turbo · silero-vad | MIT | OK — Silero-Ort im Inventar nach `resources/models/vad/` |
| SpeakerKit (argmax-oss-swift) | MIT + Apache-2.0-Teile | OK — NOTICE mitführen |
| SpeakerKit-Modelle | Segmenter pyannote/segmentation-3.0 MIT; Embedder WeSpeaker CC BY 4.0; Argmax gesamt CC BY 4.0 | OK — komponentengenau nennen |
| **libmp3lame** (dynamisch) | LGPL-2.1+ | OK — Quell-Tarball hosten, Nennung im Über-Dialog |
| AVFoundation | Apple-System-Framework | OK |
| ~~ffmpeg 9.0.1 (GPLv3)~~ | — | **entfällt** mit Phase 2 |
| npm-/Rust-Abhängigkeiten (MIT/ISC/Apache; MPL-2.0 in fünf Crates; `ffmpeg-next` kommt nicht mehr vor) | | OK — Inventar nach dem Umbau neu erzeugen (`cargo deny`/`npm ls`) |
| CC BY 4.0 / FairPlay | Modelle sind Ressourcen, keine Mach-O | OK (unsicher) |

**Zwischenstand für 0.5.0 (DMG):** ffmpeg bleibt bis Phase 2 ein Kind — dort **vor** 0.5.0 auf den LGPL-Build (Nothing-Software, `-buildconf` ohne `--enable-gpl/--enable-nonfree/--enable-openssl`) wechseln; das schliesst die GPL-§6-Lücke des heutigen DMG unabhängig vom Motor-Umbau. `LICENSE-EXCEPTION` (§7-Erlaubnis, Dorkroom-Muster, Kernklausel wie im bisherigen Plan §4), Hinweis in `main.py`/`main.tsx`/`lib.rs`, CONTRIBUTING-Regel, `resources/licenses/` + Knopf «Lizenzen» im Über-Dialog, Rechtsprüfung (FSFE Legal Network) für Ausnahme, EULA (Apples Mindestbedingungen, kein RE-Verbot) und LGPL-vs-Apple-Terms.

**Bau- und Upload-Kette** (aus dem bisherigen Plan §5, unverändert bis auf: kein `python3` mehr zu prüfen, Frameworks statt `bin/`): Portal (App-ID mit Sandbox, «Apple Distribution», «Mac Installer Distribution», Profil nach `profiles/`, API-Schlüssel); `tauri.macos-appstore.conf.json` (`bundle.category: "Productivity"`, `targets: ["app"]`, `signingIdentity`, `entitlements.mas.plist`, **`hardenedRuntime: true`**, `bundleVersion`, `embedded.provisionprofile`, `frameworks`); `scripts/release-mas.mjs`: `bundle-resources` → `sign-resources --mas` → `tauri build --no-bundle --features mas` → `tauri bundle --bundles app --features mas --config …` (ohne `APPLE_*`) → Prüfungen (`codesign --verify --deep --strict`, Entitlements der Hülle, Profil, world-readable, `otool -L` der Hülle zeigt nur `@rpath`/System) → `productbuild --sign` → `pkgutil --check-signature` → `altool --validate-app` → `--upload-package`. TestFlight: erster Build nach Phase 1 (Antwort auf `Resources`-Layout, ITMS-90296, Sandbox-Automatik); Tester macOS 14+, 90 Tage. arm64-only zulässig.

**App Store Connect** (bisheriger Plan §6, unverändert): Name «ResearchTranscript», Untertitel ≤ 30 Z., Productivity/Business = `LSApplicationCategoryType`, Preis 0, 4+, App Privacy «Data Not Collected» (`user_email`/`install_id` bleiben lokal), **Privacy-Policy-URL fehlt** → `site/privacy.html` viersprachig + Links in `EinstellungenModule.tsx` (Karte `st.datenschutz`) und `UeberDialog`; Support-E-Mail; Copyright «2026 B/IAS – Basel Institut für angewandte Stadtforschung»; Export-Compliance: OpenSSL nur noch in libpython (statisch) → «uses encryption: yes», exempt, `ITSAppUsesNonExemptEncryption=false` (unsicher, BIS-Self-Classification klären); EULA custom. Screenshots 1–10, 16:10, 1280×800…2880×1800, je Sprache, Motive aus `docs/screenshots`.

**Review-Notizen (Entwurf, ≤ 4000 Byte):**

> ResearchTranscript works fully offline: no account, no login, no server, no telemetry, no network entitlements. Architecture: the UI is a WKWebView; the application logic is written in Python and runs inside the app process through an embedded CPython 3.13 interpreter linked as a framework (no child process, no socket). The interpreter executes only the scripts shipped in the bundle (pip is not included); the app never downloads code, models or resources (2.5.2). Speech recognition (whisper.cpp large-v3-turbo, Metal) and speaker diarisation (SpeakerKit, Core ML) run in-process; audio decoding uses AVFoundation. All models ship inside the bundle. Files are accessed only through the Open/Save panels, drag & drop, or a user-chosen library folder kept as a security-scoped bookmark. The optional e-mail field is written only into dossier files the user exports; it is never transmitted. Zotero integration is optional, read-only, local, and requires the user to pick the Zotero folder. Demo: the attached zip contains a 2-minute synthetic interview (two invented speakers). Steps: drag the file into the "AI Transcript" tab → speakers: 2 → Start → about one minute on Apple silicon. Requires Apple silicon, macOS 14+. Licence: AGPL-3.0 with an App Store additional permission; LAME (LGPL) sources linked from the About dialog. Contact: +41 …

Falls E5 = Kind: Satz ergänzen «One bundled helper (argmax-cli, Core ML diarisation) is launched by the app with the sandbox inherit entitlement, reads only a temporary file inside the container, and terminates with the job.»

## 7. Offene Türen für Windows und Linux

Kein Aufwand, kein Zeitplan, nichts davon bauen. Regeln, die der Mac-Bau einhält:

1. **Motor-Schicht ist eine Schnittstelle mit genau einer Umsetzung.** Die Traits in `src/motoren/mod.rs` sind plattformneutral (Pfade, f32-Samples, `Abbruch`, `Fortschritt`); `motoren()` liefert heute die Mac-Zusammenstellung. Kein `cfg(target_os)` ausserhalb von `motoren/*_avfoundation.rs`, `*_speakerkit.rs`, `bookmarks.rs`, `medien.rs` (Schema-URL-Form) und dem Menü.
2. **Keine Mac-Pfade, keine Mac-Werkzeuge in der Python-Logik und in den Tauri-Befehlen.** Alle Speicherorte kommen von der Hülle (`app.path().app_config_dir/document_dir/app_cache_dir/resource_dir`) über `LT_CONFIG_DIR`, `LT_APP_ROOT`, neu `LT_DOCUMENTS_DIR`, `LT_CACHE_DIR`; Python rechnet keine `~/Library`-Pfade mehr. Kein `subprocess` in `researchtranscript` ausser über den Motor. Textdateien und Logs immer `encoding="utf-8"`.
3. **Plattform-Weichen** (Liste der Stellen; Ersatz-Satz je Kompromiss):

| Datei | Weiche | Was ein Port dort ersetzen müsste |
|---|---|---|
| `src/motoren/ton_avfoundation.rs` | **[Kompromiss]** Dekodierung/Sondierung über AVFoundation | zweite `Ton`-Umsetzung: LGPL-ffmpeg (`ffmpeg-next`, dynamisch) oder symphonia + rubato; MP3 bleibt LAME |
| `src/motoren/sprecher_speakerkit.rs` | **[Kompromiss]** Core ML / SpeakerKit, Apple-silicon-only | zweite `Sprechertrennung`-Umsetzung; der einzige belegte Kandidat wäre sherpa-onnx mit pyannote-segmentation-3.0 (andere Qualität, anderes Clustering) — hier nicht weiter verfolgt |
| `src/motoren/whisper.rs`, `Cargo.toml` | **[Kompromiss]** Feature `metal` | Feature `vulkan`, Vulkan-Loader als Laufzeitabhängigkeit; Bindgen/LLVM-Toolchain |
| `src/bookmarks.rs` | **[Kompromiss]** Security-Scoped Bookmarks, `NSURL` | No-op: Pfade direkt speichern |
| `src/medien.rs`, `tauri.conf.json` (CSP) | **[Kompromiss]** nur gegen WKWebView geprüft; URL-Form `rtmedia://localhost` | WebView2: `http://rtmedia.localhost`, Antwort muss vollständig vorliegen (Blockdeckel ist dort Pflicht); WebKitGTK: Medien über eigene Schemata sind als nicht funktionierend gemeldet — Rückfall Loopback-Medienserver nur für Audio/Video |
| `src/python.rs`, `build.rs`, `pyo3-config.txt` | rpath `@executable_path/../Frameworks`; `lib_name=python3.13` | Windows: `python3.dll` neben der exe, keine RUSTFLAGS, `lib_name=python313`; Linux: `$ORIGIN/../lib/<exe>/…`, AppImage verschiebt libpython; `PyConfig_SetBytesString` vermeidet die `wchar_t`-Breite bereits |
| `scripts/bundle-resources.mjs` | Laufzeit `aarch64-apple-darwin`, Compliance-Patch, Frameworks-Ordner | Plattform-Matrix mit `--target`; Stdlib-Layout `Lib\` (Windows) |
| `src/lib.rs` | macOS-Menü, `RunEvent::Opened` | Menü hinter `cfg`, Dateiöffnen per `argv` + single-instance; `bundle.fileAssociations` statt nur `Info.plist` |
| `backend/…/config.py` | `_config_dir`, `default_library_root`, `_dataless` (`SF_DATALESS`) | XDG/`%APPDATA%` aus der Hülle; OneDrive-Placeholder-Flag |
| `backend/…/bibliothek.py` `_slug` | Unicode-Slug, bis 60 Zeichen | reservierte Gerätenamen (CON, NUL, COM1–9 …) mit Suffix versehen |
| `enrich_core/zotero.py` (Upstream) | `~/Library/Application Support/Zotero/Profiles`, `/Volumes` | `%APPDATA%\Zotero\Zotero\Profiles`, `~/.zotero/zotero`; Volume-Scan je OS |
| `Info.plist` | UTIs `.enrich` (Package + Zip) | `bundle.fileAssociations`; Package-Dossier als Ordnerdialog |

4. **Nicht versperren durch Unterlassen:** Tauri auf `2.x` pinnen (3.0-alpha ist da), PyO3 ≥ 0.28.3, whisper.cpp-Tag pinnen; `uv run pytest` bleibt whisper-/ffmpeg-frei über Fakes — der billigste Portabilitätstest, sobald jemand einen fremden Runner anwirft.

## 8. Tests und Migration

**Teststrategie.** pytest bleibt Kern: `main.py` lebt als dünne HTTP-Hülle weiter (49 Tests + `eintrag`-Fixture), neue Tests gegen `api.py` ohne Transport; Fakes implementieren das Motor-Protokoll. Rust: Integrationstest `python::init` + `api.health` (das ist der Spike), Range-Parser und eid-Map als reine Funktionen, whisper mit `tiny` als `#[ignore]` im Release-Check. Vertragstests: Golden-JSON ↔ `tauri::test::mock_builder`/`get_ipc_response`; Drift-Wächter Routen ↔ Fassade ↔ `api.ts` (Muster `test_drift_guard.py`). Frontend: `tsc`; optional vitest + `@tauri-apps/api/mocks` für den Transport-Schalter (neue Abhängigkeit). E2E: Playwright gegen Browser + uvicorn bleibt (Screenshot-Pipeline; macOS hat keinen WKWebView-Treiber); die echte App prüft der manuelle Release-Check plus Dauerlauf (4 Jobs, Abbruch, Polling, 20 min, Speicher). Parität beim Motorwechsel am 3,4-h-Workshop und der 5-min-Feldaufnahme.

**Unverändert für Nutzer:** `transkript.json` Schema 2 (Segment-IDs, `sp1…`, `journal`/`run-<ULID>`, `who.app`), Ordnerlayout `<Bibliothek>/<slug>/` mit `audio.<ext>`, `video.<ext>`, `history/` (30), `_papierkorb/`, `<Bibliothek>/Modelle`; `config.json` mit `DEFAULTS` und `install_id` (Ort im Store-Build: Container); Format 2 (`TOOL`, `EIGENE_TOOLS`, enrich-core v0.1.0); QDPX (vier `localtranscript:refi-*`-Namensräume, User-GUID «LocalTranscript», `SPRECHER_FARBEN`, kein BOM); Timecodes hh:mm:ss; `LT_CONFIG_DIR`, `LT_MODELS_DIR`, `LT_SPEAKERKIT_DIR`, `LT_APP_ROOT`, `LT_BUNDLED`; `test_kompatibilitaet.py` wacht. `LT_SERVE_PORT`, Port 5628 und der localStorage-Override gelten nur noch für den Dev-Server (CLAUDE.md-Regel anpassen, User-Entscheid).

**Drift-Stellen:** Fehlerform (sechs Statuscodes → `{status, detail}`), Pydantic-Validierung in der Fassade statt in FastAPI, Export-Endungsprüfung bleibt (Save-Dialog liefert beliebige Pfade), Range/206 für Video, `PYO3_CONFIG_FILE` aus der gebündelten Laufzeit (nicht aus dem uv-Venv), `.pth`-Wächter, Bookmark-Scope beim Wechsel des Bibliotheksordners nachziehen, `sys.executable` tabu.

**Versionsplanung:** 0.4.1/0.4.2 = Phase 1.1–1.6 (unsichtbar, CHANGELOG «Internal»); **0.5.0** = eingebettetes Python, `rtmedia`, Ereignisse, LGPL-ffmpeg als Kind (sichtbar: sofortiger Start, kein Port, keine Merkdatei); **0.6.0** = Motoren im Prozess, ffmpeg raus, Lizenztabelle und Eingabeformate neu; **0.7.0** = Store-Build parallel zum DMG. Backlog: Nr. 4 (Anleitung .qdpx.zip) in 0.4.x; **Nr. 6 (iCloud-Dataless-Warnung) vorziehen** — ein hängendes `open()` blockiert jetzt die App, nicht ein neu startbares Kind; Nr. 3 (Package-Import) nach Phase 1 prüfen; Nr. 5 zurückgestellt; Plan-Variablen `LT_TOKEN`/`/api/shutdown` entfallen, `LT_SANDBOX` bleibt.

## 9. Risiken und offene Fragen

| # | Risiko | W | Wirkung | Klärung / Gegenmassnahme |
|---|---|---|---|---|
| 1 | Review «Tauri + eingebettetes CPython» unbelegt | mittel | hoch | TestFlight nach Phase 1; Notes erklären Interpreter, kein pip, kein Nachladen; Compliance-Patch |
| 2 | Absturz in whisper.cpp/Core ML/AVFoundation reisst die App mit | mittel | hoch | Autosave-Flush vor Motorlauf, `transkript.json` als Wahrheit; Option Helfer-XPC-Prozess im Bundle bleibt offen |
| 3 | GIL-Disziplin: synchroner Befehl auf dem Hauptthread, Motor ohne `detach`, `OnceLock`-Deadlock | mittel | hoch | Regeln in `python.rs`-Kopf, Dauerlauf F1, Code-Review-Checkliste |
| 4 | Medien-Seeking über eigenes Schema (erste Anfrage ohne Range, 4K-HEVC) | mittel | mittel | F2; Rückfall `asset://`; Hybrid nur DMG |
| 5 | SpeakerKit-Shim (swift-rs, Async-Brücke, Signatur) | mittel | mittel | F3 mit Tagesfrist; Kindprozess als belegter Weg |
| 6 | Parität whisper-cli ↔ whisper-rs (flash_attn, VAD, Clip-Grenzen, Versionssprung 1.8.2→1.8.3) | hoch | mittel | Paritätsskript, `LT_MOTOR=kind` als Standard bis grün, Fork mit gepinntem Submodul |
| 7 | MP3-Kodierung: Apple kodiert nicht, LAME dynamisch nötig | hoch | niedrig | M4; `libmp3lame.dylib` in Frameworks + Tarball |
| 8 | Eingabeformate nach ffmpeg-Wegfall (Opus/ogg, webm) | mittel | mittel | Format-Matrix mit Fixtures; Liste bewusst festlegen (E4), CHANGELOG |
| 9 | Speicher/GPU: Modell + Samples + Core ML + WebView in einem Prozess, `max_parallel` 4 | mittel | mittel | Messung im Dauerlauf; Serialisierung der GPU-Läufe; i16-Puffer |
| 10 | `--validate-app`: ein `.so` in `Resources`, Entitlement-Blobs, Designated Requirement | niedrig | mittel | Probe-Upload; `--requirements` von Hand |
| 11 | Zwei Transporte driften (fetch vs. invoke) | hoch | mittel | Goldens, Drift-Wächter, `tauri dev`-Pflichtprüfung |
| 12 | Bestandsnutzer: Container-Bibliothek unsichtbar, zwei Builds gleiche Bundle-ID | mittel | mittel | Bookmark-Standard, «Bibliothek wählen»; ggf. eigene Bundle-ID für Dev |

**Offene Fragen (User-Entscheide):** E5 Framework oder Kind; Bibliotheks-Standard Container oder Dialog + Bookmark; Direktvertrieb ebenfalls sandboxed (ein Datei-Fluss-Modell)?; Port-5628-Regel in CLAUDE.md; Eingabeformat-Liste; Dispatcher `api(name,args)` jetzt, typisierte Befehle beim Motor-Umbau (Vorschlag: so); `main.py` dauerhaft als Test-/Browser-Hülle (Vorschlag: ja, 0,5 PT, spart Testumbau); Hybrid-Zwischenrelease 0.5.0-beta mit Medien per HTTP (Vorschlag: nein, F2 abwarten).

## 10. Reihenfolge und Zeitplan (nur Mac)

| Woche | Schritte | Ergebnis | Entscheidungspunkt |
|---|---|---|---|
| 1 | Phase 0 (F1–F3, M4); Zertifikate/Profil beantragen; Privacy-Seite + Support-E-Mail; LGPL-ffmpeg als Kind beziehen | Spike-Befund in `docs/`; Portal bereit | **E0 Go/No-Go** (F1); Medienweg (F2); **E5** SpeakerKit |
| 2 | 1.1–1.6 (Vertrag, `api.py`, Motor-Protokoll mit Kind-Umsetzung, `jobs`-Beobachter, `config`) | 0.4.1/0.4.2, alle Tests grün, nichts sichtbar | – |
| 3 | 1.7–1.15 (PyO3-Brücke, `lib.rs` entschlackt, `rtmedia`, `api.ts`, Bundle ohne venv, Signatur ohne `cs.*`) | 0.5.0-Kandidat als DMG, Dauerlauf | **E2 Release 0.5.0**; erster TestFlight-Build (Sandbox-Spike-Entitlements, Kinder mit `inherit`) |
| 4 | Whisper im Prozess (Paritätstest), Ton über AVFoundation + LAME | Motoren hinter `LT_MOTOR`, Standard noch `kind` | **E3 Standardmotor umschalten**; **E4 Eingabeformate** |
| 5 | SpeakerKit nach E5; ffmpeg aus dem Bundle; Lizenztabelle, `LICENSE-EXCEPTION`, `resources/licenses/`, i18n-Texte; Rechtsprüfung anstossen | 0.6.0 als DMG | Rechtsfreigabe |
| 6 | Bookmarks, Zotero-Ordnerwahl, `entitlements.mas.plist`, `release-mas.mjs`, Screenshots, Metadaten, Review-Notes | Einreichfähiger Build, TestFlight | ITMS-/Beta-Review-Rückmeldung |
| 7–8 | Review-Einreichung; Nacharbeiten; 0.7.0 parallel als DMG mit Quell-Tarballs | Store-Freigabe oder begründete Ablehnung | Parallelvertrieb dauerhaft? |

## 11. Quellen

- PyO3: https://pyo3.rs/latest/building-and-distribution.html · https://pyo3.rs/latest/parallelism.html · https://pyo3.rs/latest/faq.html · https://pyo3.rs/latest/migration.html · https://docs.rs/pyo3/latest/pyo3/marker/struct.Python.html · https://docs.rs/pyo3-build-config/latest/pyo3_build_config/fn.add_libpython_rpath_link_args.html · https://github.com/PyO3/pyo3/pull/5624
- Python C-API: https://docs.python.org/3.13/c-api/init_config.html · https://docs.python.org/3.13/c-api/init.html · https://docs.python.org/3/c-api/interp-lifecycle.html · https://docs.python.org/3.13/library/threading.html · https://docs.python.org/3/using/mac.html (§5.5.4) · https://raw.githubusercontent.com/python/cpython/3.13/Mac/Resources/app-store-compliance.patch
- python-build-standalone: https://raw.githubusercontent.com/astral-sh/python-build-standalone/main/docs/running.rst · …/quirks.rst · …/distributions.rst
- PyTauri / tauri-plugin-python: https://pytauri.github.io/pytauri/latest/usage/tutorial/build-standalone/ · https://github.com/pytauri/pytauri/issues/99 · https://github.com/marcomq/tauri-plugin-python
- Tauri: https://v2.tauri.app/develop/calling-rust/ · https://v2.tauri.app/develop/calling-frontend/ · https://v2.tauri.app/security/capabilities/ · https://v2.tauri.app/develop/debug/ · https://v2.tauri.app/develop/tests/mocking/ · https://v2.tauri.app/develop/tests/webdriver/ · https://v2.tauri.app/distribute/app-store/ · https://v2.tauri.app/reference/javascript/dialog/ · https://docs.rs/tauri/latest/tauri/struct.Builder.html · https://docs.rs/tauri/latest/tauri/test/index.html · https://docs.rs/tauri/latest/tauri/async_runtime/fn.spawn_blocking.html · https://docs.rs/tauri/latest/tauri/path/struct.PathResolver.html · https://github.com/tauri-apps/tauri/blob/dev/examples/streaming/main.rs · https://github.com/tauri-apps/tauri/blob/tauri-v2.11.5/crates/tauri/src/protocol/asset.rs · https://github.com/tauri-apps/tauri/pull/15838 · Issues 4133 · 7355 · 9177 · 15144 · 15230 · https://raw.githubusercontent.com/tauri-apps/tauri/tauri-cli-v2.11.4/crates/tauri-bundler/src/bundle/macos/app.rs · …/sign.rs · https://v2.tauri.app/plugin/opener/
- wry / WebKit: https://github.com/tauri-apps/wry/blob/dev/src/wkwebview/class/url_scheme_handler.rs · https://bugs.webkit.org/show_bug.cgi?id=203302 · https://wadetregaskis.com/mac-app-sandboxing-interferes-with-drag-drop/
- whisper.cpp / whisper-rs: https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/include/whisper.h · https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/src/whisper.cpp · https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/README.md · https://codeberg.org/tazz4843/whisper-rs · https://docs.rs/whisper-rs/latest/whisper_rs/struct.WhisperState.html · …/struct.WhisperSegment.html · …/struct.FullParams.html · …/struct.WhisperVadParams.html · …/struct.WhisperContextParameters.html · https://huggingface.co/ggerganov/whisper.cpp/tree/main
- SpeakerKit: https://github.com/argmaxinc/argmax-oss-swift · https://raw.githubusercontent.com/argmaxinc/argmax-oss-swift/main/Sources/SpeakerKit/Pyannote/PyannoteDiarizer.swift · …/PyannoteConfig.swift · https://huggingface.co/argmaxinc/speakerkit-coreml · https://huggingface.co/pyannote/segmentation-3.0 · https://huggingface.co/pyannote/speaker-diarization-community-1 · https://www.pyannote.ai/blog/community-1 · https://www.argmaxinc.com/blog/speakerkit · https://www.isca-archive.org/interspeech_2025/durmus25_interspeech.pdf · https://crates.io/api/v1/crates/swift-rs · https://raw.githubusercontent.com/Brendonovich/swift-rs/master/README.md · https://crates.io/api/v1/crates/fluidaudio-rs
- Ton: https://developer.apple.com/library/archive/documentation/MusicAudio/Conceptual/CoreAudioOverview/SupportedAudioFormatsMacOSX/SupportedAudioFormatsMacOSX.html · https://crates.io/api/v1/crates/objc2-av-foundation · https://crates.io/api/v1/crates/mp3lame-encoder · https://crates.io/api/v1/crates/mp3lame-sys · https://www.gnu.org/licenses/gpl-faq.en.html#LGPLStaticVsDynamic · https://raw.githubusercontent.com/Nothing-Software/FFmpeg-Builds/main/README.md
- Apple Sandbox / Signatur / Store: https://developer.apple.com/documentation/foundation/nsurl/startaccessingsecurityscopedresource() · https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox · https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox · https://developer.apple.com/library/archive/documentation/Miscellaneous/Reference/EntitlementKeyReference/Chapters/EnablingAppSandbox.html · …/AppSandboxTemporaryExceptionEntitlements.html · https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.network.server · …/com.apple.security.cs.disable-library-validation · …/com.apple.security.cs.allow-jit · …/com.apple.security.cs.allow-unsigned-executable-memory · …/com.apple.security.cs.allow-dyld-environment-variables · https://developer.apple.com/documentation/security/hardened-runtime · https://developer.apple.com/documentation/bundleresources/placing-content-in-a-bundle · https://developer.apple.com/documentation/xcode/embedding-a-helper-tool-in-a-sandboxed-app · https://developer.apple.com/documentation/technotes/tn3125-inside-code-signing-provisioning-profiles · https://developer.apple.com/documentation/technotes/tn3147-migrating-to-the-latest-notarization-tool · https://developer.apple.com/app-store/review/guidelines/ · https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications/ · https://developer.apple.com/app-store/app-privacy-details/ · https://developer.apple.com/app-store/whats-new/
- Präzedenz: https://geolibre.app/mac-app-store/ · https://apps.apple.com/us/app/whisper-transcription/id1668083311 · https://raw.githubusercontent.com/beeware/briefcase/main/src/briefcase/platforms/macOS/__init__.py
- Lizenzen: https://www.fsf.org/news/2010-05-app-store-compliance · https://www.videolan.org/press/lgpl-libvlc.html · https://www.apple.com/legal/macapps/minterms/ · https://raw.githubusercontent.com/narrowstacks/dorkroom/main/LICENSE-EXCEPTION · https://raw.githubusercontent.com/nextcloud/ios/master/COPYING.iOS · https://ffmpeg.org/legal.html · https://raw.githubusercontent.com/argmaxinc/argmax-oss-swift/main/NOTICES
- Zotero: https://www.zotero.org/support/kb/profile_directory · https://www.zotero.org/support/dev/web_api/v3/local_api
