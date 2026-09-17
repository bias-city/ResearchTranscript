"""Motor-Protokoll (Plan 1.4): Wahl per LT_MOTOR, Prozess-Motor gegen ein
Fake-Modul, Abbruch tötet Kinder, Fehlerformen."""
from __future__ import annotations

import sys
import threading
import time
import types
from pathlib import Path

import pytest

from researchtranscript import motor as m
from researchtranscript.diarize import SpeakerSegment


def test_standard_ist_kind(monkeypatch):
    assert m.motor().name == "kind"


def test_prozess_ohne_modul_scheitert_laut(monkeypatch):
    monkeypatch.setenv("LT_MOTOR", "prozess")
    monkeypatch.setattr(m, "_modul", lambda: None)
    m.setze_motor(None)
    with pytest.raises(m.MotorFehler):
        m.motor()


def _fake_modul(aufrufe: list):
    mod = types.SimpleNamespace()

    def sondiere(pfad):
        aufrufe.append(("sondiere", pfad))
        return {"video_codec": "avc1", "audio_codec": "aac", "breite": 1920,
                "hoehe": 1080, "dauer_s": 12.5, "bitrate": 100, "playable": True}

    def wav16k(quelle, ziel, start, dauer, abbruch=None, fortschritt=None):
        aufrufe.append(("wav16k", quelle, ziel, start, dauer))
        if abbruch is not None and abbruch():
            return {"error": "abgebrochen"}
        if fortschritt:
            fortschritt(0.5); fortschritt(1.0)
        Path(ziel).write_bytes(b"RIFFfake")
        return {"samples": 160000, "dauer_s": 10.0}

    def nach_mp3(quelle, ziel, q, abbruch=None, fortschritt=None):
        aufrufe.append(("mp3", quelle, ziel, q))
        Path(ziel).write_bytes(b"ID3fake")
        return {"bytes": 7}

    def trenne(wav, n, schwelle, exklusiv, modelle, abbruch=None, fortschritt=None):
        aufrufe.append(("trenne", wav, n, schwelle, exklusiv))
        return {"segments": [{"start": 5.0, "end": 9.0, "speaker": "B"},
                             {"start": 0.0, "end": 6.0, "speaker": "A"}],
                "speaker_count": 2}

    mod.sondiere, mod.wav16k, mod.nach_mp3, mod.trenne = sondiere, wav16k, nach_mp3, trenne
    return mod


def test_prozess_motor_bildet_auf_das_modul_ab(tmp_path, monkeypatch):
    aufrufe: list = []
    monkeypatch.setenv("LT_MOTOR", "prozess")
    monkeypatch.setattr(m, "_modul", lambda: _fake_modul(aufrufe))
    monkeypatch.setenv("LT_SPEAKERKIT_DIR", str(tmp_path / "sk"))
    m.setze_motor(None)
    mo = m.motor()
    assert mo.name == "prozess"
    info = mo.sondiere(tmp_path / "v.mp4")
    assert info == {"video_codec": "avc1", "audio_codec": "aac",
                    "breite": 1920, "hoehe": 1080, "dauer_s": 12.5}
    fort: list[float] = []
    ziel = mo.wav16k(tmp_path / "a.mp3", tmp_path / "a.wav", start=1.0,
                     dauer=2.0, fortschritt=fort.append)
    assert ziel.is_file() and fort == [0.5, 1.0]
    assert aufrufe[-1][3:] == (1.0, 2.0)
    mo.nach_mp3(tmp_path / "v.mp4", tmp_path / "audio.mp3")
    assert aufrufe[-1][3] == 2                       # VBR q2
    seg = mo.trenne(tmp_path / "a.wav", 2, 2, 0.5)
    # exakt 2 Sprecher, Schwelle wie die CLI, exklusiv, überlappungsfrei
    assert aufrufe[-1][2:] == (2, 0.617, True)   # _schwelle(0.5)
    assert seg == [SpeakerSegment(0.0, 6.0, "A"), SpeakerSegment(6.0, 9.0, "B")]
    # Abbruch aus dem Modul → MotorAbbruch
    ev = threading.Event(); ev.set()
    with pytest.raises(m.MotorAbbruch):
        mo.wav16k(tmp_path / "a.mp3", tmp_path / "b.wav", abbruch=ev)


def test_kind_abbruch_toetet_das_kind():
    ev = threading.Event()
    threading.Timer(0.2, ev.set).start()
    t0 = time.monotonic()
    with pytest.raises(m.MotorAbbruch):
        m._kind_laufen([sys.executable, "-c", "import time; time.sleep(30)"], ev)
    assert time.monotonic() - t0 < 5


def test_kind_fehler_ohne_werkzeug(tmp_path, monkeypatch):
    monkeypatch.setenv("LT_BUNDLED", "1")
    monkeypatch.setenv("LT_APP_ROOT", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        m.KindMotor().wav16k(tmp_path / "x.mp3", tmp_path / "x.wav")
