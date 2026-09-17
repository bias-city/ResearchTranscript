"""Wellenform: Pyramide aus einem WAV, Ausschnitt-Wahl der Stufe, Cache
neben dem Audio, Befehl über die Fassade (Motor gefakt)."""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

from researchtranscript import wellenform as w


def _wav(pfad: Path, sekunden: float = 3.0, rate: int = 16000) -> None:
    n = int(sekunden * rate)
    with wave.open(str(pfad), "wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
        # Sekunde 1 laut, sonst leise
        f.writeframes(b"".join(
            struct.pack("<h", int((30000 if rate <= i < 2 * rate else 2000)
                                  * math.sin(i * 0.3))) for i in range(n)))


def test_pyramide_und_ausschnitt(tmp_path):
    wav = tmp_path / "a.wav"; _wav(wav)
    dauer, stufen = w.pyramide(wav)
    assert abs(dauer - 3.0) < 1e-6
    assert len(stufen) == w.STUFEN and len(stufen[0]) == 300      # 10 ms
    assert len(stufen[1]) == 30 and len(stufen[2]) == 3
    # Gesamtansicht in 3 Buckets: Mitte laut
    a = w.ausschnitt(dauer, stufen, 0, 3, 3)
    assert a[1] > 200 and a[0] < 40 and a[2] < 40
    # feiner Blick auf 0,1 s → Basisstufe, 10 Werte
    assert len(w.ausschnitt(dauer, stufen, 1.0, 1.1, 10)) == 10
    assert w.ausschnitt(dauer, stufen, 2, 1, 5) == [0] * 5


def test_befehl_baut_und_cacht(client, eintrag, tmp_path, monkeypatch):
    from researchtranscript import api, bibliothek, motor
    audio = bibliothek.eintrag_pfad(eintrag) / "audio.wav"
    _wav(audio)
    d = bibliothek.lese(eintrag); d["audio"] = "audio.wav"; bibliothek.schreibe(eintrag, d)
    aufrufe = []
    def fake_wav16k(self, quelle, ziel, **k):
        aufrufe.append(quelle); Path(ziel).write_bytes(Path(quelle).read_bytes()); return ziel
    monkeypatch.setattr(motor.KindMotor, "wav16k", fake_wav16k)
    r = api.wellenform(eintrag, 0, 3, 3)
    assert r["dauer_s"] == 3.0 and len(r["peaks"]) == 3 and r["peaks"][1] > 200
    assert (bibliothek.eintrag_pfad(eintrag) / w.DATEI).is_file()
    w._CACHE.clear()
    r2 = api.wellenform(eintrag, 0, 0, 1)          # nur Dauer, aus der Cache-Datei
    assert r2["peaks"] == [] and r2["dauer_s"] == 3.0 and len(aufrufe) == 1
    assert client.get(f"/api/transcripts/{eintrag}/wellenform?t0=0&t1=3&buckets=3").status_code == 200
