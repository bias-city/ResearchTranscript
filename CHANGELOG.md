# Changelog

All notable changes to ResearchTranscript (LocalTranscript until 2.5.0,
TurnScript in 3.0.0). The GitHub release notes for
a version are the corresponding section of this file.

## 0.6.2 — not yet released

- **Settings: three cards were unreachable.** Frame and columns sat on the same
  element — fixed height, vertical scrolling and a two-column layout at once. As
  soon as the content was taller than two screen-high columns, the rest flowed
  into a third and fourth column to the right, where vertical scrolling never
  goes. Privacy, licences and the log button were therefore missing in the app;
  found in the TestFlight build. The frame now scrolls and an inner element holds
  the columns. Measured before and after at three window sizes.

## 0.6.1 — not yet released

Answer to Apple's rejection of 0.6.0 (22 September 2026, guideline 2.5.2,
"The app installed or launched executable code. Specifically, the app uses the
itms-services URL scheme to install an app").

- **The reported string is gone.** `itms-services` came from the Python standard
  library inside the app: `urllib/parse.py` lists it in the data table
  `uses_netloc`, next to `ws`, `wss` and `git+ssh`. The app never builds, opens or
  handles such a URL. CPython ships an official App Store compliance patch that
  removes the entry; the redistribution we build on leaves it out (visible in the
  bundled `config-3.13-darwin/Makefile`: `APP_STORE_COMPLIANCE_PATCH=` is empty).
  The build now applies it and recompiles the bytecode.
- **The embedded Python runtime no longer carries tooling it does not need.**
  Removed from the shipped bundle: `pip` (10 MB, with PyPI address, download and
  install commands, a vendored HTTP stack and six Windows launcher executables),
  `venv`, CPython's build directory (`Makefile`, `install-sh`, `makesetup`,
  `python.o`), `pkgconfig`, and `ctypes/macholib/fetch_macholib`, a shell script
  that fetches source code from a third-party server. The development server
  `main.py` (uvicorn) is no longer shipped either; nothing in the bundle imports it.
- **Two guards keep it that way:** `scripts/pruefung-2-5-2.mjs` checks the
  assembled resources and, a second time, the finished bundle before upload. Either
  finding stops the build.
- **Smaller attack surface:** the window's open command only accepts `http`,
  `https`, `mailto` and `zotero` addresses and treats everything else as a path;
  `LT_WHISPER_CLI` is honoured inside the bundle only if it points into the bundle;
  the path to the LAME library always comes from the bundle; the web inspector is a
  build feature of the DMG channel and is no longer part of the App Store build.

## Unreleased

- **DOI.** ResearchTranscript is archived on Zenodo in the community
  [BIAS.CITY](https://zenodo.org/communities/bias-city):
  [10.5281/zenodo.22831469](https://doi.org/10.5281/zenodo.22831469)
  for all versions, 10.5281/zenodo.22831470 for 0.6.0. The DOI is in
  `CITATION.cff` (with ORCID), the README, the website, the About dialog
  and the BibLaTeX entry of the documentation package (app: from the
  next build). `scripts/zenodo.py` files each release as a new version.
- **Authorship and AI assistance** stated in the README, on the website
  and on Zenodo.
- README: ffmpeg is no longer listed as bundled (gone since 0.6.0).
- Source archives: `pyo3-config.txt` is generated per machine
  (`scripts/pyo3-config.mjs`) and no longer checked in, so no local path
  ends up in an archive; `BACKLOG.md`, `CLAUDE.md` and `spike/` are
  left out of source archives (`.gitattributes`). The Zenodo copy of
  0.6.0 is restricted for that reason; the code is public on GitHub.

## 0.6.0 — 2026-09-18

First version prepared for the Mac App Store; the same code is published
here as a signed and notarised DMG. It includes 0.5.0, which was never
published on its own.

### Added

- **Documentation for researchers, generated from the real values of a
  transcript** (Editor › Export › "Documentation package (.zip) …"): nine
  short Word documents in three folders — a transcription record (app and
  model of the run, editing by hand from the journal, files with
  checksums), a paragraph for the methods section in a short and a long
  form, facts about the app for records of processing, impact assessment
  and ethics applications, a form for what only the institution knows, a
  repository data sheet following the Zenodo form and DataCite, an ethics
  checklist, repositories and funder requirements, and a citation file
  for Zotero. The app states nothing it cannot know; open fields are
  marked `[ … ]`. Background and sources: `docs/begleitdokumente.md`.
- **How much the human changed.** On creation the app keeps the machine
  result (`ausgang.json`). Against it the record reports a word-level
  correction rate (counted like a word error rate with the final version
  as reference, normalised and orthographic) and the share of reassigned
  speech time. A second measure from the journal — share of segments with
  changed wording or speaker — is always available, also for transcripts
  made by earlier versions. These measure intervention, not accuracy.
- **Transcript export as Markdown and Word**, written without a third-party
  library.
- **Manual inside the app**: Help menu (⌘?) or the Help pill at the bottom
  left open a second window with 15 chapters, full-text search, every
  keyboard shortcut and pictures in light and dark — in German, English,
  French and Italian.
- **Editor**: timecodes to the hundredth of a second (editable per line,
  running in the active line, footer, header and playhead; CSV and
  REFI-QDA labels write `hh:mm:ss.hh`); memos per line with markers in the
  waveform, exported to CSV and REFI-QDA; zoomable waveform in the
  speakers' colours; speaker colours; turn editing from the keyboard
  (Enter, ⌫, ⌥Enter for interjections); foot-pedal keys (Page Up/Down);
  playback speed 0.75–2×; the app reopens where it was closed.
- **Appearance**: dark mode following macOS, uniform pill buttons, transcript
  text in sans-serif or serif (system fonts only — no font file is
  bundled), adjustable text size.
- `CITATION.cff`; `LICENSE-EXCEPTION` (additional permission under AGPL §7
  for App Store distribution); complete third-party licence list inside
  the app.

### Privacy and packaging

- **App Sandbox in both channels.** Folders are reached through the system
  dialog and kept as security-scoped bookmarks; Zotero needs its folder to
  be chosen once.
- **French addresses the reader with «tu» throughout**, like German «du»
  and Italian «tu».
- The website and its template documents describe 0.6.0: there is no
  internal service and no open port any more.

### Changed

- **Audio and speaker separation run inside the app.** Decoding,
  probing and clipping use Apple's AVFoundation; MP3 is written by LAME
  (LGPL-2.0+, built from the official 4.0 sources without decoder,
  dynamically linked so it can be replaced — the source tarball ships
  with the app and is linked from the About dialog). Speaker separation
  calls SpeakerKit (Core ML) directly instead of a helper process, with
  real progress. Speech recognition still runs `whisper-cli` as a
  separate process, deliberately: a crash or the model's memory stays
  outside the app. Results are the same — measured against ffmpeg and
  argmax-cli: identical sample counts, speaker segments byte-identical,
  MP3 within 0.4 %.
- **ffmpeg and argmax-cli are no longer bundled.** The app is 100 MB
  smaller and carries no GPL component any more; the strictest bundled
  licence is now the LGPL of LAME.
- **WebM is no longer accepted as an audio source** (AVFoundation does
  not read it). Existing entries with a WebM audio file stay readable;
  new recordings in WebM must be converted first — mp3, m4a, aac, wav,
  ogg, flac and H.264/HEVC video remain.
- Cancelling a run during speaker separation now takes effect when the
  separation finishes (about 25 s for a 3.4-hour recording) instead of
  immediately; decoding, encoding and transcription cancel at once.

### Internal

- Motor protocol (`motor.py`, `LT_MOTOR=kind|prozess`): the old child
  processes remain available in a checkout for comparison. Swift package
  `RTMotoren` (src-tauri/swift), Rust module `researchtranscript_motoren`
  (PyO3), Cargo feature `motoren` (default). `scripts/baue-lame.sh`.
  Parity report: spike/motoren-swift/BEFUND.md.

## 0.5.0 — 2026-09-17 (not published on its own; part of 0.6.0)

### Changed

- **Python now runs inside the app.** Until 0.4.0 the app started a
  Python web server on port 5628 and talked to it over HTTP. Since
  0.5.0 the same Python logic runs inside the app process (embedded
  CPython 3.13); the interface calls it directly. Visible effects: the
  app opens instantly (no "backend starting" wait), there is no port,
  no leftover process after a crash, and audio/video play straight from
  the library file. Nothing changes in the library, the transcript
  format or the exports.
- **The waiting list survives a restart.** Files dropped into the AI
  Transcript tab, with their chosen speaker count, are kept until they
  are started or removed — a crash or an accidental quit no longer
  empties the list.
- **A log for problems.** The app keeps a small local log (errors,
  processing messages); "Open log" in the settings shows it. If
  processing ever stops responding, a banner says so and offers a
  restart.
- The AGPL §13 wording and the privacy card now say what is true:
  there is no server and no listener in the app.

### Internal

- Bundle without a virtual environment (`python/site-packages`), no
  FastAPI/uvicorn in the app, empty hardened-runtime entitlements;
  start self-check with a plain-text dialog. Preparation for the Mac
  App Store build (docs/appstore-plan.md).

## 0.4.0 — 2026-09-16

### Changed

- **TurnScript is now ResearchTranscript, and version counting restarts
  at 0.4.0.** Two transcription apps carry names close to the previous
  ones, so the project takes a name that says what it is for. The count
  starts over in line with the other B/IAS tools, which are also in
  their zero series. The application, its bundle identifier
  (`city.bias.researchtranscript`), the repository and the website carry
  the new name; old addresses redirect. The releases 2.5.0 and 3.0.0
  remain available and are superseded.
- **No settings are carried over.** ResearchTranscript starts as a fresh
  installation and asks once for the library folder, where an existing
  library can be picked. That keeps the upgrade path simple and removes
  the one piece of machinery that had gone wrong in 3.0.0.
- **Your material stays readable.** Transcripts and dossiers written by
  LocalTranscript or TurnScript are still recognised as the app's own,
  and REFI-QDA exports keep the same identifiers, so ATLAS.ti sees the
  same sources as before.

## 3.0.0 — 2026-09-15

### Changed

- **LocalTranscript is now TurnScript.** Another transcription app uses
  a name close to the old one, so the application, its bundle identifier
  (`city.bias.turnscript`), the repository (github.com/bias-city/TurnScript)
  and the website carry the new name. Old GitHub and download links
  redirect.
- **Nothing is lost on the way.** On first launch TurnScript copies the
  settings of LocalTranscript, including the chosen library folder,
  and leaves the old ones in place. New installations are offered an
  existing LocalTranscript library folder instead of an empty one. Dossiers
  written by LocalTranscript are still recognised as TurnScript's own, and
  re-exporting to REFI-QDA keeps the same identifiers, so ATLAS.ti sees the
  same sources as before.

- **Fuller attribution for the diarization models.** Argmax's model
  repository now states its licence in its own metadata: the SpeakerKit
  framework is MIT, the models it is built on are CC BY 4.0. That
  licence asks for attribution and for marking changes, so the licence
  list in Settings, the README, the website and the four information
  sheets now name both models, pyannote community-1 and WeSpeaker
  ResNet34, and say that Argmax converted them to Core ML and quantised
  them. The licence list in Settings carries the same full wording.

## 2.5.0 — 2026-09-13

### Changed

- **New speaker separation.** Speakers are now found by pyannote
  community-1 running on the Mac's Neural Engine, through Argmax's
  SpeakerKit command line (MIT). The old chain (silero-VAD plus
  SpeechBrain ECAPA plus agglomerative clustering) knew nothing about
  overlapping speech and miscounted voices. Measured on the same
  five-minute field recording: the old chain invented eight speakers in
  8.4 seconds, the new one finds three in 0.9 seconds, and with a
  speaker count given it returns exactly that many (two speakers, 0.8
  seconds). An hour-long workshop recording is separated in 11.9
  seconds. Nothing is downloaded: the models sit in the application
  package and are read from there.
- **The application package shrinks by about 770 MB.** PyTorch,
  torchaudio, SpeechBrain, silero-vad, scikit-learn and SciPy leave the
  bundle (793 MB); the Core ML models and the command line add 24 MB.
  Voice activity detection for transcription is unaffected. It still
  runs inside whisper.cpp with the bundled Silero model.
- **Licence note.** The bundled weights are pyannote community-1
  (CC-BY-4.0), the runtime is SpeakerKit by Argmax (MIT). Both are
  listed in Settings, on the website and in the four information
  sheets.

### Added

- **Every recording in the queue gets its own speaker count, and
  nothing starts without one.** Dropped files now collect in a list
  instead of starting straight away. Each line carries its own choice,
  and the start button stays locked while one is missing. The count
  shapes the result, so it is written into the transcript's source data
  and journal, where it can be read back later. The setting in the
  options is now only a default for newly added files; dropping several
  files at once leaves the choice open.

### Fixed

- **The voice sample stops the one before it.** Two quick clicks played
  two voices at once. A second click on the same voice now stops it, and
  leaving the speaker panel silences it.
- **Clicking beside a speaker badge no longer opens the speaker menu.**
  The badge button used to fill its whole column, so the empty strip
  between badge and text belonged to it. That strip is now neutral: a
  click there takes the focus out of the text field, which is what the
  up and down arrow keys need to walk the segments again.

## 2.4.3 — 2026-09-12

### Fixed

- **No more invented lines on silence.** Whole-file transcription now
  runs with whisper.cpp's voice-activity detection (Silero VAD v5 as
  ggml, bundled inside the package): passages without speech are
  skipped instead of being filled with “* Musik *” or a sentence that
  repeats eight times. Measured on a five-minute field recording: same
  time, same word count, zero repetition loops instead of eight,
  timestamps unchanged. A clip with no speech at all yields an empty
  transcript. As a safety net, three or more identical consecutive
  segments are collapsed into one.
- **Smooth video playback.** The picture now runs freely at the
  audio's rate and is only re-aligned on play/pause, on a jump, or when
  it drifts more than a second; the former quarter-second corrections
  (a seek every few seconds) made 4K HEVC from an iPhone stutter.
  Measured: 20 s of 4K, zero seeks, zero stalls, zero dropped frames.
- **Short clips no longer crash speaker separation.** A recording with
  a single speech window made the clustering abort (“Found array with
  1 sample(s)”); it is now one speaker.

## 2.4.2 — 2026-09-12

### Changed

- **Loading feedback everywhere.** A spinner in the header turns while
  any request to the backend is running or the editor is building a
  long transcript; the editor shows “n segments being built …” while
  the rows appear.
- **The editor opens long transcripts three times faster.** Row
  heights were measured one row at a time while the list grew (a forced
  layout per row); they are now measured in one batch — 1200 segments
  in 0.6 s instead of 2.1 s in WebKit.
- **Re-importing a dossier keeps the Zotero role selection.** The
  chosen roles are reconstructed from the people who travelled with the
  layer, so “Reload” after an import fetches the same roles.
- Release tooling: the app is notarised outside `tauri build` with a
  two-hour timeout (`scripts/notarize-app.mjs`), the DMG is built and
  signed by `scripts/build-dmg.mjs` — a slow Apple queue no longer
  costs the build.

## 2.4.1 — 2026-09-11

### Changed

- **Side-panel tabs wrap instead of overflowing.** Speakers | Find |
  Metadata keep their full labels; when the column is too narrow the
  buttons wrap onto a second line (the third tab used to run past the
  panel edge).
- **Portrait video is bounded.** The picture under the speakers is
  limited to 45 % of the window height and letterboxed, so a 9:16
  recording no longer pushes the speaker list off the column.

## 2.4.0 — 2026-09-11

### Added

- **enrich-core is a public MIT package.** The dossier reader/writer
  that LocalTranscript bundles — manifest, schemas, journal, naming
  convention, transcript source, Zotero layer — now lives at
  <https://github.com/BenPohlBasel/enrich-core> under the MIT licence,
  like `FORMAT.md`. The app is built against the tagged release
  (v0.1.0), so the source offer of the AGPL app covers everything in
  the bundle. Settings name it in the licence list.

- **Video as a source.** Drop an MP4/MOV/M4V (H.264 or HEVC) into the
  batch list or pick it as the audio of an import: the sound track is
  extracted to mp3 as the working copy for Whisper and the editor, the
  video file itself is stored unchanged in the entry — nothing is
  transcoded, ever. Only limit: 10 GB per file. Other containers and
  codecs (webm/VP9, mkv, AVI, MPEG-2, AV1) are refused with a hint to
  export as H.264/MP4 externally. In the editor the picture sits under
  the speakers in the side panel — muted, without controls; the audio
  player leads and the picture follows (position, play/pause, speed);
  at 2× and during jumps it freezes and blurs until the picture is back.
  Export: REFI-QDA gets a second entry “with video” (`VideoSource`,
  video in the Media folder); the enrich dossier stays audio only.

### Changed

- **Zotero roles are shown as Zotero names them** — `interviewer`,
  `interviewee`, `director`, `castMember`, … in English, for every item
  type alike, no longer translated: they are Zotero's creator types, not
  app text. Any item type can be linked (video, audio, podcast, film,
  document …); the interviewed side (`interviewee`, `guest`,
  `castMember`, `performer`, `presenter`) is never preselected.

## 2.3.0 — 2026-09-11

### Changed

- **The `.enrich` export carries no PDF any more.** FORMAT.md §5 now
  says transcript + audio are a valid input state and the receiving
  application typesets the reading copy itself — enrich does so on
  import. The export shrinks to the transcript layer
  (`source/transcript.json`, origin per record), the audio as mp3 and
  the Zotero layer; PDF typesetting, PyMuPDF (AGPL-3.0) and the
  Recursive fonts leave the bundle (about 60 MB smaller). The app's
  licence stays AGPL-3.0-or-later by choice; the strictest bundled tool
  is now ffmpeg.

### Added

- **Your own Whisper models.** Drop any whisper.cpp model
  (`ggml-*.bin`) into the library's `Modelle` folder and it appears in
  the model list, marked as your own; a file with the same name as a
  bundled model replaces it. Files are checked (ggml magic, finished
  copying) before they are offered; Settings show the folder, open it,
  rescan, and name what was ignored and why. The app never downloads
  models; the journal records which model transcribed a recording.
  A file that iCloud has evicted from the Mac ("Optimise Mac Storage")
  is reported as such and not opened — opening it would block until
  iCloud has fetched it.

- **Metadata from Zotero.** A third tab in the editor's side panel —
  Speakers | Find | Metadata — links a transcript to an item in your
  local Zotero library. Search by title, year, name or citekey
  (interviews ranked first), pick which people go into the transcript
  by role (the interviewee is not preselected, so a pseudonymised
  transcript does not get their name through the back door), link,
  reload, unlink. The snapshot is stored in the transcript as `source`
  and the link is a human run in the journal. In the `.enrich` export
  it becomes the layer `source/zotero.json`; enrich puts "Title · Date ·
  Interviewer · Citekey" on page 1 when it typesets the text. Zotero is
  read only on request, only read-only (`zotero.sqlite` opened
  immutable — Zotero can stay open), only on this computer, and only
  after you enable it in Settings (optional data directory; the usual
  places are searched otherwise). Nothing is sent to Zotero or the
  network.

- **Export and import follow Format 2 of the enrich dossier**
  (`FORMAT.md` in the enrich repository), built on enrich-core's own
  manifest models so enrich reads it. The container is one uncompressed
  `.enrich` file, laid out by enrich's naming convention (FORMAT.md
  Appendix A: `source/`, `text/`) and packed by enrich-core's own
  `handover` profile: the transcript is the source
  (`source/transcript.json`, schema
  `transcript/1.0.0`, registered in inventory and lineage,
  `source.canonical`), the typeset PDF is `rendered`, every layer
  carries the header `kind · id · origin · from · by · did · result`,
  and the manifest is a complete inventory — every file, including the
  audio, with hash and size — plus lineage (`layers`) and a chained
  journal (`runs`). Import verifies the inventory and refuses a
  container whose files no longer match their hashes. Format-1
  dossiers (earlier exports, enrich's own transcript dossiers) are
  still read.
- **Origin on every record.** Each segment and speaker carries
  `origin`: `machine` for what Whisper and the diarisation produced,
  `source` for a VTT/CSV imported from elsewhere, `human` for anything
  a person touched in the editor — text, speaker, boundaries, a name.
  Only the editor sets `human`; imports carry the flags over and never
  flatten them. Older library entries are upgraded on read.
- **Journal.** Every write is a run: the Whisper job (model,
  diarisation), an import, and each editor session (bundled — ten
  minutes of quiet close a run) with the ids of
  the records it changed and the kind of change. Runs name the app, the
  installation id and, if set, the e-mail; they are chained by the hash
  of the preceding entry and travel with the dossier.

- **Identity in the dossier** (Settings). An optional e-mail address as
  the app's user ID: it is written into every enrich dossier you export
  — as the person in the journal of who edited what and when — and
  leaves the computer only inside the file you pass on yourself. The
  settings say so next to the field. Alongside it a random
  installation ID (`ins-…`), generated on first launch, shown and
  regenerable in Settings; it tells two installations apart in a
  journal without naming a device or a person. Never a hardware UUID or
  hostname.

### Changed

- **The enrich dossier is one file: `.enrich`.** The export no longer
  writes `.enrich.zip` but `<name>.enrich` — a zip container like
  `.docx` or `.qdpx`, stored without compression (the audio inside does
  not compress anyway). enrich opens it by content. On macOS the app
  declares the dossier type, so a `.enrich` shows as a single document
  whether or not enrich is installed.
- **Import takes the dossier in both forms:** the `.enrich` file, and
  the dossier folder as enrich keeps it while working (a package on
  macOS) — chosen in the dialog or dropped onto the Human Editor list.
  Files named `.enrich.zip` by earlier versions are still read; they are
  just no longer produced or offered.
- Drag and drop onto the Human Editor list imports `.enrich`, `.vtt`
  and `.csv` files.

## 2.2.0 — 2026-09-09

Requires macOS 14 or later, Apple Silicon. Signed with a Developer ID
and notarised by Apple; the notarisation tickets are stapled to both
the disk image and the app.

### Added

- **REFI-QDA export (`.qdpx`)** for ATLAS.ti, NVivo and MAXQDA. The
  transcript is written both as a `TextSource` and as the
  `Transcript` of an `AudioSource`, with one `SyncPoint` per utterance
  (character offset ↔ millisecond). Speakers become codes; each
  utterance becomes a coded selection. The audio is placed in a
  `<name> Media/` folder alongside the `.qdpx`.
- **Transcript handover through `.enrich.zip`.** The dossier now also
  carries `transkript.json`, the canonical model. The Human Editor
  import accepts `.zip` and restores transcript and audio unchanged;
  analysis layers are discarded. Dossiers without the file are read
  from the time map at turn granularity.
- **Find and replace** as a second tab in the side panel. Literal
  matching, no regular expressions. Options for case sensitivity and
  for hyphenation (finds `Werk- statt` for `Werkstatt`). Replace,
  skip, replace all.
- **Batch queue** with a setting for simultaneous runs (Settings →
  Standard options, default 1). Files are processed in the order they
  were dropped; waiting runs are marked as such.
- **Elapsed and estimated time** per run in the batch list, projected
  from actual progress.
- **About dialog** with version and links to source code, releases,
  licence text and the bundled tools.
- **Formats card** in Settings listing the interchange formats and the
  licences of their specifications.

### Changed

- **Licence: AGPL-3.0-or-later** (previously GPL-3.0-or-later).
  PyMuPDF (AGPL-3.0) typesets the dossier PDF in the enrich export;
  GPLv3 §13 permits the combination but extends the AGPL network
  clause to the work as a whole. The backend binds to `127.0.0.1`
  only and rejects foreign hosts, and the source is public.
- **Backend port 5628** (previously 44100), overridable with
  `LT_SERVE_PORT`. The browser interface is at
  <http://127.0.0.1:5628/>.
- **Speaker count** offers exact values 1–6 and Automatic instead of
  overlapping ranges. Selecting 1 disables speaker detection.
- **Speaker detection reports progress**; cancelling now takes effect
  immediately instead of after the full detection pass.
- **Window title** appears once instead of twice.
- Icon set unified on one size scale; 16 px layout grid throughout the
  interface.
- Transport controls centred; timecodes use tabular figures.

### Fixed

- Arrow key navigation between segments while playback is paused.
- Text field and row actions overlapped in the segment list.
- Simultaneous speaker detection could terminate the backend process.
- A second instance could terminate the first instance's backend.
- Baselines within a segment row were misaligned.

### Bundled components

whisper.cpp (MIT) · large-v3-turbo model (OpenAI, MIT) · silero-vad
(MIT) · SpeechBrain ECAPA (Apache-2.0) · PyMuPDF (AGPL-3.0) ·
Recursive typeface (SIL OFL 1.1) · FastAPI/uvicorn (MIT) ·
React/Radix (MIT) · Lucide (ISC) · ffmpeg 9.0.1, GPL static build from
<https://ffmpeg.martin-riedl.de> (source:
<https://ffmpeg.org/download.html>) — the GPL §6 source offer.

The REFI-QDA specification is MIT-licensed, Copyright 2019 REFI-QDA.
LocalTranscript supports export to REFI-QDA; this is not an official
certification, and the MIT licence of the specification does not cover
trademarks.

## 2.0.0 — 2026-08-30

Complete rebuild as a Tauri app (previously Electron): fully offline
transcription with speaker diarisation, a library model, a segment
editor and the enrich export.

- Three tabs: AI Transcript (drop, options, batch list), Human Editor
  (library and VTT/CSV import), Settings (de/en/fr/it).
- Canonical storage: one folder per transcript with `transkript.json`
  (speakers as entities), history snapshots on every save, trash
  instead of deletion. VTT/CSV/TXT are derived exports.
- Editor: autosave, rename/merge/assign speakers with audio samples,
  split/join/delete segments, player with follow mode, timecodes
  always hh:mm:ss.
- Exports: VTT (standard voice tags), CSV, TXT and `.enrich.zip`.

### Withdrawn releases

Versions 2.1.0 through 2.1.3 were published and withdrawn. Their app
bundles carried an incomplete code signature: the `.app` had no
`_CodeSignature/` seal, which macOS reports as “damaged”. The tags
remain in the repository; the disk images are no longer available.
Their changes are contained in 2.2.0.
