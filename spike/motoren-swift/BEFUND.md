# Befund: RTMotoren — eine C-Schnittstelle für die Motoren der App

Spike zu docs/appstore-plan.md §5, aufbauend auf spike/avfoundation (M4) und
spike/speakerkit-shim (F3). Stand 2026-09-17. Rechner: Apple M3 Pro, macOS 26.5
(Darwin 25.5.0), Xcode 26.5, Swift 6.3.2, Rust 1.93.0, swift-rs 1.0.8, LAME 4.0
(Homebrew). Vergleichs-ffmpeg: `frontend/src-tauri/resources/bin/ffmpeg` (9.0.1),
ffprobe 9.0 (Homebrew) nur zum Nachmessen, `resources/bin/argmax-cli`, Modelle
`resources/models/speakerkit`.

## Kurzfassung

Das SwiftPM-Paket `RTMotoren` (statische Bibliothek, 6 C-Funktionen, JSON-Rückgaben)
ersetzt die vier ffmpeg-/argmax-Aufrufstellen der Motor-Schicht (`motor.py`:
`sondiere`, `wav16k`, `nach_mp3`, `diarize`) im Prozess. Parität:

- **wav16k (Volldekodat)**: Samplezahl und Lage identisch mit ffmpeg für m4a/mp4/mov/
  ogg/opus/flac (Δ 0, Lag 0), SNR 35 dB breit / 79–84 dB unter 3,4 kHz — dieselben
  Zahlen wie im AVFoundation-Befund. mp3: konstant −13,1 ms (LAME-Delay), +32,9 ms
  länger (Padding), 34,6 / 46,4 dB — wie M4, akzeptiert.
- **Ausschnitt (start/dauer)**: sample-genau und **bit-identisch mit dem Stück des
  eigenen Volldekodats** für mp3 (auch 1 h VBR bei 3000 s), wav, flac, mov, ogg, opus;
  gegen ffmpeg `-ss -t` dieselbe Lage (0,0 ms; mp3 −13,1 ms). Das ging erst mit
  `AVAudioFile.framePosition` statt `AVAssetReader.timeRange` — Letzteres liegt bei
  VBR-mp3 bis **±1 s** daneben (gemessen, s. §3b). `_clip` aus dem 16-kHz-WAV:
  bit-identisch mit ffmpeg (SNR ∞).
- **mp3**: gegen `ffmpeg -q:a 2` Dauer gleich, Bitrate und Grösse auf 0,1–0,4 %
  (derselbe Encoder), Laufzeit gleich (1 h: 9,1 s vs. 9,5 s).
- **diarize_wav**: RTTM **byte-identisch** mit `argmax-cli` (5-min-Feldaufnahme 62
  Segmente/3 Sprecher, Demo 16/2; automatisch und n=2), warm 0,70 s je 5 min, 1 h in
  7,6 s.
- **Abbruch**: wav16k der 1-h-Datei nach 2 s → Rückgabe nach **2,004 s**, keine Ziel-
  datei; mp3 1,003 s. **Diarize lässt sich nicht unterbrechen** (SpeakerKit trägt die
  Pipeline in einem unstrukturierten `Task`, Cancel erreicht sie nicht): die Rückgabe
  `abgebrochen` kommt erst nach dem Ende (1 h: 7,5 s).
- **Threads**: alles blockiert den rufenden Thread, nichts braucht den Main-Thread.
  Diarize und Dekodieren laufen gleichzeitig aus mehreren Threads korrekt (Ausgaben
  byte-identisch), skalieren aber nicht: 2× 1-h-mp3 parallel 5,2 s statt 2,4 s
  einzeln, 4 Diarisierungen parallel je 2,5 s statt 0,7 s.

## 1. Was gebaut wurde

```
spike/motoren-swift/
├── RTMotoren/                       SwiftPM-Paket, statische Bibliothek (macOS 13+)
│   ├── Package.swift                Abhängigkeit ../../speakerkit-shim/argmax-oss-swift (@ ea872ff)
│   ├── include/rtmotoren.h          DIE C-Schnittstelle (66 Zeilen)
│   └── Sources/RTMotoren/
│       ├── Gemeinsam.swift          JSON, Callbacks, Fortschritt (monoton), WAV lesen/schreiben, rt_free
│       ├── Ton.swift                rt_dekodiere_wav16k: NativLeser (AVAssetReader), DateiLeser (AVAudioFile), Downmix, Umtaster
│       ├── Lame.swift               rt_nach_mp3: libmp3lame per dlopen, VBR, Xing-Tag
│       ├── Sondiere.swift           rt_sondiere
│       └── Diarize.swift            rt_diarize_wav / rt_unload_models (SpeakerKit)
├── rt-motoren-probe/                Cargo-Binary: swift-rs SwiftLinker in build.rs, ruft alle Funktionen
├── vergleich-wav.swift              leseWav/versatz/vergleiche 1:1 aus spike/avfoundation/avspike.swift
├── paritaet.sh                      alle Messungen dieses Befunds (Aufruf s. §7)
└── BEFUND.md
```

Swift 844 Zeilen, Rust 213, Header 66. Keine Zusatzfeatures; die JSON-Rückgaben
tragen zwei Zusatzfelder, die die Messung brauchte (`quelle_rate`, `quelle_kanaele`,
`quelle_frames`, `leser` bei wav16k; `abtastrate`, `kanaele` bei sondiere; `rate`,
`kanaele`, `lame` bei mp3).

### Schnittstelle (include/rtmotoren.h, Auszug)

```c
typedef bool (*rt_abbruch_cb)(void *ctx);                   /* true = abbrechen */
typedef void (*rt_fortschritt_cb)(double anteil, void *ctx); /* 0..1, monoton */
char *rt_sondiere(const char *pfad);
char *rt_dekodiere_wav16k(const char *pfad, const char *ziel_wav, double start_s, double dauer_s,
                          rt_abbruch_cb, rt_fortschritt_cb, void *ctx);
char *rt_nach_mp3(const char *pfad, const char *ziel_mp3, int vbr_q, const char *lame_dylib,
                  rt_abbruch_cb, rt_fortschritt_cb, void *ctx);
char *rt_diarize_wav(const char *wav_pfad, int32_t num_speakers, float cluster_distance_threshold,
                     bool exclusive, const char *model_dir, rt_abbruch_cb, rt_fortschritt_cb, void *ctx);
void  rt_unload_models(const char *model_dir);
void  rt_free(char *p);
```

Alle Rückgaben JSON-C-Strings (`rt_free`), Fehler `{"error":"…"}`, Abbruch
`{"error":"abgebrochen"}` (Zieldatei gelöscht). Callbacks dürfen NULL sein.
`lame_dylib` NULL → `dlopen("libmp3lame.dylib")` über den dyld-Suchpfad (geprüft mit
`DYLD_LIBRARY_PATH`; in der App: `@rpath` auf `Contents/Frameworks`).

Erprobte Wege 1:1 übernommen: nativ dekodieren (`AVAssetReaderTrackOutput` ohne
Konvertierung) → eigener Downmix (L+R)/n (vDSP) → `AVAudioConverter` Qualität max
(M4); LAME per dlopen, `lame_set_VBR(vbr_mtrh)`, `VBR_quality(q)`, `bWriteVbrTag=1`,
`write_id3tag_automatic=0`, Xing-Tag nach `lame_encode_flush` an den Dateianfang
(M4); SpeakerKit-Aufruf, Konfiguration, Label `A + id % 26`,
`updateSegments(minActiveOffset: 0)`, Cache je Modellordner, `Task.detached` +
`DispatchSemaphore` (F3).

**Neu gegenüber den Spikes** (aus der Messung nötig, s. §3):

1. Dekodieren **streamt** (Block → Downmix → Umtaster → s16-WAV auf Platte); der
   1-h-Fall braucht 24 MB RSS statt 635 MB Samples im Speicher.
2. Ausschnitt: Leser je Container — mp3/wav/aiff/caf/flac über **`AVAudioFile` mit
   `framePosition`** (CoreAudio baut die Pakettabelle: sample-genau auch bei VBR-mp3);
   mp4/m4v/mov/m4a über `AVAssetReader.timeRange` (Sample-Tabelle, exakt; `AVAudioFile`
   ignoriert bei `.mov` die Edit-Liste und liegt 23 ms früh); Ogg und Unbekanntes
   `AVAssetReader` von vorn (Ogg-Seeking landet ~37 % zu spät und meldet trotzdem die
   Soll-PTS — nicht erkennbar). Immer 0,5 s Vor- und Nachlauf lesen, alles durch den
   Umtaster, **Schnitt erst im 16-kHz-Raster** → der Ausschnitt ist ein bit-identisches
   Stück des Volldekodats (ohne das: 30–40 ms Stille am Anfang durch das Einschwingen
   des Umtasters, SNR 10 dB).
3. Umtaster meldet dem `AVAudioConverter` **nie `.noDataNow`** (Ausgabegrösse an den
   Vorrat gekoppelt, ein Block Reserve): sonst hängt der Flush der Filterverzögerung
   (192 Samples) davon ab, wie der Reader die Blöcke schneidet.
4. mp3-Quellen werden auf die nominelle Spurlänge **gekappt**: der `AVAssetReader`
   liefert das LAME-Padding am Ende mal mit, mal nicht (162 708 480 oder 162 709 009
   Frames bei 1 h — auch sequenziell, 1 von 3 Läufen). Nach der Kappe: 3 sequenzielle
   und 4 parallele Läufe byte-identisch.
5. Diarize: Abbruch-Callback wird auf dem rufenden Thread alle 100 ms gepollt
   (`sem.wait(timeout:)`), Fortschritt aus `Progress.completedUnitCount / 100`, WAV-
   Leser für s16 und f32.

### Bauen

```sh
cd spike/motoren-swift
# Swift allein (Prüfung; cargo tut es selbst über swift-rs):
(cd RTMotoren && swift build -c release)          # 42 s kalt (argmax-oss-swift komplett), 5–10 s inkrementell
# Rust-Probe (baut den Swift-Teil im OUT_DIR mit):
export PATH="$HOME/.cargo/bin:$PATH"
(cd rt-motoren-probe && cargo build --release)    # 47 s kalt, ~60 s bei Swift-Änderung
# Vergleichswerkzeug:
swiftc -O vergleich-wav.swift -o vergleich-wav -framework Accelerate
```

Voraussetzung: `spike/speakerkit-shim/argmax-oss-swift` (Klon @ ea872ff, gitignored;
Klonbefehl im Shim-Befund). `build.rs` = das des Shim-Spikes (`SwiftLinker::new("13.0")
.with_package("RTMotoren", "../RTMotoren")` + `-Wl,-rpath,/usr/lib/swift`).
`Package.swift` linkt AVFoundation/AudioToolbox/Accelerate explizit (Autolink täte es
auch). Nur Deprecation-Warnungen (synchrone `AVAsset`-Properties, wie im avspike).

| Artefakt | Grösse |
|---|---|
| `libRTMotoren.a` (84 Objekte: ArgmaxCore, WhisperKit, TTSKit, SpeakerKit, RTMotoren) | 13,9 MB |
| `rt-motoren-probe` (fertige Binary) | 3,7 MB |
| `otool -L` der Binary | nur Systempfade + `@rpath/libswift_Concurrency.dylib` mit `LC_RPATH /usr/lib/swift` (wie F3) |

### Probe

```
probe sondiere <datei>
probe wav16k <datei> <ziel.wav> [start dauer]
probe mp3 <datei> <ziel.mp3>                  RT_LAME_DYLIB (sonst /opt/homebrew/opt/lame/lib/libmp3lame.dylib), RT_VBR_Q (2)
probe diarize <wav> <modelldir> [n] [aus.rttm]  RT_SCHWELLE (0.62), exclusive immer; RT_WIEDERHOLE=k warme Läufe
probe parallel <wav> <modelldir> <datei> <ziel.wav> [<datei2> <ziel2> …]   Thread 0 diarize, 1..k wav16k
probe parallel-diarize <wav> <modelldir> <k>
RT_ABBRUCH_NACH_S=<s>   Abbruch-Callback liefert nach s Sekunden true (jeder Aufruf eigener ctx)
RT_FORTSCHRITT_ALLE=1   ganze Fortschrittsfolge ausgeben
```

Jeder Aufruf meldet auf stderr Wandzeit, Zahl/erster/letzter Fortschrittswert,
Monotonie, Zeitpunkt der Abbruchmeldung.

## 2. Sondieren

| Datei | rt_sondiere | ffprobe |
|---|---|---|
| video_h264.mp4 | `avc1`, aac, 1280×720, 45,000 s, 660 806 b/s, playable | h264/avc1, aac/mp4a, 1280×720, 45,000, 667 973 (Format-Bitrate) |
| video_hevc.mov | `hvc1`, aac, 1920×1080, 45,000, 641 474 | hevc/hvc1, 648 666 |
| video_hev1.mp4 | `hev1`, aac, 640×360, **playable=false** | hevc/hev1 |
| interview.mp3 | mp3, 44 100/1, 122,984 s, 91 179 | mp3, 122,952, 91 218 |
| interview_stereo.m4a | aac, 48 000/2, 122,929 s, 129 744 | aac/mp4a, 122,952, 131 320 |
| feld5.mp3 (Bibliothek) | mp3, 48 000/2, 300,000, 192 000 | mp3, 300,000, 192 019 |
| interview_apple.flac | flac, 122,984, bitrate 0 | flac, 316 131 |
| interview.ogg / _opus.ogg | vorbis 139,153 s / opus 129,180 s, bitrate 0 | 122,952 |
| interview.webm | keine Spuren, `{"video_codec":null,"audio_codec":null,…,"playable":false}` | opus |

Codec-Tags wie ffprobe (`kAudioFormat*` → `mp3/aac/vorbis/opus/flac/pcm/alac/…`,
Video-FourCC direkt). Bitrate = Summe der Track-`estimatedDataRate` (ffprobes
Format-Bitrate zählt Container-Overhead mit, 1 %). Bekannt aus M4: Ogg-Dauer falsch,
FLAC/Ogg ohne Bitrate, m4a-Dauer ohne Priming. 12–30 ms je Aufruf.

## 3. Parität

Alle Zahlen aus `paritaet.sh` (letzter Lauf, `out/paritaet3.log` im Scratchpad).
Wandzeit ffmpeg = ganzer Prozess; RTMotoren = Funktionsaufruf (Datei → WAV auf Platte).

### (a) wav16k gegen `ffmpeg -vn -ar 16000 -ac 1 -c:a pcm_s16le`

Metrik wie M4 (`vergleich-wav`): Samples, Kreuzkorrelation der ersten 10 s, maxAbw in
LSB16, SNR breit und < 3,4 kHz, Gain.

| Datei | Samples RT / ffmpeg | Versatz | maxAbw | SNR breit / <3,4 kHz | Gain | Zeit RT / ffmpeg |
|---|---|---|---|---|---|---|
| interview.mp3 (44,1 k mono) | 1 967 752 / 1 967 226 (+32,9 ms) | −13,06 ms | 2222 | 34,6 / 46,4 dB | 0,9993 | 0,135 / 0,122 s |
| interview_stereo.m4a (AAC 48 k **stereo**, dekorrelierte Kanäle) | 1 967 226 / 1 967 226 | 0 | 3395 | 28,6 / **78,8 dB** | 0,9988 | 0,115 / 0,124 s |
| video_h264.mp4 | 720 000 / 720 000 | 0 | 1768 | 35,0 / 81,7 | 0,9993 | 0,088 / 0,067 s |
| video_hevc.mov | 720 000 / 720 000 | 0 | 1768 | 35,0 / 81,7 | 0,9993 | 0,089 / 0,063 s |
| interview.ogg (Vorbis) | 1 967 226 / 1 967 226 | 0 | 2123 | 35,3 / 84,0 | 0,9994 | 0,184 / 0,122 s |
| interview_opus.ogg | 1 967 226 / 1 967 226 | 0 | 2417 | 35,3 / 84,1 | 0,9993 | 0,229 / 0,169 s |
| interview_apple.flac | 1 967 752 / 1 967 226 (+32,9 ms) | 0 | 2259 | 35,1 / 84,0 | 0,9993 | 0,109 / 0,075 s |
| feld5.mp3 (Bibliotheks-mp3, 48 k stereo, 5 min) | 4 800 000 / 4 799 824 (+11 ms) | 0 | 1408 | 37,2 / 78,8 | 0,9995 | 0,44 s |
| long.mp3 (1 h) | 59 032 555 | | | | | **2,41 / 1,53 s** |
| long.m4a (1 h AAC) | | | | | | 1,21 s |

Identisch mit dem AVFoundation-Befund (nativ-Weg): der Stereo-Downmix (L+R)/2 trifft
ffmpeg mit 79 dB unter 3,4 kHz; das Streaming (Blöcke, `.noDataNow`-freier Umtaster,
s16-Rundung) hat nichts verändert. mp3: +32,9 ms Länge = Xing-nominale Länge (4708
Frames × 1152; ffmpeg trimmt Delay/Padding, wir nicht — wie beim FLAC aus afconvert),
Lage −13 ms konstant. Fortschritt: ein Callback je Reader-Block (≈ 0,19 s Audio; 664
je 2 min, 19 845 je Stunde), monoton, 0 → 1.

### (b) Ausschnitt gegen `ffmpeg -ss -t` (Hörprobe, `_clip`)

Erst der Umweg, der die Regel in §1 Punkt 2 erklärt. `AVAssetReader.timeRange` (0,5 s
Vorlauf, per PTS getrimmt) — Lage des 1-s-Ausschnitts im ffmpeg-Volldekodat, Soll 0
(mp3: −13 ms):

| Quelle | 5 s | 30 s | 60 s | 90 s | 120 s | 600 s | 3000 s |
|---|---|---|---|---|---|---|---|
| interview.mp3 (VBR, Xing+TOC, Lavc) | −13 | **+91** | **+353** | **−65** | **+118** | | |
| `ffmpeg -q:a 2`-mp3 (was `ton_befehl` erzeugt) | −13 | **−327** | +13 | +39 | +65 | | |
| RTMotoren/LAME-q2-mp3 | 0 | **+131** | 0 | +26 | +78 | | |
| long.mp3 (1 h VBR) | | | | | | **−980** | **−474** |
| CBR 128 k (Info-Kopf) | −13 | −13 | −13 | −13 | −13 | | |
| feld5.mp3 (Bibliothek, CBR 192 k) | 0 | 0 | 0 | 0 | 0 | 200 s: 0 | |

Der Reader interpoliert bei VBR den Xing-TOC (100 Byte-Stützstellen, 1/256-Auflösung —
bei 3,4 h sind das 2 min je Stützstelle); die Fehler wachsen mit der Dateilänge. ffmpeg
selbst seekt exakt (`-ss 3000` auf 1 h: 0,0 ms, 0,06 s). **`AVAudioFile.framePosition`**
dagegen: −13,1 ms an allen Positionen und Dateien inklusive 1 h bei 3000 s (Öffnen
5–16 ms, Seek+1 s lesen 2–14 ms).

Endstand (RTMotoren = AVAudioFile für mp3/wav/flac, Reader-timeRange für mp4/mov/m4a,
von vorn für Ogg; Schnitt im 16-kHz-Raster):

| Ausschnitt | Leser | Samples RT / ffmpeg | Lage im ffmpeg-Volldekodat | Lage im RT-Volldekodat | bit-identisch mit RT-Slice | SNR gegen ffmpeg-Clip | Zeit |
|---|---|---|---|---|---|---|---|
| interview.mp3 30+8 s (Hörprobe) | audiofile | 128 000 / 128 000 | −13,1 ms | 0,0 | **ja** | 22 dB (Lag) | 18 ms |
| interview.mp3 0+5 | audiofile | 80 000 / 80 000 | −13,1 | 0,0 | ja | 34,5 / 48,9 | 12 ms |
| interview.mp3 120+10 (über das Ende) | audiofile | 47 752 / 47 226 | −13,1 | 0,0 | ja | 28,9 | 10 ms |
| feld5.mp3 200+8 | audiofile | 128 000 / 128 000 | 0,0 | 0,0 | ja | 29,2 / 33,7 | 22 ms |
| long.mp3 3000+8 | audiofile | 128 000 / 128 000 | −13,1 | 0,0 | ja | 22 (Lag) | 27 ms |
| long.mp3 600+1 | audiofile | 16 000 / 16 000 | −13,1 | 0,0 | ja | | 12 ms |
| interview_stereo.m4a 10+1 | reader-timerange | 16 000 / **15 915** | 0,0 | 0,0 | nein (24 dB) | 15,8 | 55 ms |
| interview_stereo.m4a 60+8 | reader-timerange | 128 000 / **127 829** | 0,0 | 0,0 | nein (29 dB) | 19,5 | 61 ms |
| video_hevc.mov 30+1 | reader-timerange | 16 000 / 15 997 | 0,0 | 0,0 | **ja** | 27,4 / 31,3 | 56 ms |
| video_h264.mp4 20+8 | reader-timerange | 128 000 / 127 751 | 0,0 | 0,0 | nein (62,7 dB) | 17,1 | 63 ms |
| interview.ogg 30+1 | reader-von-vorn | 16 000 / 16 000 | 0,0 | 0,0 | ja | 33,4 / 82,1 | 91 ms |
| interview_opus.ogg 60+2 | reader-von-vorn | 32 000 / 32 000 | 0,0 | 0,0 | ja | 28,5 / 30,6 | 146 ms |
| interview_apple.flac 30+1 | audiofile | 16 000 / 16 000 | 0,0 | 0,0 | ja | 33,4 / 82,2 | 11 ms |
| ref_interview_mp3.wav 12,345+3,21 (`_clip`) | audiofile | 51 360 / 51 360 | 0,0 | 0,0 | ja | **∞ (bit-identisch mit ffmpeg)** | 4 ms |

Lesart: Die «SNR gegen ffmpeg-Clip» ist bei mp3 durch den konstanten 13-ms-Lag und bei
allen kurzen Clips durch ffmpegs *eigene* Schnittkanten gedrückt (ffmpeg liefert bei
AAC 85–249 Samples zu wenig, bei mov 3, sein Umtaster schwingt am Clip-Anfang ein);
aussagekräftig ist die Spalte «bit-identisch mit RT-Slice»: der Ausschnitt ist genau das
Stück, das `_konvertiere` als Volldekodat liefert — für die Hörprobe und für jede
spätere Slice-Umsetzung im Speicher dasselbe Ergebnis. Ausnahme AAC: nach einem Seek
weicht der CoreAudio-AAC-Dekoder um 24–29 dB (stereo) bzw. 63 dB (mono) vom
Volldekodat ab, Lage exakt; mit `AVAudioFile` genauso (gemessen), also Dekoder-Zustand
(vermutlich PNS-Rauschersatz), nicht das Seeking — für eine Hörprobe unhörbar. Ogg von
vorn kostet die Dekodierzeit bis `start` (1,5 ms/s Audio); Ogg-Eingaben liegen in der
Bibliothek ohnehin als mp3.

### (c) mp3 gegen `ffmpeg -vn -c:a libmp3lame -q:a 2`

| Quelle | RTMotoren (ffprobe) | ffmpeg (ffprobe) | Grösse RT / ffmpeg | Zeit RT / ffmpeg |
|---|---|---|---|---|
| interview.mp3 | 44 100 mono, 122,984 s, 101 145 b/s | 122,952 s, 101 271 b/s | 1 555 246 / 1 556 890 B (−0,11 %) | 0,358 / 0,356 s |
| interview_stereo.m4a | 48 000 stereo, 122,952 s, 225 105 | 122,952, 225 952 | 3 460 320 / 3 473 471 (−0,38 %) | 0,852 / 0,838 s |
| video_hevc.mov | 44 100 mono, 45,000, 100 304 | 45,000, 100 257 | 564 651 / 564 522 (+0,02 %) | 0,169 / 0,158 s |
| long.mp3 (1 h) | 3689,535 s, 101 102 | 3689,502, 101 240 | 46 627 771 / 46 691 127 (−0,14 %) | **9,10 / 9,50 s** |

Xing-Tag: `Xing`, flags 15, TOC ja, Encoder-String `LAME4.0`, Delay/Padding
`240240` (576/576) gegen ffmpegs `034c61`; Dauer laut ffprobe stimmt (Stolperstein aus
M4 umgesetzt: Tag nach dem Flush an Offset 0 geschrieben, LAME hatte den Platzhalter
im ersten Block gesetzt). Kodierung streamt (keine Samples im Speicher), Fortschritt je
Block. Dekodierte mp3-Quellen werden 32,9 ms länger (nominale Länge, s. (a)), ffmpeg-
Ausgaben aus AAC/mov exakt gleich lang. > 2 Kanäle werden auf mono gemischt (ffmpeg
würde nach stereo mischen — nicht vorkommend, dokumentierte Grenze).

### (d) diarize_wav gegen `argmax-cli diarize`

Material: (1) 5-min-Feldaufnahme aus der Bibliothek (`feldaufnahme
stereo_L-4_R-5/audio.mp3`, Minuten 10–15, Stereo-Lavalier → Downmix; der Shim-Spike
hatte diese Aufnahme nicht mehr vorgefunden und die Demo benutzt — hier beides), (2)
`docs/demo/housing-cooperatives-interview.mp3`. 16-kHz-WAV per ffmpeg (`ref_*`), Flags
wie `diarize.py`: `--cluster-distance-threshold 0.62 --use-exclusive-reconciliation`,
ohne und mit `--num-speakers 2`. `vergleich.py` aus dem Shim-Spike, 10-ms-Raster.

| Fall | Segmente / Sprecher | Übereinstimmung | RTTM | Zeit CLI (Prozess) / RT (Aufruf, kalt) |
|---|---|---|---|---|
| Feld 5 min, auto | 62 / 3 | 100,00 % (291,45 s Sprache) | **byte-identisch** (File-ID angeglichen; CLI ohne Newline am Ende) | 0,88 / 0,79 s (Modell 81 ms + Diarize 724 ms) |
| Feld 5 min, n=2 | 57 / 2 | 100,00 % | byte-identisch | 0,86 / 0,79 s |
| Demo 2 min, auto | 16 / 2 | 100,00 % | byte-identisch | 0,58 / 0,52 s |
| Demo 2 min, n=2 | 16 / 2 | 100,00 % | byte-identisch | 0,57 / 0,54 s |
| Feld warm, 3 Aufrufe im Prozess | 62 / 3 | identisch | identisch | 0,77 / 0,70 / 0,72 s (Modell 0 ms) |
| 1 h (long.mp3-Dekodat) | 491 / 2 | | | 7,65 s (≈ 480× Echtzeit) |
| Feld aus dem **RTMotoren**-Dekodat statt ffmpeg-WAV | 59 / 3 | **98,3 %** | nicht identisch | |

Core-ML-Erstlauf im frischen Prozess/Cache 4,6 s (wie F3), danach 80 ms. Die letzte
Zeile ist die Wahrheit über den Wechsel des Dekoders: dieselbe Aufnahme über
AVFoundation statt ffmpeg dekodiert (37 dB SNR, 11 ms länger) ergibt 3 Segmente
Unterschied (1,7 % der Zeit) — die Parität «RTTM byte-identisch» gilt für die
Diarisierung, nicht für die Kette Dekoder + Diarisierung. Für den Paritätstest der
Motor-Schicht heisst das: Dekodat festhalten (WAV-Fixture), nicht die Quelle.

Fortschritt: Folge `0, 0,85, 0,92, 0,97, 1,0` — der Sprung auf 0,85 ist die F3-
bekannte Upstream-Eigenheit; bei 1 h steht die Anzeige 6,7 s auf 0,85.

### (e) Abbruch

| Aufruf | Abbruch nach | Rückgabe nach | Zieldatei | Fortschritt beim Abbruch |
|---|---|---|---|---|
| wav16k long.mp3 (1 h) | 2,000 s | **2,004 s** | gelöscht (`ls`: No such file) | 0,84 |
| mp3 long.mp3 | 1,001 s | 1,003 s | gelöscht | 0,10 |
| diarize Feld 5 min | 0,52 s | 0,81 s (= Ende) | keine (Aufrufer schreibt RTTM nicht) | lief zu Ende |
| diarize 1 h | 3,07 s | **7,54 s (= Ende)** | | lief zu Ende |

Dekodieren/Kodieren prüfen den Callback alle 0,5 s Audio (≈ alle 0,3 ms Wandzeit bei
1500× Echtzeit); die Reaktionszeit ist der Callback-Takt selbst. **Diarize**: der Shim
ruft `task.cancel()` auf dem `Task.detached`, aber SpeakerKit startet die Pipeline in
`PyannoteDiarizer.initialize` als unstrukturierten `Task { … }` (Zeile 171 @ ea872ff),
der die Cancellation des Elterntasks **nicht erbt**; dessen `Task.checkCancellation()`
je Seek-Clip und `Task.isCancelled` in den Embedder-Workern greifen nur über das
interne `reset()` (nicht öffentlich). Ein Abbruch endet also erst mit der Diarisierung
(3,4 h ≈ 25 s). Abhilfe: Fork-Patch (Pipeline als Kind-Task oder `cancel()` öffentlich,
wenige Zeilen) — oder akzeptieren, wie heute das Kill des Kindes bei laufender Core-ML-
Inferenz ohnehin nur zwischen Chunks wirkt.

## 4. Threading

- **Alle sechs Funktionen blockieren den rufenden Thread; keine braucht den Main-Thread**
  (Probe läuft ohne Run-Loop, ohne `DispatchQueue.main`; AVFoundation/AudioToolbox/
  Core ML/LAME sind hier reine Rechen- und Dateiaufrufe). In Tauri also aus
  `spawn_blocking`/Job-Thread rufen.
- Callbacks: `abbruch`/`fortschritt` bei wav16k und mp3 auf dem **rufenden Thread**
  (synchron im Dekodier-Loop). Bei diarize kommt `fortschritt` aus einem SpeakerKit-
  Thread (Swift-Concurrency-Pool), `abbruch` wird auf dem rufenden Thread alle 100 ms
  gepollt. Die `ctx`-Struktur muss also für diarize threadsicher sein (Probe: Mutex).
- **Gleichzeitig aus mehreren Threads** (Frage `max_parallel` bis 4):

| Lauf | Ergebnis |
|---|---|
| Thread 0 diarize Feld + Threads 1–3 wav16k (1 h mp3, 2 min mp3, mov) | alle vier WAVs und die RTTM **byte-identisch** zu den Einzelläufen; diarize 0,87 s (statt 0,79), 1 h 2,61 s (statt 2,41) |
| 4× wav16k (1 h ×2, feld5, mov) + diarize Demo | identisch; 1 h **je 5,23 s** statt 2,41 s, feld5 0,90 s statt 0,44 s, mov 1,48 s statt 0,09 s; CPU 7,8 s user für 4,8 s Wand (`/usr/bin/time`) |
| 2× 1-h-**AAC** parallel | 2,45 s je Datei (einzeln 1,21 s) |
| 2 / 3 / 4× diarize Feld parallel | je 1,27 / 2,05 / 2,55 s (einzeln 0,72 s); Segmente aller Threads identisch; Gesamtzeit ≈ Summe der Einzelläufe |

Also: **korrekt und sicher** (kein geteilter Zustand ausser dem gelockten SpeakerKit-
Cache und dem dlopen-Handle-Cache; jeder Aufruf eigener Reader/Converter/Encoder),
aber **kein Durchsatzgewinn**: Apples mp3-/AAC-Dekodierung und der Umtaster laufen
offenbar seriell durch einen gemeinsamen Codec-Dienst (2 Dateien → 2,2× Zeit), Core ML
teilt sich die ANE. `max_parallel` sollte deshalb weiterhin die *Jobs* begrenzen; zwei
Dekodierungen nebeneinander sind erlaubt, bringen aber nichts. Nicht gemessen: mp3-
Kodierung parallel (LAME ist je Instanz unabhängig, dlopen-Handle wird geteilt — LAME
selbst ist reentrant je `lame_t`).

## 5. libmp3lame (Homebrew), otool

```
$ otool -L /opt/homebrew/opt/lame/lib/libmp3lame.0.dylib
  /opt/homebrew/opt/lame/lib/libmp3lame.0.dylib (compatibility 1.0.0, current 1.0.0)
  /opt/homebrew/opt/mpg123/lib/libmpg123.0.dylib (compatibility 50.0.0, current 50.4.0)
  /usr/lib/libSystem.B.dylib
LC_ID_DYLIB: /opt/homebrew/opt/lame/lib/libmp3lame.0.dylib    (kein LC_RPATH)
arm64-only (215 872 B), codesign: Signature=adhoc, TeamIdentifier=not set
$ otool -L libmpg123.0.dylib → nur sich selbst + libSystem (271 856 B)
```

Für `Contents/Frameworks/libmp3lame.dylib` also: (1) `install_name_tool -id
@rpath/libmp3lame.dylib`, (2) entweder `libmpg123.0.dylib` mitliefern und die Referenz
auf `@rpath/libmpg123.0.dylib` umbiegen (`-change`), oder LAME aus dem Tarball mit
`--disable-decoder` bauen (dann keine mpg123-Abhängigkeit; die 13 dlsym-Symbole sind
alle Encoder-seitig), (3) mit der Team-ID signieren (Hardened Runtime; adhoc reicht
nicht, `disable-library-validation` will der Store nicht). Der Shim lädt über
`dlopen(pfad)` — mit `@rpath/…` als Pfad oder NULL → `libmp3lame.dylib` über den dyld-
Suchpfad, beides funktioniert (getestet mit `DYLD_LIBRARY_PATH`). LGPL-2.0+: Quell-
Tarball auf bias.city wie im Plan.

## 6. Grenzen, Stolpersteine, Fehlerwege

- **mp3-Seeking nur über `AVAudioFile`** (§3b) — `AVAssetReader.timeRange` ist bei VBR-
  mp3 unbrauchbar (bis ±1 s). Die Bibliotheks-mp3s der App sind VBR q2 mit TOC.
- **`AVAudioFile` ignoriert die Edit-Liste bei `.mov`** (23 ms früh), nicht bei `.mp4`/
  `.m4a` mit derselben `elst` — deshalb Reader für ISO-BMFF.
- **Ogg**: Reader-Seeking landet 37 % zu spät bei richtiger PTS; `AVAudioFile` öffnet Ogg
  zwar, seekt aber ungenau (+3…+23 ms, r 0,98). Von vorn lesen ist exakt.
- **Reader-Tail bei mp3 nicht deterministisch** (Padding mal dabei, mal nicht) → Kappe
  auf die nominale Länge; vor der Kappe unterschied sich das 1-h-WAV zwischen Läufen um
  192 Samples Stille am Ende.
- **`AVAudioConverter` + `.noDataNow`** verändert den End-Flush (192 Samples) je nach
  Blockung → nie melden.
- AAC nach Seek: 24–29 dB gegen das Volldekodat (stereo), Lage exakt (§3b).
- Diarize-Abbruch wirkungslos bis zum Ende (§3e).
- Fehlerwege (alle JSON, keine Zieldatei zurückgelassen): webm → `keine Tonspur
  (asset.tracks=0, readable=false)`; FLAC Block 47 → `AVFoundationErrorDomain -11800 …
  (1718449215)` (= `fmt?`, wie M4); fehlende Datei → `keine Tonspur`; `hev1` dekodiert
  (playable=false, readable=true); falscher dylib-Pfad → dlopen-Text; fehlender Modell-
  ordner, Nicht-WAV, 44,1-kHz-WAV → eigene Meldungen.
- Nur arm64 gebaut (Core ML/ANE; Plan: Apple-silicon-only).
- `Package.resolved` pinnt nur swift-argument-parser (1.8.2); argmax-oss-swift ist ein
  Pfad-Paket — produktiv `.package(url:, revision: "ea872ff")` wie im Shim-Befund.
- Speicher: 1-h-mp3 → 16-kHz-WAV mit 24 MB RSS; `rt_diarize_wav` hält das ganze WAV
  als `[Float]` (1 h = 236 MB) plus SpeakerKit-intern; `rt_nach_mp3` streamt.

## 7. Reproduktion

```sh
# Fixtures (nicht im Repo): spike/avfoundation/fixtures/* (M4) und im out-Ordner:
ffmpeg -i fixtures/interview.mp3 -filter_complex "[0:a]asplit[a][b];[b]adelay=300|300,volume=0.6[c];[a][c]amerge=inputs=2" -ar 48000 -c:a aac -b:a 128k out/interview_stereo.m4a
ffmpeg -stream_loop 29 -i fixtures/interview.mp3 -c copy out/long.mp3
ffmpeg -ss 600 -t 300 -i ~/Documents/LocalTranscript/feldaufnahme/audio.mp3 -c copy out/feld5.mp3
ffmpeg -i out/feld5.mp3 -vn -ar 16000 -ac 1 -c:a pcm_s16le out/ref_feld5.wav
ffmpeg -i docs/demo/housing-cooperatives-interview.mp3 -vn -ar 16000 -ac 1 -c:a pcm_s16le out/ref_demo.wav
# dann, aus dem Repo-Wurzelverzeichnis:
spike/motoren-swift/paritaet.sh <out-ordner> > paritaet.log 2>&1
```

Die Feldaufnahme und alle daraus abgeleiteten Dateien (feld5.mp3, ref_/rt_feld5.wav,
Clips, RTTMs) lagen nur im Session-Scratchpad und wurden nach der Messung gelöscht
(private Aufnahme); die Zahlen stehen oben.

## 8. Empfehlung für Phase 2

Die Schnittstelle trägt: eine statische Bibliothek, sechs Funktionen, ein Linkerflag,
keine Runtime-Dylibs ausser `libmp3lame` (+ mpg123 oder eigener Bau). Für `src/motoren/`
übernehmen mit drei Auflagen aus diesem Befund: (1) Ausschnitte über `AVAudioFile`
(mp3) bzw. Reader-timeRange (mp4/mov) mit Schnitt im 16-kHz-Raster — nicht über
`reader.timeRange` bei mp3; (2) Diarize-Abbruch braucht einen Fork-Patch oder die
Akzeptanz «endet mit der Diarisierung»; (3) `max_parallel` bleibt Job-Begrenzer, weil
Dekodieren und Core ML im Prozess nicht skalieren. Paritätsfixture für den Motor-Test:
das 16-kHz-WAV (nicht die mp3-Quelle), weil der Dekoderwechsel allein 1,7 % der
Sprecherzuordnung verschiebt.
