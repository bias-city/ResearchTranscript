"""Transkriptions-Jobs: in-memory (bewusst flüchtig — das ERGEBNIS
landet sofort als Bibliotheks-Eintrag, v1 verlor bei jedem Neustart
alle Jobs UND ihre Bearbeitbarkeit).

Pipeline je Job (eigener Thread):
  1. ffmpeg → 16 kHz mono WAV (IMMER — v1 ließ .wav-Uploads unkonvertiert
     zu whisper.cpp durch, ein gemessener v1-Bug)
  2. optional Diarisierung (SpeakerKit: pyannote community-1, Core ML)
  3. whisper.cpp: je Sprecher-Block ein Clip (diarisiert) oder die
     ganze Datei mit Live-Text-Streaming (klassisch)
  4. Bibliotheks-Eintrag anlegen (Sprecher als Entitäten)

Abbruch KOOPERATIV UND HART: cancel-Event wird zwischen den Schritten
geprüft, ein laufender whisper-/ffmpeg-Prozess wird gekillt (v1s
DELETE ließ whisper einfach weiterrechnen).
"""
from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from . import bibliothek, config
from .config import read_config
from .motor import MotorAbbruch, MotorFehler, motor

JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()

#: Beendete Jobs bleiben so lange sichtbar (Plan 1.19 — der Dauerlauf
#: zeigte +4 Einträge je Runde ohne Aufräumen); die Bibliothek hat das
#: Ergebnis längst.
AUFRAEUMEN_NACH_S = 24 * 3600
ENDZUSTAENDE = ("completed", "failed", "cancelled")

# ---------- Beobachter (Plan 1.5) ----------
# Die Hülle will Job-Änderungen als Ereignis statt per Polling. Ein
# Beobachter bekommt die `sicht()` eines Jobs — gedrosselt auf 10 Hz je
# Job, denn `partial_text` (bis 4000 Zeichen je whisper-Zeile) würde
# den IPC fluten; Statuswechsel gehen immer sofort durch.
_BEOBACHTER: Callable[[dict], None] | None = None
_ZULETZT: dict[str, float] = {}
DROSSEL_S = 0.1


def setze_beobachter(cb: Callable[[dict], None] | None) -> None:
    global _BEOBACHTER
    _BEOBACHTER = cb
    _ZULETZT.clear()


def _melde(job: dict, sofort: bool) -> None:
    cb = _BEOBACHTER
    if cb is None:
        return
    jetzt = time.monotonic()
    if not sofort and jetzt - _ZULETZT.get(job["id"], 0.0) < DROSSEL_S:
        return
    _ZULETZT[job["id"]] = jetzt
    try:
        cb(sicht(job))
    except Exception:  # noqa: BLE001 — ein kaputter Beobachter darf
        pass           # nie den Job umbringen


class Abbruch(Exception):
    pass


def _neu(filename: str, params: dict) -> dict:
    job = {"id": uuid.uuid4().hex[:8], "filename": filename,
           "params": params, "status": "pending", "progress": 0,
           "message": "", "partial_text": "", "error": None,
           "eintrag": None,
           "created_at": datetime.now(UTC).isoformat(
               timespec="seconds"),
           # gesetzt, wenn die Arbeit WIRKLICH beginnt — bei mehreren
           # gedroppten Dateien liegt created_at weit davor, und die
           # Anzeige „vergangen" wäre gelogen (User 2026-09-09)
           "started_at": None}
    with _LOCK:
        JOBS[job["id"]] = job
    _melde(job, sofort=True)
    return job


def _setze(job: dict, **kv) -> None:
    job.update(kv)
    _melde(job, sofort="status" in kv or "eintrag" in kv
           or "error" in kv)


def aufraeumen(jetzt: float | None = None) -> int:
    """Beendete Jobs älter als AUFRAEUMEN_NACH_S vergessen. Liefert die
    Zahl der entfernten Einträge."""
    from datetime import datetime as _dt
    jetzt = time.time() if jetzt is None else jetzt
    weg = []
    with _LOCK:
        for jid, j in JOBS.items():
            if j["status"] not in ENDZUSTAENDE:
                continue
            try:
                alter = jetzt - _dt.fromisoformat(j["created_at"]).timestamp()
            except (KeyError, ValueError):
                alter = 0
            if alter > AUFRAEUMEN_NACH_S:
                weg.append(jid)
        for jid in weg:
            JOBS.pop(jid, None)
            _ZULETZT.pop(jid, None)
    return len(weg)


def _lauf_fakten(p: dict) -> dict:
    from .config import APP_VERSION, get_available_models, get_vad_model
    from .motor import motor
    quelle = next((m["quelle"] for m in get_available_models() if m["name"] == p["model"]), None)
    return {"app": APP_VERSION, "modell_quelle": quelle,
            "vad": get_vad_model() is not None, "motor": motor().name,
            "trennung": p.get("cluster_threshold") if p.get("diarize") else None}


def alle_abbrechen(frist_s: float = 3.0) -> None:
    """Beim Beenden der Hülle: jedes Abbruch-Ereignis setzen, laufende
    Kinder töten, kurz auf die Threads warten. Die Threads sind
    daemon — ein hängendes Kind blockiert das Ende nicht."""
    for jid in list(_CANCEL):
        abbrechen(jid)
    frist = time.monotonic() + frist_s
    for t in threading.enumerate():
        if t.name.startswith("lt-job-") and t.is_alive():
            t.join(max(0.0, frist - time.monotonic()))


_CANCEL: dict[str, threading.Event] = {}

# ---------- Warteschlange ----------
# Vorher startete jeder Job sofort seinen Thread — vier gedroppte
# Dateien rechneten gleichzeitig um dieselbe GPU. Jetzt wartet der
# Thread ganz am Anfang auf einen Platz; der Job bleibt so lange
# „pending" mit started_at=None, und die Oberfläche zeigt „wartet …".
# Streng der Reihe nach (FIFO), damit die zuerst gedroppte Datei auch
# zuerst drankommt.
_SLOT = threading.Condition()
_LAUFEND: set[str] = set()
_WARTEND: list[str] = []


def _nimm_slot(job: dict) -> None:
    jid = job["id"]
    with _SLOT:
        _WARTEND.append(jid)
        while True:
            if _CANCEL.get(jid, threading.Event()).is_set():
                _WARTEND.remove(jid)
                raise Abbruch
            if _WARTEND[0] == jid and len(_LAUFEND) < config.max_parallel():
                _WARTEND.pop(0)
                _LAUFEND.add(jid)
                return
            _SLOT.wait(0.5)


def _gib_slot(job: dict) -> None:
    with _SLOT:
        _LAUFEND.discard(job["id"])
        if job["id"] in _WARTEND:
            _WARTEND.remove(job["id"])
        _SLOT.notify_all()


def _pruefe_abbruch(job: dict) -> None:
    ev = _CANCEL.get(job["id"])
    if ev is not None and ev.is_set():
        raise Abbruch()


def abbrechen(job_id: str) -> bool:
    """Das Ereignis setzen — die Motoren töten daraufhin ihre Kinder
    bzw. brechen im Prozess ab (motor.py); der Job-Thread sieht es
    zwischen den Schritten über _pruefe_abbruch."""
    ev = _CANCEL.get(job_id)
    if ev is None:
        return False
    ev.set()
    return True


def schleifen_zusammenziehen(segmente: list[dict],
                             mindestens: int = 3) -> list[dict]:
    """Whisper-Schleifen entschärfen: läuft derselbe Wortlaut drei- oder
    mehrmals direkt hintereinander, bleibt EIN Segment über die ganze
    Spanne. Zwei gleiche Zeilen nacheinander sind noch Sprache («Ja.
    Ja.»), ab drei ist es die bekannte Halluzination — mit VAD selten,
    aber nicht unmöglich."""
    aus: list[dict] = []
    i = 0
    while i < len(segmente):
        j = i
        while j + 1 < len(segmente) and \
                segmente[j + 1].get("text", "").strip() == segmente[i].get("text", "").strip() \
                and segmente[i].get("text", "").strip():
            j += 1
        if j - i + 1 >= mindestens:
            aus.append({**segmente[i], "end": segmente[j]["end"]})
        else:
            aus.extend(segmente[i:j + 1])
        i = j + 1
    return aus


def merge_consecutive_speakers(diarization: list,
                               min_segment_duration: float = 0.5) -> list:
    """v1-Logik unverändert: Mikro-Segmente (<0.5 s) dem Vorgänger
    zuschlagen, dann gleiche aufeinanderfolgende Sprecher verschmelzen."""
    if not diarization:
        return []
    from .diarize import SpeakerSegment

    filtered: list = []
    for seg in sorted(diarization, key=lambda x: x.start):
        if seg.end - seg.start < min_segment_duration:
            if filtered:
                filtered[-1] = SpeakerSegment(
                    start=filtered[-1].start, end=seg.end,
                    speaker=filtered[-1].speaker)
            continue
        filtered.append(seg)
    merged: list = []
    for seg in filtered:
        if merged and merged[-1].speaker == seg.speaker:
            merged[-1] = SpeakerSegment(start=merged[-1].start,
                                        end=seg.end, speaker=seg.speaker)
        else:
            merged.append(seg)
    return merged


def _konvertiere(job: dict, quelle: Path, arbeits_dir: Path) -> Path:
    """IMMER nach 16 kHz mono WAV (auch .wav-Quellen — Resample-Fix)."""
    ziel = arbeits_dir / f"{job['id']}.wav"
    _nimm_slot(job)
    _setze(job, started_at=datetime.now(UTC).isoformat(
        timespec="seconds"), progress=5, message="konvertiere")
    motor().wav16k(quelle, ziel, abbruch=_CANCEL.get(job["id"]))
    _pruefe_abbruch(job)
    return ziel


def _clip(job: dict, wav: Path, start: float, end: float,
          i: int) -> Path:
    ziel = wav.parent / f"{job['id']}_seg{i}.wav"
    motor().wav16k(wav, ziel, start=start, dauer=max(end - start, 0.05),
                   abbruch=_CANCEL.get(job["id"]))
    _pruefe_abbruch(job)
    return ziel


def _sprecher_label(n: int) -> str:
    basis = {"de": "Sprecher", "en": "Speaker", "fr": "Locuteur",
             "it": "Parlante"}.get(
        read_config().get("ui_language", "de"), "Speaker")
    return f"{basis} {n}"


def _lauf(job: dict, quelle: Path, name: str) -> None:
    import shutil
    import tempfile

    p = job["params"]
    tmp = Path(tempfile.mkdtemp(prefix="lt-job-"))
    try:
        # Video? Dann ist die Bibliotheks-Tonspur ein mp3, das Video
        # liegt unverändert daneben (BACKLOG 8). Geprüft wurde schon im
        # Endpunkt — hier nur noch der Ton.
        from . import video as _video
        ist_video = _video.pruefe(quelle) is not None
        wav = _konvertiere(job, quelle, tmp)
        audio_fuer_bibliothek = quelle
        if quelle.suffix.lower() in bibliothek.VIDEO_ENDUNGEN:
            # Aus einem Video-Container (auch ohne Bild) kommt die
            # Bibliotheks-Tonspur als mp3 — als Job-Prozess, damit
            # «Abbrechen» auch hier greift (Review 2026-09-11)
            _setze(job, message="tonspur")
            mp3 = tmp / "audio.mp3"
            motor().nach_mp3(quelle, mp3, abbruch=_CANCEL.get(job["id"]))
            _pruefe_abbruch(job)
            audio_fuer_bibliothek = mp3
        segmente: list[dict] = []
        sprecher: list[dict] = []

        if p["diarize"]:
            _setze(job, status="diarizing", progress=10,
                   message="sprecher")
            from .diarize import DiarisierungAbgebrochen, diarize_audio
            # 10 → 25 % füllen, sonst steht der Balken die ganze
            # Diarisierung still; nebenbei greift der Abbruch dann
            # SOFORT und nicht erst nach dem ganzen Lauf.
            def _diar_fortschritt(anteil: float) -> None:
                _setze(job, progress=10 + int(max(0.0, min(1.0, anteil)) * 15))

            try:
                diar = diarize_audio(str(wav), p["min_speakers"],
                                     p["max_speakers"],
                                     p["cluster_threshold"],
                                     fortschritt=_diar_fortschritt,
                                     abbruch=_CANCEL.get(job["id"]))
            except DiarisierungAbgebrochen as e:
                # Der Prozess wurde getötet: erst prüfen, ob WIR das
                # waren (dann fliegt Abbruch), sonst als Fehler melden.
                _pruefe_abbruch(job)
                raise RuntimeError("Sprechertrennung abgebrochen") from e
            _pruefe_abbruch(job)
            bloecke = merge_consecutive_speakers(diar)
            labels: dict[str, str] = {}   # Rohlabel (A, B …) → Entitäts-ID
            # Reihenfolge nach Gesamt-Sprechzeit (dominanter zuerst)
            zeit: dict[str, float] = {}
            for b in bloecke:
                zeit[b.speaker] = zeit.get(b.speaker, 0.0) \
                    + (b.end - b.start)
            for n, roh in enumerate(sorted(zeit, key=zeit.get,
                                           reverse=True), 1):
                sid = f"sp{n}"
                labels[roh] = sid
                sprecher.append({"id": sid,
                                 "name": _sprecher_label(n)})
            _setze(job, status="transcribing",
                   message=f"transkribiere:0/{len(bloecke)}")
            texte: list[str] = []
            for i, b in enumerate(bloecke):
                _pruefe_abbruch(job)
                _setze(job, progress=25 + int(i / max(len(bloecke), 1)
                                              * 60),
                       message=f"transkribiere:{i + 1}/{len(bloecke)}")
                clip = _clip(job, wav, b.start, b.end, i)
                try:
                    teile = motor().transkribiere_clip(
                        clip, p["model"], p["language"], b.start,
                        abbruch=_CANCEL.get(job["id"]))
                finally:
                    clip.unlink(missing_ok=True)
                _pruefe_abbruch(job)
                for t in teile:
                    segmente.append({"start": round(t.start, 3),
                                     "end": round(t.end, 3),
                                     "sprecher": labels[b.speaker],
                                     "text": t.text})
                    texte.append(t.text)
                _setze(job, partial_text=" ".join(texte[-80:]))
        else:
            _setze(job, status="transcribing", progress=15,
                   message="transkribiere")

            def cb(pct: int, _msg: str, text: str) -> None:
                _pruefe_abbruch(job)
                if pct >= 0:
                    _setze(job, progress=15 + int(pct * 0.7))
                _setze(job, partial_text=text[-4000:])

            teile = motor().transkribiere(wav, p["model"], p["language"],
                                          abbruch=_CANCEL.get(job["id"]),
                                          fortschritt=cb)
            _pruefe_abbruch(job)
            segmente = [{"start": round(t.start, 3),
                         "end": round(t.end, 3), "sprecher": None,
                         "text": t.text} for t in teile]

        segmente = schleifen_zusammenziehen(segmente)
        _setze(job, status="saving", progress=90, message="speichere")
        eintrag = bibliothek.anlegen(
            name=name, segmente=segmente, sprecher=sprecher,
            quelle={"datei": job["filename"], "model": p["model"],
                    "language": p["language"], "diarize": p["diarize"],
                    "sprecherzahl": p.get("speaker_range", "auto"),
                    "erzeugt": "transcription",
                    # fürs Transkriptionsprotokoll (dokumente.py): was zum
                    # Zeitpunkt des Laufs galt, nicht was heute eingestellt ist
                    **_lauf_fakten(p)},
            audio=audio_fuer_bibliothek, video=quelle if ist_video else None,
            origin="machine",
            by={"tool": "whisper.cpp", "model": p["model"],
                **({"diarization": "pyannote-community-1 (speakerkit)",
                    "speakers": p.get("speaker_range", "auto")}
                   if p["diarize"] else {})})
        _setze(job, status="completed", progress=100, message="fertig",
               eintrag=eintrag["id"])
    except (Abbruch, MotorAbbruch):
        _setze(job, status="cancelled", message="abgebrochen")
    except MotorFehler as e:
        _setze(job, status="failed", error=str(e), message="fehler")
    except Exception as e:  # noqa: BLE001 — Job-Fehler gehören in den
        # Job-Status, nie als toter Thread verschluckt
        _setze(job, status="failed", error=str(e), message="fehler")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        quelle_tmp = job.get("_quelle_tmp")
        if quelle_tmp:
            Path(quelle_tmp).unlink(missing_ok=True)
        _gib_slot(job)
        _CANCEL.pop(job["id"], None)


def starte(quelle: Path, filename: str, params: dict,
           quelle_ist_temp: bool = False) -> dict:
    aufraeumen()
    job = _neu(filename, params)
    if quelle_ist_temp:
        job["_quelle_tmp"] = str(quelle)
    _CANCEL[job["id"]] = threading.Event()
    t = threading.Thread(target=_lauf, name=f"lt-job-{job['id']}",
                         args=(job, quelle, Path(filename).stem),
                         daemon=True)
    t.start()
    return job


def sicht(job: dict) -> dict:
    return {k: v for k, v in job.items() if not k.startswith("_")}
