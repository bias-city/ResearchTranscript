# Befund M4: AVFoundation statt ffmpeg (Phase 0, Nebenmessung Ton)

Datum 2026-09-17 · macOS 26.5 (Darwin 25.5.0), Apple Silicon, Swift 6.3.2 ·
Vergleichs-ffmpeg: das gebündelte `frontend/src-tauri/resources/bin/ffmpeg`
(9.0.1, martin-riedl-Build) · ffprobe aus Homebrew nur zum Nachmessen.

Werkzeug: `avspike.swift` (ein Swift-Kommandozeilenprogramm, ~450 Zeilen),
bauen mit `swiftc -O avspike.swift -o avspike -framework AVFoundation
-framework AudioToolbox -framework Accelerate`. Unterbefehle `decode`,
`probe`, `clip`, `chan`, `mp3writer`, `mp3converter`, `mp3lame`
(Kopfkommentar der Datei). Fixtures in `fixtures/`, Ergebnisse in `out/`
(die Referenz-WAVs `ref_*` sind ffmpegs `-vn -ar 16000 -ac 1 -c:a pcm_s16le`,
genau der Aufruf aus `jobs._konvertiere`).

Was ffmpeg heute tut (nur gelesen): `jobs._konvertiere` (Datei → 16-kHz-mono-
s16-WAV), `jobs._clip` (Ausschnitt aus dem WAV), `video.sondiere/pruefe`
(Codec-Tag h264/hevc, Masse, Dauer aus `ffmpeg -i`-stderr), `video.ton_befehl`
und `exporte` (Tonspur → MP3 `libmp3lame -q:a 2`), Hörprobe in `main.py`
(`-ss/-t` auf dem Bibliotheks-Audio → 16-kHz-WAV).

## 1. Dekodieren nach 16 kHz mono Float32

Drei Wege gemessen:

- **mix** = `AVAssetReaderAudioMixOutput` mit `AVSampleRateKey 16000,
  AVNumberOfChannelsKey 1` (Umtastung + Downmix im Reader).
- **track** = `AVAssetReaderTrackOutput` mit denselben Einstellungen
  (identisches Ergebnis wie mix, gleiche Zahlen — nicht separat gelistet).
- **nativ** = `AVAssetReaderTrackOutput` ohne Konvertierung (Float32, native
  Rate/Kanäle) → eigener Downmix (L+R)/n → `AVAudioConverter`
  (`sampleRateConverterQuality = max`) auf 16 kHz. **Empfohlener Weg.**

Vergleich mit ffmpeg: Länge in Samples, Kreuzkorrelation der ersten 10 s
(Lag ±100 ms), nach Ausrichtung maximale Abweichung (in LSB eines
16-Bit-Samples), SNR gegen ffmpeg breitbandig und unter 3,4 kHz (Tiefpass,
was Whisper hauptsächlich sieht), Gain-Faktor dec/ref. Laufzeiten sind
Wanduhr; die ffmpeg-Zeit ist der ganze Prozess (Start + Dekodieren +
Schreiben), die AVFoundation-Zeit Datei → Samples im Speicher.

| Datei | Weg | Samples AVF / ffmpeg | Versatz | maxAbw | SNR breit / <3,4 kHz | Gain | Zeit AVF / ffmpeg |
|---|---|---|---|---|---|---|---|
| interview.mp3 (44,1 k mono, 123 s) | mix | 1 967 938 / 1 967 226 (+44,5 ms) | −13,1 ms (−209) | 8685 LSB | 18,6 dB / — | 0,992 | 0,17 s / 0,07 s |
| interview.mp3 | nativ | 1 967 944 / 1 967 226 (+44,9 ms) | −13,1 ms | 2222 LSB | 34,6 / 46,4 dB | 0,999 | 0,16 s |
| IMG_7192.m4a (AAC 48 k **stereo**, 25 s) | mix | 401 301 / 401 307 (−0,4 ms) | +0,06 ms | 6110 LSB | 6,3 / 6,9 dB | **1,369** | 0,08 s / 0,04 s |
| IMG_7192.m4a | nativ | 401 307 / 401 307 (0) | 0 | 701 LSB | 27,8 / **70,6 dB** | 0,996 | 0,09 s |
| interview.ogg (Vorbis) | mix | 1 967 220 / 1 967 226 | 0 | 8016 LSB | 19,3 dB | 0,993 | 0,18 s / 0,09 s |
| interview.ogg (Vorbis) | nativ | 1 967 226 / 1 967 226 (0) | 0 | 2123 LSB | 35,3 / 86,5 dB | 0,999 | 0,21 s |
| interview_opus.ogg (Opus 48 k) | nativ | 1 967 226 / 1 967 226 (0) | 0 | 2417 LSB | 35,3 / 86,5 dB | 0,999 | 0,26 s / 0,14 s |
| video_h264.mp4 (avc1 + AAC) | nativ | 720 000 / 720 000 | 0 | 1768 LSB | 35,0 / 82,8 dB | 0,999 | 0,12 s / 0,04 s |
| video_hevc.mov (hvc1 + AAC) | nativ | 720 000 / 720 000 | 0 | 1768 LSB | 35,0 / 82,8 dB | 0,999 | 0,11 s / 0,04 s |
| video_hev1.mp4 (hev1-Tag) | mix | 719 994 / 720 000 | 0 | 7983 LSB | 19,4 dB | 0,993 | 0,08 s / 0,04 s |
| IMG_7192.flac (24 bit stereo, aus m4a) | nativ | 401 600 / 401 307 (+18 ms) | 0 | 701 LSB | 27,8 / 70,6 dB | 0,996 | 0,10 s |
| interview.flac (ffmpeg direkt aus mp3) | alle | **Fehler** −11800 / `fmt?` (1718449215) | | | | | |
| interview.webm (Opus in Matroska) | alle | **keine Spur** (`asset.tracks` leer, `isReadable=false`) | | | | | |
| long.mp3 (1 h, 30× Interview) | mix | 59 032 741 | | | | | 2,36 s / **1,79 s** |
| long.mp3 (1 h) | nativ | 59 032 747 | | | | | 3,13 s |

Lesart:

- **Der Reader-eigene Umtaster (mix/track) ist grob**: ~19 dB gegen ffmpeg
  bei allen Quellen — das ist Filterunterschied oberhalb ~6 kHz, kein
  Fehler, aber deutlich. Der Weg **nativ + AVAudioConverter(max)** liegt bei
  35 dB breitbandig und 46–87 dB unter 3,4 kHz — für Whisper gleichwertig
  mit ffmpeg. (Für mp3 nur 46 dB, weil zusätzlich die Dekoder differieren.)
- **Stereo-Downmix**: `AVAssetReaderAudioMixOutput` mischt mit ≈0,707·(L+R)
  (Gain 1,37 gegen ffmpegs 0,5·(L+R); die iPhone-Notiz hat L/R-Korrelation
  nur 0,28, darum SNR 6 dB). Die Kanalanalyse (`chan`) zeigt: (L+R)/2 selbst
  gemischt + AVAudioConverter trifft ffmpeg mit 70 dB (<3,4 kHz). Also
  **selbst mischen**, nicht dem AudioMixOutput überlassen.
- **mp3-Versatz 13 ms**: AVFoundation liefert 209 Samples (= 576 bei 44,1 k,
  der LAME-Encoder-Delay) mehr am Anfang und ~500 mehr am Ende: ffmpeg
  schneidet per LAME/Xing-Tag Encoder-Delay und Padding weg
  (`start: 0.025057` in `ffmpeg -i`), AVFoundation nur den Decoder-Delay.
  Das ist ein *konstanter* Versatz von 13 ms für mp3-Eingaben — unter der
  Whisper-Auflösung (20 ms), aber: Zeitstempel im Transkript wären um 13 ms
  später als heute. Hypothese (nicht gemessen): WKWebView spielt dasselbe
  mp3 über dieselbe Apple-Dekodierung, d. h. der AVFoundation-Weg wäre
  gegenüber dem Player sogar konsistenter als ffmpeg. m4a/mov/ogg/opus/flac:
  **kein** Versatz, Länge identisch.
- **Laufzeit**: bei der 1-h-Datei ist ffmpeg (1,8 s) schneller als
  AVFoundation (2,4 s mix / 3,1 s nativ); Apples mp3-Dekoder ist langsamer
  als ffmpegs. Für den 3,4-h-Workshop hiesse das ~11 s statt ~6 s — im
  Rahmen des Jobs irrelevant (Whisper braucht Minuten). Bei AAC ist
  AVFoundation etwa gleich schnell.

### Formatmatrix (Ergebnis)

| Format | AVAssetReader | Bemerkung |
|---|---|---|
| mp3 | ja | 13-ms-Versatz, s. o. |
| m4a/AAC (auch HE-AAC, ALAC, AMR laut Decoder-Liste) | ja | Decoder-IDs des Systems: `.mp1 .mp2 .mp3 aac* ac-3 alac alaw apac flac ilbc ima4 lpcm opus samr sawb ulaw usac vorb …` |
| mp4/mov mit H.264 oder HEVC (avc1/hvc1/hev1) | ja | Tonspur, Video bleibt liegen |
| flac | **ja, mit Fussnote** | Der Fehler `fmt?` trat nur bei FLACs auf, die ffmpeg direkt aus dem mp3 kodiert hatte — diese haben Blockgrösse **47** (STREAMINFO min=max=47; Nebeneffekt der mp3-Frame-Grösse im Encoder-Pfad). FLAC aus WAV (Block 4096/4608, ffmpeg wie afconvert) und aus der m4a (Block 960) dekodiert AVFoundation. Reale FLACs (Rekorder, XLD, dBpoweramp) haben 4096/4608. Also: Apples FLAC-Dekoder lehnt exotisch kleine Blöcke ab; die kanonische Wahrheit für die Format-Matrix sollte ein *echter* FLAC-Fixture sein, nicht ein ffmpeg-Transcode aus mp3. `afconvert`/`AVAudioFile` scheitern an derselben Datei (`ExtAudioFileSetProperty ('cfmt') failed ('fmt?')`) — es ist der System-Decoder, nicht der Reader. |
| ogg/Vorbis | **ja** (überraschend) | `codec=vorb`; Sondierung meldet `bitrate=0` und Dauer 139 s statt 123 s (falsche Asset-Dauer!), Dekodat aber vollständig und lagegleich |
| ogg/Opus | ja | `opus` ist auch als *Encoder* im System |
| webm/mkv | **nein** | Matroska-Container unbekannt: 0 Spuren, `isReadable=false` |
| wav/aiff/caf | ja (nicht gemessen, lpcm) | |

## 2. Sondieren (Ersatz für `video.sondiere`)

`AVURLAsset.tracks` → `CMFormatDescriptionGetMediaSubType` liefert den
Vierzeichen-Tag direkt (kein stderr-Regex):

| Datei | AVFoundation | ffprobe / `ffmpeg -i` |
|---|---|---|
| video_h264.mp4 | `vide codec=avc1 1280x720 fps=30.00`, `soun codec=aac 44100 Hz ch=1`, dauer 45,000 | `h264 / avc1 1280x720 30/1`, `aac mp4a 44100 mono`, 45.000000 |
| video_hevc.mov | `vide codec=hvc1 1920x1080 fps=30.00`, `aac 44100 ch=1`, 45,000, playable=true | `hevc / hvc1 1920x1080`, 45.000000 |
| video_hev1.mp4 | `vide codec=hev1 640x360`, **playable=false** (readable=true, Ton dekodiert trotzdem) | `hevc / hev1 640x360` |
| IMG_7192.m4a | `aac 48000 Hz ch=2`, dauer **25,082** | `aac mp4a 48000 stereo`, **25.130667** (ffmpeg zählt Priming/`start 0.044` mit; AVFoundation die editierte Dauer — AVF ist hier die «richtige» Spieldauer) |
| interview.mp3 | `.mp3 44100 ch=1`, 122,984 | mp3 44100 mono, 122.951610 (Xing-getrimmt) |
| interview.ogg | `vorb 44100 ch=1`, **139,153** (falsch), bitrate 0 | vorbis, 122.951610 |
| interview.flac | `flac 44100 ch=1`, 122,952 (Sondierung geht, Dekodieren dieser Datei nicht) | flac 44100 mono |
| interview.webm | keine Spuren, dauer 0 | opus 48000 mono |

Breite/Höhe: `CMVideoFormatDescriptionGetDimensions` = ffprobe `width/height`;
`naturalSize` berücksichtigt zusätzlich die Drehmatrix (iPhone-Hochkant), was
`video.sondiere` heute gar nicht kennt. Bitraten auf das Bit identisch
(`estimatedDataRate` 524905 = ffprobe 524905). Cover-Art in mp3/m4a erscheint
in AVFoundation **nicht** als Videospur (kein `mjpeg/png`-Sonderfall mehr
nötig). `hev1`-Dateien meldet AVFoundation als `playable=false` — das ist
genau der Fall, den WKWebView nicht abspielt; `pruefe` könnte `isPlayable`
statt der Codec-Liste benutzen (heute lässt `CODECS_OK` hev1 durch).

## 3. Ausschnitt per `reader.timeRange` (Hörprobe)

1 s ab Sekunde 30, ohne die ganze Datei zu lesen (die Lage im ffmpeg-
Volldekodat per Kreuzkorrelation gemessen):

| Datei | Samples | Lage tatsächlich | Zeit AVF | ffmpeg `-ss 30 -t 1` |
|---|---|---|---|---|
| interview.mp3 | 15 994 (1,000 s) | **30,039 s** (39 ms spät; = 1,5 mp3-Frames, Frame-Raster + der 13-ms-Versatz) | 0,05 s | 16 000, 30,000 s, 0,02 s |
| video_hevc.mov | 15 994 | 30,000 s | 0,05 s | 15 997, 30,000 s |
| IMG_7192.m4a (ab 10 s) | 15 994 (1,000 s) | — | 0,05 s | |
| interview.ogg | **12 848 (0,80 s)** | **30,374 s** | 0,06 s | 16 000, 30,000 s |

Für mp4/m4a sample-genau; für mp3 auf ~40 ms genau (für eine 8-s-Hörprobe
unerheblich, für `_clip` nicht relevant — das schneidet aus dem WAV bzw. aus
den Samples im Speicher). Für Ogg ist das Seeking im Reader unbrauchbar
(37 % zu spät, zu kurz) — Ogg-Eingaben würden nach dem Import ohnehin als
mp3 in der Bibliothek liegen (`ton_befehl`/Regel «.enrich-Audio IMMER
mp3»), die Hörprobe liest nie ein Ogg. 5 994 statt 6 000 Samples (0,4 ms):
Umtast-Rundung des Readers, im nativ-Weg 0.

## 4. MP3-Kodierung

### (a) Apple — kodiert nicht

- `AudioFormatGetProperty(kAudioFormatProperty_EncodeFormatIDs)`:
  `aac aace aacf aacg aach aacl aacp alac alaw apac flac ilbc ima4 lpcm opus ulaw`
  — **kein `.mp3`** (Decoder-Liste enthält `.mp3`). Apples alte Formattabelle
  stimmt also noch: MP3 «decode only». Neu ist FLAC und Opus als Encoder.
- `AudioConverterNew(PCM → kAudioFormatMPEGLayer3)`: Status 1718449215
  `'fmt?'` = `kAudioConverterErr_FormatNotSupported` (Gegenprobe PCM→AAC: 0).
- `ExtAudioFileCreateWithURL(kAudioFileMP3Type, MPEGLayer3)`: liefert
  überraschend 0, aber `ExtAudioFileSetProperty(ClientDataFormat=PCM)` →
  `'fmt?'` und `ExtAudioFileWrite` → 1885563711 `'pck?'`. Kein Weg.
- `AVAssetWriter(outputURL:fileType: .mp3)`: NSException
  `NSInvalidArgumentException — -[AVAssetWriter initWithURL:fileType:error:]
  Invalid file type UTI. Available file types are: com.scenarist.closed-caption,
  org.w3.webvtt, public.aiff-audio, com.apple.m4v-video,
  org.3gpp.adaptive-multi-rate-audio, com.apple.m4a-audio,
  com.apple.quicktime-audio, com.microsoft.waveform-audio,
  com.apple.coreaudio-format, com.apple.immersive-video, public.3gpp,
  public.mpeg-4, com.apple.itunes-timed-text, com.apple.quicktime-movie,
  public.aifc-audio`. (Ausgabe des Kindprozesses; Swift kann NSException
  nicht fangen — in der App darf dieser Aufruf nie ausgeführt werden.)

### (b) libmp3lame per dlopen — geht

- `brew --prefix lame` = `/opt/homebrew/opt/lame`, **LAME 4.0** (Homebrew-
  Bottle, Lizenz laut Formel **LGPL-2.0-or-later**), `lib/libmp3lame.0.dylib`
  **215 872 Bytes**, arm64-only, Abhängigkeit: `libmpg123.0.dylib`
  (271 856 Bytes, LGPL-2.1) — LAME 4.0 linkt den Decoder von mpg123; für das
  Bundle also entweder beide dylibs in `Contents/Frameworks` oder LAME mit
  `--disable-decoder` selbst bauen (dann nur eine, für das Kodieren ist mpg123
  unnötig). Dazu `libmp3lame.a` 304 656 Bytes (statisch — für LGPL nicht
  empfohlen, s. Plan).
- Aufruf über `dlopen`/`dlsym` (13 Symbole, `@convention(c)`), Einstellung
  wie ffmpegs libmp3lame-Wrapper: `lame_set_VBR(vbr_mtrh)`,
  `lame_set_VBR_quality(2.0)` (= `-q:a 2`), `bWriteVbrTag=1`,
  `write_id3tag_automatic=0`, Eingabe `lame_encode_buffer_ieee_float`
  (mono) / `…_interleaved_ieee_float` (stereo) mit den nativ dekodierten
  Samples (44,1 k mono bzw. 48 k stereo, wie ffmpeg ohne `-ar`).
  Stolperstein: `lame_get_lametag_frame(gf, NULL, 0)` liefert **vor** dem
  Kodieren 0 — LAME setzt den Xing/Info-Platzhalter selbst in den ersten
  Ausgabeblock; nach `lame_encode_flush` liefert die Funktion 417 (44,1 k)
  bzw. 384 (48 k) Bytes, die den Dateianfang überschreiben. Ohne diesen
  Schritt zeigt ffprobe/der Player eine falsche VBR-Dauer.

| Quelle | LAME-Ergebnis (ffprobe) | ffmpeg `-q:a 2` (ffprobe) | Zeit LAME (Kodieren + Dekod.) / ffmpeg |
|---|---|---|---|
| interview.mp3 | mp3 44100 mono, **122,996 s**, 101 163 b/s, 1 555 350 B | 122,952 s, 101 300 b/s, 1 556 890 B | 0,33 + 0,14 s / 0,34 s |
| IMG_7192.m4a | mp3 48000 stereo, 25,082 s, 188 465 b/s, 590 880 B | 25,082 s, 188 527 b/s, 591 074 B | 0,18 + 0,08 s / 0,18 s |
| video_hevc.mov | mp3 44100 mono, 45,000 s, 100 382 b/s, 564 651 B | 45,000 s, 100 359 b/s, 564 522 B | 0,13 + 0,10 s / 0,14 s |
| long.mp3 (1 h) | 46 627 875 B, 364× Echtzeit | | 10,1 + 2,5 s / 10,4 s |

Bitrate, Grösse, Dauer stimmen auf 0,1 % überein (derselbe Encoder, dieselbe
Qualitätsstufe). Die 45 ms Mehrdauer beim mp3→mp3-Fall sind der Versatz aus
Abschnitt 1 (AVFoundation trimmt Encoder-Delay/Padding nicht). Der 3,4-h-
Workshop bräuchte ~35 s reine Kodierzeit — muss im Job bzw. in `detach`
laufen, wie der Plan sagt, mit Fortschritt aus der Sample-Position.

## 5. Sandbox-Hinweis (nicht gemessen)

Alle Aufrufe hier sind reine Datei-Lese-/Schreibzugriffe im eigenen Prozess:
`AVURLAsset` auf eine Nutzerdatei braucht den security-scoped URL aus dem
Open-Panel (`files.user-selected.read-write`) — gilt für Dekodieren,
Sondieren, Ausschnitt gleichermassen (alle öffnen die Quelldatei; die
Hörprobe liest aus dem Bibliotheksordner, der bei Variante A im Container
oder per Bookmark erreichbar ist). Schreiben (MP3, WAV) geht in Container/
`$TMPDIR`. Kein XPC, kein Kindprozess, kein `cs.*`-Entitlement; VideoToolbox/
AudioToolbox laufen im Sandbox-Prozess (WKWebView tut dasselbe). `dlopen`
von `libmp3lame.dylib` aus `Contents/Frameworks` verlangt nur dieselbe
Signatur/Team-ID wie die App (Hardened Runtime; sonst
`disable-library-validation`, das der Store nicht mag) — die Bibliothek
also im Bundle mitsignieren, nicht aus Homebrew laden.

## 6. Empfehlung

**AVFoundation + libmp3lame (dynamisch), wie im Plan §5 vorgesehen — mit
drei Präzisierungen aus der Messung:**

1. **Dekodieren über `AVAssetReaderTrackOutput` nativ, Downmix (L+R)/n
   selbst, Umtastung mit `AVAudioConverter` (Qualität max).** Nicht den
   `AudioMixOutput` mit `AVSampleRateKey` benutzen: dessen Umtaster liegt bei
   ~19 dB gegen ffmpeg und sein Stereo-Downmix hat +3 dB und stimmt nicht
   mit ffmpeg überein; der nativ-Weg liegt bei 35 dB / 70–87 dB (<3,4 kHz),
   Länge und Lage identisch. Sechs Aufrufstellen wie geplant
   (`dekodiere_16k`, Slice, `nach_mp3`, `sondiere`, Hörprobe).
2. **MP3 nur über LAME** — Apple kodiert nicht (drei APIs geprüft, Fehler
   dokumentiert). dylib 216 KB (+272 KB mpg123 bei Homebrew-Bau; eigener Bau
   ohne Decoder empfohlen), LGPL-2.0+, Quell-Tarball auf bias.city wie
   geplant. Xing-Tag nach dem Flush zurückschreiben (Stolperstein oben).
3. **Sondierung** über Track-Formatbeschreibungen (`avc1/hvc1/hev1`,
   Dimensions, `naturalSize` mit Rotation, `isPlayable`) — schärfer als der
   heutige stderr-Regex; Cover-Art-Sonderfall entfällt.

**Was wegfällt:** `.webm` (Matroska: 0 Spuren) — steht heute in
`bibliothek.AUDIO_ENDUNGEN` (`.mp3 .m4a .aac .wav .ogg .flac .webm`) und in
`paket.AUDIO_NAMEN`/`main.py`-MIME-Tabelle, ist also ein belegter Verlust:
aus den Listen nehmen, CHANGELOG-Pflicht, Fehlermeldung «bitte als m4a/mp4
exportieren» wie bei fremden Video-Codecs (`VIDEO_ENDUNGEN` = mp4/m4v/mov
sind alle abgedeckt). **Nicht** weg:
`ogg` (Vorbis und Opus dekodieren beide, nur Seeking und Asset-Dauer sind
unzuverlässig — für den Import egal, da alles zu mp3 wird), `flac` (geht für
normale Blockgrössen; ein ffmpeg-Fixture direkt aus mp3 erzeugt Block 47 und
scheitert — Format-Matrix mit echtem FLAC-Fixture belegen). Bekannte,
akzeptierte Abweichungen: mp3-Eingaben 13 ms später als ffmpeg (konstant,
unter Whisper-Auflösung; vermutlich player-konsistent), mp3-Dekodieren ~1,3×
langsamer als ffmpeg (1 h: 3,1 s statt 1,8 s).

Gegen die Alternative LGPL-ffmpeg als Bibliothek spricht: 20–40 MB
Shared-Libs mit Neulink-Pflicht, Lizenzwächter, Codec-Bundle — für einen
Gewinn, der sich auf webm/mkv und 13 ms beschränkt. Eine Mischung
(AVFoundation + ffmpeg-Fallback nur für Matroska) lohnt sich erst, wenn
webm-Eingaben in der Praxis vorkommen (Browser-Aufnahmen, Teams/Meet-
Downloads sind mp4/m4a).

## Dateien

- `avspike.swift` — Messprogramm (Bauzeile im Kopf).
- `fixtures/` — aus `docs/demo/housing-cooperatives-interview.mp3` erzeugt:
  `interview.{mp3,flac,ogg,webm}`, `interview_opus.ogg`, `interview16.flac`
  (Block 47, scheitert), `interview_apple.flac` (afconvert, geht),
  `interview_fromwav.flac` (geht), `video_h264.mp4`, `video_hevc.mov`,
  `video_hev1.mp4`. Die iPhone-Sprachnotiz `~/Desktop/IMG_7192.m4a`
  und ihre FLAC-Ableitungen sowie alle daraus dekodierten/kodierten
  Ausgaben in `out/` wurden nach der Messung entfernt (private Aufnahme
  mit Ortsmarke); die Zahlen stehen oben. `long.mp3` (1 h) ebenfalls
  entfernt (42 MB; `ffmpeg -stream_loop 29 -i interview.mp3 -c copy`).
- `out/` — `ref_*` ffmpeg-Referenzen, `av_*`/`avnat_*` AVFoundation-Dekodate,
  `lame_*.mp3` / `ffm_*.mp3` die beiden Kodierwege, `av_clip_*` Ausschnitte.
