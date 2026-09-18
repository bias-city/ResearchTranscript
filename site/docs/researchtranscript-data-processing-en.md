# ResearchTranscript — Description of the data processing

A text block to paste into a record of processing activities, a data
protection impact assessment, an ethics application or a data
management plan. As of 18 September 2026, ResearchTranscript 0.6.0. Items
in `[square brackets]` are completed by the controller.

The text describes what the software does and does not do. The legal
assessment of the controller's own processing — under the GDPR or the
revised Swiss FADP — is made by the controller; the text is no
substitute for legal advice.

This text is the general template. Since 0.6.0 the app itself generates
the version for an individual transcript (Editor › Export ›
“Documentation package (.zip) …”): a transcription record with the
model and version actually used and the measured degree of editing by
hand, a methods paragraph, facts for data protection, a data sheet for
the repository and a citation file.

---

## 1. Software used

ResearchTranscript, version `[0.6.0]`. Free software under
AGPL-3.0-or-later (with an additional permission for distribution
through the App Store), developed at B/IAS – Basel Institut für
angewandte Stadtforschung. Source code public at
<https://github.com/bias-city/ResearchTranscript>; the signed and
notarised installer (DMG) is on the releases page there. The software
runs as a local application on macOS (Apple Silicon) in the macOS App
Sandbox and is installed and operated by the controller itself.

## 2. Purpose of the processing

Conversion of audio recordings `[e.g. semi-structured interviews in the
project …]` into text with timecodes and speaker attribution, for
subsequent qualitative analysis `[in ATLAS.ti / MAXQDA / NVivo /
enrich / …]`.

## 3. Data subjects and categories of data

The data subjects are the recorded persons `[interviewees, participants
in group discussions, …]`. Processed are voice recordings (voice and
content of the conversation) and the transcripts generated from them,
with timecodes and speaker attribution. Depending on the content of the
conversation, special categories of personal data may be involved
`[yes / no: …]`.

## 4. Data flow of one transcription

1. **Input.** The audio or video file is read from the local file
   system of the device (audio: MP3, WAV, M4A, OGG, FLAC; video: MP4,
   MOV, M4V with H.264/HEVC — from video only the sound track is read,
   the video is never transcoded). Audio is read by macOS AVFoundation.
   The macOS App Sandbox allows access only to folders the person
   chooses in a dialog and to files dragged in.
2. **Processing.** The application logic runs embedded inside the app.
   Speech recognition (whisper.cpp 1.8.2, model large-v3-turbo) runs as
   a helper program from the app bundle on the graphics processor
   (Metal). Speaker diarisation (SpeakerKit by Argmax with the models
   pyannote segmentation-3.0, WeSpeaker ResNet34 and pyannote
   community-1, converted to Core ML by Argmax) runs in the app via
   Core ML and can be switched off. Voice activity detection (Silero
   VAD 5.1.2 inside whisper.cpp) is used only when speaker diarisation
   is switched off; otherwise the diarisation cuts the blocks. All
   models are contained in the application package; the application
   downloads neither models nor program components. A user can add
   whisper.cpp models only by hand, into the library's “Modelle”
   folder. The models do not learn from the recordings. The application
   summarises nothing and rephrases nothing; speech recognition is an
   AI model and can produce words that were not said, which is why the
   transcript must be checked against the recording.
3. **Storage.** For each transcript a subfolder is created in the
   chosen library folder `[path]` holding `transkript.json` (wording,
   speakers, memos, journal, Zotero details), a copy of the recording
   (for video the unchanged video file too) and `wellenform.json`.
   `ausgang.json` holds the state as delivered by the machine or by an
   imported file; `history/` holds the last 30 states. **Both contain
   the wording before any pseudonymisation.** Settings and the app log
   are stored in the app container of the user account. The journal
   records an installation ID and, optionally, an e-mail address of the
   editing person.
4. **Network.** The software transmits no recordings, texts or usage
   data: no account, no telemetry, no update check, no crash reports of
   its own, no model downloads. There is no internal service, no server
   and no open port. The macOS network entitlement is set only because
   the built-in web view requires it; a firewall or `nettop` shows that
   no connection is made. Crash reports of the macOS operating system
   are governed by its system settings, not by the software.
5. **Output.** Export files are written wherever the operator saves
   them. All text formats (VTT, CSV, TXT, Markdown, Word) contain
   wording, speaker names and timestamps; CSV, Markdown and Word
   additionally the memos; Markdown and Word, with a Zotero link, a
   header with title, date, citekey and the persons whose roles were
   selected. **REFI-QDA (`.qdpx.zip`) contains text, memos and the audio
   recording, i.e. the voice, and on request the video file; the enrich
   dossier (`.enrich`) contains text, the audio recording as MP3 (via
   LAME), the journal with installation ID and e-mail, and Zotero
   details, no memos.** Passing them on is passing on the recording.
   With Zotero consent the application reads the local `zotero.sqlite`
   read-only and only on request. For a video recording the video file
   is stored unchanged in the transcript's folder (faces are personal
   and, where identifiable, biometric data).

## 5. Location of the processing

Exclusively on the device `[device, location]` in the session of the
logged-in user. There is no server, no open port, no cloud service and
no user account.

## 6. Recipients, processors, transfers to third countries

None. Since no data is transmitted, there are neither recipients nor
processors nor a transfer to a third country. Data leaves the device
only if the controller itself passes on export files `[to …, by …]`.

## 7. Retention and deletion

Retention of recordings and transcripts: `[period, basis]`. Deleting in
the application moves an entry to a trash folder inside the library
(`_papierkorb`); it is removed for good only when that folder is emptied
in the Finder `[by whom, when]`. `ausgang.json` and the states in
`history/` live in the folder of the respective transcript and are
deleted with it. Backups of the device
`[Time Machine, …]` are subject to the controller's deletion rule.

## 8. Technical and organisational measures

To be provided by the controller, as the software itself brings no
access control:

- Disk encryption, e.g. FileVault: `[active since …]`
- Access protection of the device (login, screen lock): `[…]`
- Pseudonymisation before any transfer — in the application's editor,
  speakers can be renamed and names in the text swapped with find and
  replace; the decision of what to replace is made by the editing
  person: `[procedure, responsibility]`
- Backup rule: `[…]`
- Rule for passing on export files, in particular those containing
  audio: `[…]`

## 9. Legal basis and information of the data subjects

`[consent / legitimate interest / research privilege under …;
information letter of …]`. The software contributes nothing here.

## 10. Verifiability

The statements in section 4 can be checked against the source code: the
shell `frontend/src-tauri/src/lib.rs` starts no server and opens no
port; the sandbox entitlements are in
`frontend/src-tauri/entitlements.plist`. The repository contains the
complete build chain up to the signed installation package; anyone who
does not trust the distributed binary can build it.

---

Source of this text: <https://github.com/bias-city/ResearchTranscript>
(folder `site/docs`). It is licensed CC BY 4.0: use and adapt it
freely, commercially too, as long as B/IAS is credited and changes are
marked.
