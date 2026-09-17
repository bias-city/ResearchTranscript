# Befund F3 — SpeakerKit im Prozess (Rust ↔ Swift) statt Kindprozess

Spike zu docs/appstore-plan.md §3, Frage F3. Stand 2026-09-17, Arbeitszeit
rund 70 Minuten. Rechner: Apple M3 Pro, 36 GB, macOS 26.5 (25F71),
Xcode 26.5 (17F42), Swift 6.3.2, Rust 1.93.0, swift-rs 1.0.8.

## Kurzfassung

**Der Shim funktioniert.** SpeakerKit (argmax-oss-swift @ ea872ff) lässt
sich als statische Swift-Bibliothek mit einer C-Schnittstelle
(`rt_diarize`) aus Rust im selben Prozess aufrufen — Linken über swift-rs
in `build.rs`, ein einziger zusätzlicher Linkerflag (rpath). Die Ausgabe
ist **byte-identisch** mit `argmax-cli` (gleiche RTTM, 16 Segmente, 2
Sprecher, 100 % Übereinstimmung), deterministisch über alle Läufe, auch
unter der App-Sandbox ohne zusätzliches Entitlement. Laufzeit kalt gleich
wie die CLI (~0,58 s je 2-min-Datei), warm (Modelle im Prozess) 0,41 s.
Der Fortschritts-Callback meldet monoton, aber wegen einer Upstream-
Eigenheit springt er sofort auf 85.

**Empfehlung E5: Shim im Prozess** (Variante a). Siehe unten.

## Was gebaut wurde

```
spike/speakerkit-shim/
├── SpeakerKitShim/              SwiftPM-Paket, statische Bibliothek
│   ├── Package.swift            hängt an ../argmax-oss-swift (lokaler Klon @ ea872ff)
│   └── Sources/SpeakerKitShim/Shim.swift   rt_diarize / rt_unload / rt_free
├── rt-diarize-spike/            Cargo-Projekt (Binary)
│   ├── build.rs                 swift-rs SwiftLinker + rpath
│   └── src/main.rs              WAV lesen (hound) → rt_diarize → RTTM
├── vergleich.py                 RTTM-Parität (beste Label-Permutation, 10-ms-Raster)
├── argmax-oss-swift/            Klon, Commit ea872ff (gitignored)
└── BEFUND.md
```

### C-Schnittstelle (Shim.swift)

```c
// JSON-C-String; Aufrufer gibt mit rt_free frei.
// Erfolg: {"segments":[{"start":0.0,"end":6.927,"speaker":"B"},…],
//          "speaker_count":2,"model_load_ms":70.1,"diarize_ms":433.2}
// Fehler: {"error":"…"}
char *rt_diarize(const float *samples, size_t n,      // 16 kHz mono f32
                 int32_t num_speakers,                 // 0 = automatisch
                 float cluster_distance_threshold,     // wie --cluster-distance-threshold
                 bool exclusive,                       // wie --use-exclusive-reconciliation
                 const char *model_dir,                // wie --model-path
                 void (*progress)(int32_t));           // 0–100, darf NULL sein
void  rt_unload(const char *model_dir);                // Modelle aus dem Speicher werfen
void  rt_free(char *p);
```

- Die async-API (`SpeakerKit.diarize`) wird über `Task.detached` +
  `DispatchSemaphore` synchron gemacht. Der Aufruf **blockiert den
  rufenden Thread** — in Tauri also nie aus dem Main-Thread, sondern aus
  `spawn_blocking`/eigenem Thread rufen (Hauptthread-Aufruf funktioniert
  im Spike, weil SpeakerKit keinen MainActor braucht; in einer GUI-App
  würde er aber die UI einfrieren).
- Die geladene `SpeakerKit`-Instanz bleibt je Modellordner im Prozess
  (`Cache`); der zweite Aufruf spart das Modell-Laden (70–90 ms) und den
  Prozessstart.
- Sprecherlabel wie die CLI: `A` + id % 26; Segmente wie
  `SpeakerKit.generateRTTM` ohne Transkript (`updateSegments(minActiveOffset: 0)`).
- Konfiguration wie `DiarizeCLI.setupSpeakerKit`: `PyannoteConfig(modelFolder:,
  download: false, verbose: false, fullRedundancy: true)`.

## Exakte Build-Schritte

```sh
cd spike/speakerkit-shim
git clone https://github.com/argmaxinc/argmax-oss-swift && (cd argmax-oss-swift && git checkout ea872ff)
# Swift allein (optional, cargo tut es selbst):
(cd SpeakerKitShim && swift build -c release)      # → .build/release/libSpeakerKitShim.a
# Rust (baut den Swift-Teil über build.rs mit):
(cd rt-diarize-spike && cargo build --release)     # → target/release/rt-diarize-spike
```

Erstbau Swift ≈ 35 s (ganzes argmax-oss-swift: ArgmaxCore, WhisperKit,
TTSKit, SpeakerKit werden mitkompiliert, weil SpeakerKit von WhisperKit
abhängt), Rust ≈ 47 s inkl. Swift-Neubau im OUT_DIR. Inkrementell ~1–4 s.
`.build`-Ordner je 282 MB (SwiftPM) bzw. 350 MB (cargo target).

`Package.swift` referenziert den Klon per `.package(path: "../argmax-oss-swift")`;
produktiv `.package(url: …, revision: "ea872ff")` — dann klont SwiftPM
selbst (Netz beim ersten Build, wie heute `hole-argmax.mjs`).

### build.rs (vollständig)

```rust
use swift_rs::SwiftLinker;
fn main() {
    SwiftLinker::new("13.0")
        .with_package("SpeakerKitShim", "../SpeakerKitShim")
        .link();
    // libswift_Concurrency wird sonst aus der Xcode-Toolchain mit
    // @rpath-Install-Name gelinkt → dyld «no LC_RPATH's found».
    println!("cargo:rustc-link-arg=-Wl,-rpath,/usr/lib/swift");
}
```

Cargo.toml: `[build-dependencies] swift-rs = { version = "1.0.8", features = ["build"] }`.
Zur Laufzeit wird swift-rs nicht gebraucht (reines `extern "C"`).

### Was swift-rs tatsächlich tut (aus dem Build-Script-Output)

```
swift build --sdk <MacOSX26.5.sdk> -c release --arch arm64
      --build-path <OUT_DIR>/swift-rs/SpeakerKitShim
      -Xswiftc -sdk <sdk> -Xswiftc -target arm64-apple-macosx13.0
      -Xcc --target=arm64-apple-macosx13.0 -Xcxx --target=arm64-apple-macosx13.0
cargo:rustc-link-search=native=/Applications/Xcode.app/…/XcodeDefault.xctoolchain/usr/lib/swift/macosx
cargo:rustc-link-search=native=/usr/lib/swift
cargo:rustc-link-lib=clang_rt.osx
cargo:rustc-link-search=/Applications/Xcode.app/…/usr/lib/clang/21/lib/darwin
cargo:rustc-link-search=native=<OUT_DIR>/swift-rs/SpeakerKitShim/arm64-apple-macosx/release
cargo:rustc-link-lib=static=SpeakerKitShim
cargo:rustc-link-arg=-Wl,-rpath,/usr/lib/swift        (unser Zusatz)
```

Keine `-framework`-Flags nötig: Swift-Objekte tragen die Frameworks als
LC_LINKER_OPTION (Autolink), ld zieht CoreML, Accelerate, AVFoundation
usw. selbst. Deployment-Target macOS 13.0 (SpeakerKit-Minimum).

## Grössen und Abhängigkeiten

| Artefakt | Grösse |
|---|---|
| `libSpeakerKitShim.a` (80 Objekte: ArgmaxCore + WhisperKit + TTSKit + SpeakerKit + Shim) | 13,5 MB |
| `rt-diarize-spike` (fertige Binary, dead-stripped) | 3,6 MB |
| `bin/argmax-cli` zum Vergleich | 6,6 MB |

`otool -L` der Binary: **nur Systempfade** — `/usr/lib/swift/libswift*.dylib`
(Core, Foundation, _Concurrency, Dispatch, CoreML, Accelerate,
AVFoundation, CoreAudio, CoreFoundation, ObjectiveC, os, simd, Network,
_StringProcessing, NaturalLanguage, CryptoKit …) und die Frameworks
AVFoundation, Accelerate, AudioToolbox, CFNetwork, CoreAudio,
CoreFoundation, CoreGraphics, CoreML, CoreVideo, CryptoKit, Foundation,
NaturalLanguage, libobjc, libSystem. **Keine Swift-Runtime muss ins
Bundle** (ABI-stabil seit macOS 10.14.4); die Liste ist dieselbe wie bei
`argmax-cli`. `libswift_Concurrency` ist nach dem rpath-Fix
`@rpath/libswift_Concurrency.dylib` mit `LC_RPATH /usr/lib/swift` — wird
also aus dem System geladen.

## Laufzeitvergleich

Testdatei: `docs/demo/housing-cooperatives-interview.mp3` → 16 kHz mono
WAV (ffmpeg, pcm_s16le), 122,95 s, 1 967 226 Samples. (Die im Auftrag
genannte feld5.wav lag nicht mehr im Scratchpad; sie wurde daraus neu
erzeugt.) Flags wie `diarize.py`: `--cluster-distance-threshold 0.62`
(= `_schwelle(0.5)`), `--use-exclusive-reconciliation`, mit und ohne
`--num-speakers 2`. Wandzeit je Prozess, 3 Läufe:

| Variante | Lauf 1 | Lauf 2 | Lauf 3 | Median |
|---|---|---|---|---|
| argmax-cli, automatisch | 584 ms | 636 ms | 572 ms | **584 ms** |
| argmax-cli, `--num-speakers 2` | 536 ms | 556 ms | 550 ms | **550 ms** |
| Shim, eigener Prozess je Lauf (kalt), automatisch | 586 ms | 576 ms | 577 ms | **577 ms** |
| Shim, eigener Prozess je Lauf (kalt), n=2 | 548 ms | 616 ms | 547 ms | **548 ms** |
| Shim, 3 Aufrufe im selben Prozess (warm), automatisch — nur `diarize` | 433 ms | 411 ms | 412 ms | **412 ms** |
| Shim, warm, n=2 | 456 ms | 427 ms | 405 ms | **427 ms** |

Aufschlüsselung Shim (aus dem JSON): Modell-Laden 70–90 ms, Diarisierung
405–456 ms; Rest (~60 ms) Prozessstart + WAV lesen. Die CLI meldet mit
`--verbose` für dieselbe Datei «Total Time 435 ms» — die Kerne sind
identisch, der Prozessstart der CLI kostet ~150 ms.

**Verhältnis Shim/CLI ≈ 1,0 kalt, ≈ 0,7 warm** — Kriterium «≤ 1,5×»
erfüllt. Der Gewinn ist bei 2 min Audio klein (~150 ms); bei 3,4-h-
Workshops ist die Diarisierung selbst (~300× Echtzeit → ~40 s)
dominant, das Sparen des Prozessstarts fällt kaum ins Gewicht.

**Core-ML-Erstlauf:** Der allererste Modell-Ladevorgang pro Benutzer
(bzw. pro Sandbox-Container) dauert 4,5–4,9 s (Core-ML-/ANE-Kompilat wird
gecacht), danach 70–90 ms. Gilt für CLI und Shim gleichermassen (CLI-Kind
unter Sandbox: 7,0 s beim ersten, 540 ms beim zweiten Lauf). Für die App:
nach Installation kostet die erste Diarisierung einmalig ~5 s mehr.

## Parität

`vergleich.py` (10-ms-Raster, beste Label-Permutation):

| Vergleich | Segmente | Sprecher | Übereinstimmung | RTTM identisch |
|---|---|---|---|---|
| CLI auto vs. Shim auto | 16 / 16 | 2 / 2 | 100,00 % (122,87 s Sprache) | ja (3 Dezimalen) |
| CLI n=2 vs. Shim n=2 | 16 / 16 | 2 / 2 | 100,00 % | ja |
| CLI Lauf 1/2/3 untereinander | 16 | 2 | 100,00 % | ja |
| Shim kalt 1/2/3, warm, sandboxed | 16 | 2 | 100,00 % | ja |
| CLI auto vs. CLI n=2 | 16 | 2 | 100,00 % | ja (Aufnahme hat 2 Sprecher) |

`diff` der RTTM-Dateien: nur das fehlende Newline am Dateiende bei der
CLI (`joined(separator: "\n")`). Die WAV-Normalisierung in Rust
(`i16 / 32768`) trifft die von AVAudioFile exakt genug, dass die
Ergebnisse identisch sind.

## Fortschritts-Callback

Monoton: **ja** (alle Läufe). Gemeldete Folge: `[0, 85, 92, 97, 100]`.
Der Sprung 0 → 85 ist **strukturell in ea872ff** (`PyannoteDiarizer.swift`):
`initialize()` startet Segmentierung + Embedding als Hintergrund-Task und
kehrt sofort zurück; `clusterSpeakers()` meldet **vor** dem `await
diarizationTask` bereits 0 % seiner Phase — das ergibt im gemeinsamen
Progress 85. Alle späteren Meldungen der Segmentierphase (≤ 85) verwirft
der Monotonie-Guard (`if value > completedUnitCount`). Folge: die Anzeige
steht während der teuren Phase auf 85 %. Ein Einzeiler-Patch upstream
(`progressCallback?(0)` erst nach `try await diarizationTask?.value`
melden) behöbe es; alternativ in Rust einen zeitbasierten Schätzer
(Audiosekunden / ~300) bis 85 füttern. Die heutige Python-Lösung meldet
ohnehin nur einen Zeit-Zähler 0–9/10.

## Sandbox

Getestete Fassung: Spike-Binary mit eingebetteter Info.plist
(`-sectcreate __TEXT __info_plist`, nötig für die Container-Anlage),
ad-hoc signiert mit **nur** `com.apple.security.app-sandbox`. Container
`~/Library/Containers/city.bias.rtsandboxspike` wurde angelegt; Lesen
ausserhalb: `Operation not permitted` (Sandbox greift).

- **Core ML im Prozess unter Sandbox ohne weiteres Entitlement: läuft.**
  Modelle + WAV im Container: 3 Läufe, RTTM identisch zur CLI, Diarize
  490–510 ms, Modell-Laden 88–90 ms (Erstlauf 4,9 s, Cache). ANE wird
  genutzt (`ANEServices: Selected ANEDriver device` im Log).
- **argmax-cli als Kind** (Parallelfrage aus F3): Kind ad-hoc signiert
  mit `app-sandbox` + `inherit`, aus dem sandboxed Elternprozess gestartet,
  WAV/Modelle/RTTM im Container: **läuft** (Status 0, 16 Segmente). Der
  Ort des Kindes ist entscheidend: **aus `…/Containers/<id>/Data/` heraus
  verweigert die Sandbox den Exec (posix_spawn EPERM)**; aus einem
  Systemordner (getestet /Applications/…, Analogon zu
  `Contents/MacOS`) klappt es. Ein nur ad-hoc signiertes Kind ohne
  `app-sandbox`-Entitlement startete ebenfalls (Sandbox wird auf Kernel-
  Ebene vererbt) — für den Store müssen trotzdem alle Executables im
  Bundle `app-sandbox`+`inherit` tragen.
- Nicht getestet: signierter Tauri-Build mit Hardened Runtime; `tauri
  dev` honoriert Entitlements nicht (Plan §3).

## Stolpersteine (wörtlich)

1. Swift-Compiler, generische Klasse in generischer Funktion:
   `error: type 'Box' cannot be nested in generic function 'runSync'` —
   Box als `private final class ResultBox<T>` auf Dateiebene.
2. Erster Lauf der Binary:
   ```
   dyld[82968]: Library not loaded: @rpath/libswift_Concurrency.dylib
     Referenced from: …/rt-diarize-spike
     Reason: no LC_RPATH's found
   ```
   Ursache: swift-rs setzt `-L …/XcodeDefault.xctoolchain/usr/lib/swift/macosx`
   **vor** `/usr/lib/swift`; dort hat `libswift_Concurrency.dylib` einen
   `@rpath`-Install-Name. Fix: `cargo:rustc-link-arg=-Wl,-rpath,/usr/lib/swift`
   (bekanntes swift-rs-Muster). Alternative: Suchreihenfolge tauschen.
3. Sandbox-Test ohne Info.plist in der Binary: Absturz `EXC_BREAKPOINT`
   in `_libsecinit_appsandbox`, Crash-Report: «Unable to get bundle
   identifier for container id … because Info.plist from code signature
   information has no value for kCFBundleIdentifierKey.» — betrifft nur
   nackte CLI-Binaries, nicht eine App im Bundle.
4. Kind-Exec aus dem Container-Data-Ordner: `posix_spawn` → `Operation
   not permitted`. Hilfsprogramme gehören ins Bundle, nicht in den Container.
5. swift-rs 1.0.8 enthält Sonderpfade für Xcode 27 (andere Produkt-Ordner,
   `@_cdecl`-Symbole werden internalisiert und per `llvm-objcopy` wieder
   global gemacht — braucht `rustup component add llvm-tools`). Unter
   Xcode 26.5 nicht aktiv; beim Xcode-Wechsel im Blick behalten.
6. `swift build` kompiliert das ganze argmax-oss-swift mit (WhisperKit-
   Abhängigkeit von SpeakerKit); die .a enthält deshalb auch WhisperKit-
   und TTSKit-Objekte — ld strippt sie, die Binary bleibt 3,6 MB.
7. zsh hat ein eingebautes `log`; für Sandbox-Logs `/usr/bin/log` rufen.

## Nicht gemacht / offen

- **Abbruch**: Der Shim kennt kein `rt_cancel`. SpeakerKit trägt die
  Diarisierung als `Task` (`diarizationTask`, prüft `Task.isCancelled`),
  ein Abbruch ist also über einen gehaltenen Task-Handle machbar (Task im
  Shim behalten, `rt_cancel` ruft `cancel()`); Aufwand ~1 h. Bei der CLI
  ist Abbruch = Prozess killen (heute `register(proc)` in diarize.py).
- Gleichzeitige Aufrufe: SpeakerKit-Doku sagt «Concurrent callers are
  safe»; nicht gemessen.
- Speicher nach `rt_unload` nicht gemessen.
- Nur arm64 gebaut (Core ML/ANE — Plan nennt ohnehin Apple-silicon-only).
- Test nur mit der 2-min-Demo; die 5-min-Feldaufnahme vom 13.9. war nicht
  im Worktree. Da die Kerne identisch sind (gleiche Objekte, gleiche
  Optionen), ist Abweichung bei anderem Material nicht zu erwarten.

## Empfehlung E5

**Shim im Prozess (Variante a).** Begründung:

- Funktioniert in einem Tag (hier: ~70 min), linkt mit einem einzigen
  zusätzlichen Flag, braucht keine Runtime-Dylibs im Bundle.
- Ergebnis byte-identisch zur CLI, deterministisch, unter Sandbox ohne
  Entitlement.
- Entfällt: `bin/argmax-cli` (6,6 MB) im Bundle, das Symlink-/Temp-RTTM-
  Geschiebe aus diarize.py, das ps-Identifizieren fremder Prozesse, das
  Sekunden-Polling. Audio kann direkt als f32-Puffer aus dem
  AVAssetReader-Pfad (M4) übergeben werden — kein WAV auf Platte.
- Modelle bleiben zwischen Jobs warm (70–90 ms und Prozessstart gespart).

Bedingungen: (1) Aufruf aus einem Blocking-Thread, nie aus dem Main-
Thread; (2) `rt_cancel` nachrüsten, bevor der Kindprozess abgeschaltet
wird; (3) Fortschritt entweder upstream-Patch (Fork, eine Zeile) oder
zeitbasierter Schätzer bis 85; (4) Dependency in `Package.swift` auf
`revision: "ea872ff"` pinnen und `Package.resolved` einchecken.

Der Kindprozess (Variante b) bleibt belegter Rückfallweg: er läuft unter
Sandbox mit `inherit`, wenn das Kind im Bundle liegt — nicht im Container.
