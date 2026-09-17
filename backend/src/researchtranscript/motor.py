"""Motor-Protokoll (Plan §4 1.4 / §5): EINE Schnittstelle für Ton,
Sprechertrennung und Whisper — mit zwei Umsetzungen.

- `KindMotor`: die heutigen Kindprozesse (ffmpeg, argmax-cli,
  whisper-cli). Byte-identisch zu 0.5.0; Standard, bis die Parität des
  Prozess-Motors belegt ist (Plan E3).
- `ProzessMotor`: Ton über AVFoundation + libmp3lame und Sprechertrennung
  über den SpeakerKit-Shim IM PROZESS der Hülle — das Rust-Modul
  `researchtranscript_motoren` (PyO3, nur in der App vorhanden). Whisper
  bleibt auch hier ein Kind (User-Entscheid 17.9.2026: Absturz- und
  Speicherisolation).

Wahl: `LT_MOTOR=kind|prozess`; ohne Vorgabe `kind`. Die Aufrufstellen
(jobs, video, diarize, api, exporte) kennen nur `motor()` — kein
`subprocess`, kein `get_ffmpeg_cli` mehr ausserhalb dieser Datei und
der beiden Kind-Module (transcribe.py, diarize.py behalten ihre
whisper-/argmax-Aufrufe, der KindMotor ruft sie).

Abbruch: kooperativ über ein `threading.Event` (`abbruch`), das die
Motoren zwischen den Blöcken prüfen; Kindprozesse werden beim Setzen
gekillt (Wächter-Thread), der Prozess-Motor fragt das Ereignis in
seinem Callback ab. Fortschritt: `fortschritt(anteil)` mit 0..1.
"""
from __future__ import annotations

import os
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from .config import get_ffmpeg_cli

Fortschritt = Callable[[float], None] | None
Abbruch = threading.Event | None


class MotorAbbruch(Exception):
    """Der Lauf wurde über das Abbruch-Ereignis beendet — kein Fehler."""


class MotorFehler(RuntimeError):
    """Der Motor hat versagt (Datei unlesbar, Werkzeug fehlt …)."""


# ---------- Kindprozesse ----------

def _kind_laufen(cmd: list[str], abbruch: Abbruch, *,
                 log: Path | None = None) -> int:
    """Kind starten, auf Ende warten; wird `abbruch` gesetzt, das Kind
    töten und MotorAbbruch werfen. Rückgabe: Exit-Code."""
    aus = log.open("w") if log else subprocess.DEVNULL
    try:
        proc = subprocess.Popen(cmd, stdout=aus, stderr=subprocess.STDOUT
                                if log else subprocess.DEVNULL)
    finally:
        if log:
            aus.close()
    getoetet = False
    while proc.poll() is None:
        if abbruch is not None and abbruch.is_set():
            proc.kill()
            getoetet = True
            proc.wait()
            break
        try:
            proc.wait(timeout=0.1)
        except subprocess.TimeoutExpired:
            pass
    if getoetet:
        raise MotorAbbruch()
    return proc.returncode


class KindMotor:
    """Heutige Umsetzung: ffmpeg, argmax-cli, whisper-cli als Kinder."""

    name = "kind"

    def sondiere(self, pfad: Path) -> dict:
        from .video import sondiere_ffmpeg
        return sondiere_ffmpeg(pfad)

    def wav16k(self, quelle: Path, ziel: Path, *, start: float = 0.0,
               dauer: float = 0.0, abbruch: Abbruch = None,
               fortschritt: Fortschritt = None) -> Path:
        """IMMER nach 16 kHz mono s16 WAV (auch .wav-Quellen — Resample-
        Fix aus v1). `dauer > 0` schneidet einen Ausschnitt ab `start`."""
        cmd = [get_ffmpeg_cli(), "-y"]
        if dauer > 0:
            cmd += ["-ss", f"{start:.3f}", "-t", f"{dauer:.3f}"]
        cmd += ["-i", str(quelle), "-vn", "-ar", "16000", "-ac", "1",
                "-c:a", "pcm_s16le", str(ziel)]
        rc = _kind_laufen(cmd, abbruch)
        if rc != 0 or not ziel.is_file():
            raise MotorFehler("Audio-Konvertierung fehlgeschlagen (ffmpeg)")
        if fortschritt:
            fortschritt(1.0)
        return ziel

    def nach_mp3(self, quelle: Path, ziel: Path, *, abbruch: Abbruch = None,
                 fortschritt: Fortschritt = None) -> Path:
        """Tonspur als mp3 (VBR q2, wie der enrich-Export) — Arbeitskopie
        für Whisper, Editor und Dossier; ein Video bleibt unangetastet."""
        cmd = [get_ffmpeg_cli(), "-y", "-i", str(quelle), "-vn",
               "-c:a", "libmp3lame", "-q:a", "2", str(ziel)]
        rc = _kind_laufen(cmd, abbruch)
        if rc != 0 or not ziel.is_file():
            raise MotorFehler("Tonspur konnte nicht gelesen werden (ffmpeg)")
        if fortschritt:
            fortschritt(1.0)
        return ziel

    def trenne(self, wav: Path, min_sp: int, max_sp: int, threshold: float,
               *, abbruch: Abbruch = None, fortschritt: Fortschritt = None):
        from .diarize import trenne_cli
        return trenne_cli(wav, min_sp, max_sp, threshold, abbruch=abbruch,
                          fortschritt=fortschritt)

    def transkribiere_clip(self, wav: Path, model: str, language: str,
                           time_offset: float, *, abbruch: Abbruch = None):
        from .transcribe import transcribe_segment
        return transcribe_segment(wav, model, language, time_offset,
                                  register=_toeter(abbruch))

    def transkribiere(self, wav: Path, model: str, language: str, *,
                      abbruch: Abbruch = None,
                      fortschritt: Callable[[int, str, str], None] | None = None):
        from .transcribe import transcribe_classic
        return transcribe_classic(wav, model, language, progress_cb=fortschritt,
                                  register=_toeter(abbruch))


def _toeter(abbruch: Abbruch):
    """Für die whisper-Funktionen (Register-Muster): ein Wächter-Thread
    tötet das registrierte Kind, sobald das Ereignis gesetzt wird."""
    if abbruch is None:
        return None
    halter: dict[str, subprocess.Popen | None] = {"proc": None}

    def waechter() -> None:
        while True:
            p = halter["proc"]
            if p is None or p.poll() is not None:
                return
            if abbruch.wait(0.1):
                p = halter["proc"]
                if p is not None and p.poll() is None:
                    p.kill()
                return

    def register(proc: subprocess.Popen | None) -> None:
        halter["proc"] = proc
        if proc is not None:
            threading.Thread(target=waechter, daemon=True,
                             name="lt-toeter").start()
    return register


# ---------- Im Prozess (Rust-Modul der Hülle) ----------

class ProzessMotor(KindMotor):
    """Ton und Sprechertrennung über `researchtranscript_motoren`
    (AVFoundation + libmp3lame, SpeakerKit-Shim). Whisper wie KindMotor."""

    name = "prozess"

    def __init__(self, modul) -> None:
        self._m = modul

    @staticmethod
    def _cb(abbruch: Abbruch, fortschritt: Fortschritt) -> dict:
        return {"abbruch": (abbruch.is_set if abbruch is not None else None),
                "fortschritt": fortschritt}

    @staticmethod
    def _pruefe(aus: dict) -> dict:
        if aus.get("error") == "abgebrochen":
            raise MotorAbbruch()
        if aus.get("error"):
            raise MotorFehler(str(aus["error"]))
        return aus

    def sondiere(self, pfad: Path) -> dict:
        info = self._pruefe(self._m.sondiere(str(pfad)))
        return {"video_codec": info.get("video_codec"),
                "audio_codec": info.get("audio_codec"),
                "breite": info.get("breite"), "hoehe": info.get("hoehe"),
                "dauer_s": info.get("dauer_s")}

    def wav16k(self, quelle: Path, ziel: Path, *, start: float = 0.0,
               dauer: float = 0.0, abbruch: Abbruch = None,
               fortschritt: Fortschritt = None) -> Path:
        self._pruefe(self._m.wav16k(str(quelle), str(ziel), start, dauer,
                                    **self._cb(abbruch, fortschritt)))
        return ziel

    def nach_mp3(self, quelle: Path, ziel: Path, *, abbruch: Abbruch = None,
                 fortschritt: Fortschritt = None) -> Path:
        self._pruefe(self._m.nach_mp3(str(quelle), str(ziel), 2,
                                      **self._cb(abbruch, fortschritt)))
        return ziel

    def trenne(self, wav: Path, min_sp: int, max_sp: int, threshold: float,
               *, abbruch: Abbruch = None, fortschritt: Fortschritt = None):
        from .config import get_speakerkit_dir
        from .diarize import SpeakerSegment, _schwelle, ueberlappungsfrei
        n = min_sp if (min_sp > 0 and min_sp == max_sp) else 0
        aus = self._pruefe(self._m.trenne(
            str(wav), n, _schwelle(threshold), True, str(get_speakerkit_dir()),
            **self._cb(abbruch, fortschritt)))
        return ueberlappungsfrei([SpeakerSegment(s["start"], s["end"], s["speaker"])
                                  for s in aus.get("segments", [])])


# ---------- Wahl ----------

_MOTOR: KindMotor | None = None
_LOCK = threading.Lock()


def _modul():
    try:
        import researchtranscript_motoren
        return researchtranscript_motoren
    except ImportError:
        return None


def motor() -> KindMotor:
    """Der Motor dieser Sitzung. `LT_MOTOR=prozess` verlangt das
    Rust-Modul und scheitert laut, wenn es fehlt; `kind` erzwingt die
    Kinder; ohne Vorgabe: kind (Plan E3 — Standard bleibt, bis die
    Parität belegt ist)."""
    global _MOTOR
    with _LOCK:
        if _MOTOR is None:
            wahl = os.environ.get("LT_MOTOR", "kind").strip().lower()
            if wahl == "prozess":
                m = _modul()
                if m is None:
                    raise MotorFehler("LT_MOTOR=prozess, aber das Modul "
                                      "researchtranscript_motoren fehlt")
                _MOTOR = ProzessMotor(m)
            else:
                _MOTOR = KindMotor()
        return _MOTOR


def setze_motor(m: KindMotor | None) -> None:
    """Für Tests und die Hülle: Motor austauschen (None = neu wählen)."""
    global _MOTOR
    with _LOCK:
        _MOTOR = m
