# Phase 0 — Befund des Versuchs-Branchs `eingebettet-spike`

Stand 17.9.2026. Gehört zu `docs/appstore-plan.md` §3 (Fragen F1–F3,
Nebenmessung M4). Rechner: Apple M3 Pro, macOS 26.5, Xcode 26.5,
Rust 1.93, PyO3 0.29, Tauri 2, python-build-standalone CPython 3.13.

Alles auf diesem Branch, nichts auf `main`. Bundle
`ResearchTranscriptSpike.app` (Identifier `city.bias.researchtranscript.spike`,
eigener Container), signiert mit Developer ID, Hardened Runtime und
App-Sandbox — also die Bedingungen des Stores, nur ohne Store-Zertifikat.

## Kurzfassung

| Frage | Ergebnis | Entscheid |
|---|---|---|
| **F1** Eingebettetes Python im signierten Sandbox-Bundle | **Ja.** Start 6,4 ms, Import `researchtranscript` + pydantic 125 ms, vier Python-Threads mit Rust-Callback, Abbruch < 0,5 s, Poll 0,0 ms, keine Sandbox-Verstösse | **E0: Go** für Variante A |
| **F2** Medien ohne HTTP-Server | **Ja, beide Wege.** 60-MB-mp3 und 730-MB-mp4 aus dem Container, Sprünge 66–281 ms, kein Stocken; `asset://` (Tauri) ebenbürtig bis leicht schneller als eigenes Schema | **`asset://` mit `convertFileSrc`**, kein eigenes Schema |
| **F3** SpeakerKit im Prozess | **Ja.** Swift-Shim via swift-rs, RTTM byte-identisch zur CLI, Sandbox ohne Extra-Entitlement; Kindprozess mit `inherit` läuft ebenfalls (16 RTTM-Zeilen) | **E5: Shim im Prozess**, Kindprozess bleibt belegter Rückfall |
| **M4** AVFoundation statt ffmpeg | **Ja, mit Einschränkungen.** Dekodieren nativ → eigener Downmix → `AVAudioConverter`; MP3-Schreiben nur über `libmp3lame` (LGPL, dynamisch); WebM fällt weg | AVFoundation + libmp3lame, ffmpeg raus |

Kein Abbruchkriterium aus §3 ist eingetreten.

## Zwei Befunde, die den Plan ändern

1. **`com.apple.security.network.client` ist Pflicht.** Ohne dieses
   Entitlement lädt WKWebView in der Sandbox *gar keine* Seite — auch
   `tauri://localhost/index.html` nicht; `on_page_load` feuert nie, das
   Fenster bleibt leer, ohne Fehler im Unified Log. Mit dem Entitlement
   lädt alles. Der Plan (§3 F1, §6) sah «**ohne** `network.*`» vor — das
   ist zu streichen. Für Zotero (localhost:23119) und Ollama bräuchten wir
   es ohnehin.
2. **Der Engine muss `LT_APP_ROOT` und `LT_BUNDLED=1` setzen.**
   `config.get_app_root()` leitet die Wurzel aus `__file__` ab
   (Repo-Layout `backend/src/…`); im Bundle liegt das Paket unter
   `venv/lib/python3.13/site-packages/`, die Wurzel würde `venv/lib`, und
   `bin/`, `models/`, `BUNDLED` sind unauffindbar. Die alte Hülle setzte
   die Variablen beim Kindstart; jetzt tut es `python::sicherstellen()`
   vor `Py_InitializeFromConfig`. Gehört in Phase 1 (1.2, `python.rs`).

## F1 im Einzelnen

Bau: `pyo3 0.29` mit `PYO3_CONFIG_FILE` auf die gebündelte Laufzeit,
`build.rs` mit rpath `@executable_path/../Frameworks`, `libpython3.13.dylib`
über `bundle.macOS.frameworks`, isolierte `PyConfig` (home = `python-runtime`,
`sys.path` = stdlib + lib-dynload + venv-site-packages, kein `site`),
`PyEval_SaveThread` nach dem Start. Selbstlauf aus Rust (`selbstlauf()`),
damit die Messung nicht vom WebView abhängt.

| Messung | Ergebnis |
|---|---|
| 1 `health` | `sandboxed: true`, `HOME` = Container, `isolated: 1`, Init 6,4 ms |
| 2 Import `researchtranscript.jobs`, `pydantic_core` | 125 ms, Module aus dem Bundle-venv |
| 3 Vier Fake-Jobs (`jobs.starte`, Python-Threads, `_konvertiere` durch Schlaf-Fake ersetzt) | alle vier laufen parallel, Fortschritt steigt gleichmässig, Rust-Callback 395 Aufrufe in 20 s, Poll 0,0 ms je Aufruf, `abbruch` → `cancelled` nach < 500 ms bei 28 %, die anderen drei bis 99 % und in den gewollten Fehler |
| 4 Ordner per Open-Panel, Python listet/schreibt/löscht darin | **offen** — braucht einen Klick im Spike-Fenster (Knopf «4 · Ordner wählen») |
| 5 Kind `argmax-cli` mit `app-sandbox` + `inherit` | exit 0, 16 RTTM-Zeilen auf der 5-min-Feldaufnahme, 5,7 s |
| Sandbox-Verstösse (`log show`, sender Sandbox) | keine |
| `codesign --verify --deep --strict` | ok (Hülle, `libpython3.13.dylib`, `argmax-cli` mit eigenen Entitlements) |

Erster Lauf von Messung 3 scheiterte mit «ffmpeg nicht gefunden» — Befund 2
oben; kein Problem des Einbettens.

## F2 im Einzelnen

Eigenes Schema `rtmedia://localhost/<key>` (`medien.rs`,
`register_asynchronous_uri_scheme_protocol`, 206 mit `Accept-Ranges`,
4-MB-Deckel) gegen Tauris `asset://` (`convertFileSrc`, Scope `**`).
Messung: `preload="auto"`, stumm abspielen, fünf Sprünge (83/12/55/97/31 %
der Dauer), Zeit bis `seeked`, Zähler `waiting`/`stalled`.

| Datei | Weg | Metadaten | Sprünge (ms) | waiting / stalled |
|---|---|---|---|---|
| audio.mp3, 60 MB, 42 min | rtmedia | 30 ms | 66 · 281 · 176 · 90 · 172 | 1 / 0 |
| audio.mp3 | asset | 70 ms | 122 · 79 · 68 · 87 · 77 | 1 / 0 |
| Teams-mp4, 730 MB, 89 min | rtmedia | 91 ms | 171 · 156 · 153 · 105 · 134 | 1 / 0 |
| Teams-mp4 | asset | 50 ms | 125 · 70 · 87 · 154 · 80 | 1 / 0 |

Das eine `waiting` ist jeweils der Start vor dem ersten Puffer. WebKit
fragt von Anfang an mit Range (`bytes=0-1`, `0-7`, `0-65535`, dann
gezielt); 907 Anfragen, je 0,0–0,3 ms im Handler. **Entscheid:** `asset://`
— null eigener Code, Scope statt Map; Plan-Zeile 1.10 wird zu «CSP
`media-src asset: http://asset.localhost`, Scope auf Bibliothek +
Bookmark-Pfade». Das 4K-HEVC-Video aus §3 wurde nicht gemessen (kein
Fixture); Risiko 4 sinkt trotzdem, weil der Weg bei 730 MB trägt.

CSP-Lehre nebenbei: die produktive CSP (`media-src 'self' blob:
http://127.0.0.1:*`) blockt beide Wege stumm — Phase 1 muss `media-src`
und `img-src` anpassen.

## F3 — siehe `spike/speakerkit-shim/BEFUND.md`

Shim `rt_diarize` (C-ABI, JSON zurück), statisch über swift-rs gelinkt,
keine Swift-Laufzeit zum Mitliefern, byte-identische RTTM zur CLI,
kalt 0,58 s / warm 0,41 s je 2-min-Datei, Sandbox ohne Extra-Entitlement.
Der Aufruf blockiert den rufenden Thread → nur aus `spawn_blocking`.
Fortschritt springt upstream sofort auf 85 — für die UI eigene Zeitskala
oder Patch. **E5: Variante (a)**, Kindprozess (b) belegt und bleibt Rückfall.

## M4 — siehe `spike/avfoundation/BEFUND.md`

- Dekodieren: nativ lesen, selbst (L+R)/n mischen, `AVAudioConverter`
  (Qualität max) auf 16 kHz — 35 dB SNR gegen ffmpeg breitbandig,
  70–87 dB unter 3,4 kHz, kein Versatz (mp3: konstant 13 ms LAME-Delay,
  den Apple nicht trimmt). **Nicht** `AVAssetReaderAudioMixOutput` mit
  `AVSampleRateKey` (19 dB, Stereo +3 dB). 1 h mp3: 3,1 s (ffmpeg 1,8 s).
- Formate: mp3, m4a/AAC, mp4/mov (avc1/hvc1/hev1), FLAC, Ogg/Vorbis,
  Ogg/Opus gehen; **WebM/Matroska nicht** → aus `AUDIO_ENDUNGEN`/MIME
  streichen, CHANGELOG-Eintrag.
- Sondieren: Codec-Tag, Masse, Dauer, Bitrate wie ffprobe, plus `isPlayable`.
- MP3 schreiben: Apple kann es nicht (drei APIs geprüft). `libmp3lame`
  (LGPL 2.0+, 216 KB, dynamisch in `Contents/Frameworks`, ohne Decoder
  gebaut) per dlopen: VBR q2 auf 0,1 % gleich wie `ffmpeg -q:a 2`, 1 h in
  10,1 s. Xing-Tag nach `lame_encode_flush` zurückschreiben.

## Folgen für den Plan (Änderungsliste)

- §3/§6 Entitlements: `network.client` **hinzufügen**.
- §4 1.2 `python.rs`: `LT_APP_ROOT`/`LT_BUNDLED` setzen, bevor der
  Interpreter startet (oder `get_app_root()` auf `sys.prefix` umstellen).
- §4 1.10: `rtmedia` streichen, `asset://` mit Scope; CSP `media-src`,
  `img-src` anpassen; `medien.rs` entfällt.
- §5 E5: Shim im Prozess; `spawn_blocking`; Fortschritt selbst skalieren.
- §5 Ton: AVFoundation nativ + `AVAudioConverter`; `libmp3lame` als
  dynamische Bibliothek mit LGPL-Hinweis; WebM raus.
- §9 Risiko 3 (GIL) unverändert offen — der 20-min-Dauerlauf aus §3
  wurde nicht gefahren (nur 26 s).

## Was im Branch liegt

`frontend/src-tauri/src/python.rs` (Interpreter, Spike-Befehle,
Selbstlauf), `src/medien.rs` (rtmedia-Handler, wird nicht übernommen),
`src/lib.rs` (Einbindung, `on_page_load`-Protokoll), `Cargo.toml`/`build.rs`/
`pyo3-config.txt`, `tauri.conf.json` (Spike-Identifier, `spike-ui`,
gelockerte CSP, Framework-Eintrag), `entitlements.spike.plist`,
`entitlements.child.plist`, `frontend/spike-ui/` (F1-/F2-Seiten),
`spike/speakerkit-shim/`, `spike/avfoundation/`. Bauen:
`PYO3_CONFIG_FILE=$PWD/src-tauri/pyo3-config.txt npx tauri build --bundles app`,
danach `argmax-cli` mit `entitlements.child.plist` und die Hülle mit
`entitlements.spike.plist` neu signieren. Protokoll: stdout und
`~/Library/Containers/city.bias.researchtranscript.spike/Data/spike.log`.
