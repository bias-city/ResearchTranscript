# ResearchTranscript — Fact sheet for researchers

What the app is, which AI in it does what, where the code lives, and
why the transcript never leaves your computer. For handing to a project
lead, an ethics board or colleagues. As of 18 September 2026, version
0.6.0.

This sheet is the general template. Since 0.6.0 the app itself
generates the version for an individual transcript (Editor › Export ›
“Documentation package (.zip) …”): a transcription record with the
model and version actually used and the measured degree of editing by
hand, a methods paragraph, facts for data protection, a data sheet for
the repository and a citation file.

## What the app does

ResearchTranscript turns audio recordings — interviews, group discussions,
workshops — into text with timecodes and speaker attribution. The
transcript is then corrected in an editor, speakers are named, names are
replaced, and the result is exported for analysis (ATLAS.ti, MAXQDA,
NVivo via REFI-QDA; enrich; WebVTT, CSV, plain text, Markdown, Word).
Video recordings (MP4/MOV) are accepted too: the sound is extracted, the
video stays unchanged with the transcript and leaves the computer only
if you explicitly include it in the REFI-QDA export. All of it happens
on your own Mac.

## Which AI does what

| Component | Task | Origin, licence | Runs where |
|---|---|---|---|
| whisper.cpp 1.8.2 with the model `large-v3-turbo` | Speech recognition: audio → text with timecodes | model by OpenAI (MIT), runtime whisper.cpp (MIT) | locally, as a helper program from the app bundle, on the Mac's graphics processor (Metal) |
| Silero VAD 5.1.2 (inside whisper.cpp) | Voice activity: detects where speech occurs at all. Only when speaker diarisation is switched off; otherwise the diarisation cuts the blocks | MIT | locally, in the same helper program |
| SpeakerKit (Argmax) with the models pyannote segmentation-3.0, WeSpeaker ResNet34 and pyannote community-1 | Speaker diarisation: detects speaker changes including overlap and groups the voices; can be switched off | models from pyannote speaker-diarization-community-1 (CC BY 4.0), converted to Core ML by Argmax; SpeakerKit runtime by Argmax (MIT) | locally, in the app, via Core ML |

All models ship inside the application package; the app downloads
neither models nor program components. Audio is read by macOS itself
(AVFoundation), MP3 is written by LAME (LGPL, dynamically linked). There
is no access to an AI service, no account, no API key. Anyone wishing
to use a different whisper.cpp model places it in the library's
“Modelle” folder themselves; such a model is not part of this list, and
each transcript's journal records which model produced it.

**No summarising, no rephrasing.** The app summarises nothing and
rephrases nothing. The models do not learn from the recordings.

**Limits of speech recognition.** Speech recognition is an AI model.
Where it understands nothing (background noise, dialect, overlapping
speech) it can produce words that were not said. A transcript from
ResearchTranscript is a **raw transcript** that must be checked against the
recording; the editor is built for that. Standard German, French,
Italian and English are recognised well, Swiss German patchily — the
speakers are still separated cleanly.

## Where the code lives

- Source code: <https://github.com/bias-city/ResearchTranscript>
- Licence: AGPL-3.0-or-later, with an additional permission for
  distribution through the App Store — free software that may be used,
  inspected, modified and passed on
- Developed at B/IAS – Basel Institut für angewandte Stadtforschung,
  Beckenweg 6, 4056 Basel, <https://bias.city>
- Installer (DMG): signed and notarised with an Apple Developer ID, on
  the GitHub releases page, with a checksum
- If you do not trust the binary: the repository holds the complete
  build chain, the app can be built from source

## The transcript never leaves the computer

- The app transmits **no recordings, texts or usage data**: no account,
  no telemetry, no update check, no crash reports of its own, no model
  downloads. The macOS network entitlement is set only because the
  built-in web view requires it; a firewall or `nettop` shows that no
  connection is made.
- There is no internal service: no server, no open port. The
  application logic runs embedded inside the app. Readable by anyone:
  the shell `frontend/src-tauri/src/lib.rs` starts no server and opens
  no port.
- The app runs in the macOS App Sandbox: access only to folders chosen
  in a dialog and to files dragged in. The entitlements are in
  `frontend/src-tauri/entitlements.plist`.
- Recording and transcript live in the chosen library folder, one
  subfolder per transcript: `transkript.json` (wording, speakers, memos,
  journal, Zotero details), a copy of the recording, for video the video
  file too, `wellenform.json`, plus `ausgang.json` (the state as
  delivered by the machine or by an imported file) and `history/` (the
  last 30 states). Deleted transcripts remain in the library's
  `_papierkorb` folder until it is emptied in the Finder. Settings and
  the app log are stored in the app container of the user account.
- No cloud service, no user account, no processor, no third-country
  transfer — because nothing is transmitted.

What this does **not** cover: backups of the Mac (Time Machine, iCloud
Drive for the Documents folder) and the crash reports of macOS itself
follow the system settings, not the app. Whoever places the library
folder inside a synchronised folder synchronises the recordings.

## Pseudonymising names

- **Rename speakers:** a name in the speaker panel applies to every
  segment of that person — "Speaker 1" becomes "B3" in one step.
- **Names in the text:** "Find and replace" finds a name in all
  segments, shows each match in context and replaces one at a time or
  all at once — even where the transcript broke the name across a line.
- **What the app does not decide:** which details to replace — places,
  employers, events. That remains the researcher's decision.
- **The recording stays what it is.** What is pseudonymised is the text
  of the final version. `ausgang.json` and `history/` contain the
  wording before any pseudonymisation, the recording the voice and real
  names.
- **What exports contain.** All text formats (VTT, CSV, TXT, Markdown,
  Word): wording, speaker names, timestamps; CSV, Markdown and Word
  additionally the memos; Markdown and Word, with a Zotero link, a
  header with title, date, citekey and the persons whose roles were
  selected. REFI-QDA (`.qdpx.zip`): text, memos and the audio recording,
  i.e. the voice; on request the video file. enrich dossier (`.enrich`):
  text, audio recording as MP3, journal (installation ID, optionally
  e-mail), Zotero details; no memos. Whoever wants to pass on
  pseudonymised data only passes on a text format and checks memos and
  header.

## For the methods section

> The recordings were transcribed locally with ResearchTranscript 0.6.0
> (B/IAS Basel, AGPL-3.0-or-later; speech recognition whisper.cpp with
> the model large-v3-turbo, speaker diarisation SpeakerKit with pyannote
> models) on a computer of the research group; the app transmits no data
> in the process. The raw transcripts were then checked against the
> recording, corrected and pseudonymised in the text.

---

Source: <https://github.com/bias-city/ResearchTranscript> (folder
`site/docs`). The sheet is licensed CC BY 4.0: use and adapt it
freely, commercially too, as long as B/IAS is credited and changes are
marked.
