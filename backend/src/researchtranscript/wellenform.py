"""Wellenform fürs Editor-Panel (User 2026-09-17): Peaks-Pyramide je
Eintrag, einmal gebaut, als `wellenform.json` neben dem Audio gecacht.

Muster aus PrepareMedia (sync.rs `peak_pyramid`/`peaks`): Basisstufe
= max|Amplitude| je 10 ms als Byte 0–255, darüber Stufen zu je 100 ms,
1 s, 10 s (Maximum von zehn Bins). Ein Ausschnitt wählt die gröbste
Stufe, die noch ≥ 10 Bins je Bucket liefert — so kostet ein 3,4-h-Blick
so wenig wie ein 3-s-Blick. Zoombar, ohne die ganze Datei im Browser zu
dekodieren.

Quelle ist das 16-kHz-mono-WAV des Motors (dieselbe Dekodierung wie
für Whisper); die Datei lebt nur während des Aufbaus.
"""
from __future__ import annotations

import base64
import json
import tempfile
import threading
import wave
from array import array
from pathlib import Path

from . import bibliothek
from .bibliothek import BibliothekFehler

VERSION = 1
BIN_MS = 10
STUFEN = 4          # 10 ms · 100 ms · 1 s · 10 s
DATEI = "wellenform.json"

_CACHE: dict[str, dict] = {}
_LOCK = threading.Lock()


def pyramide(wav: Path) -> tuple[float, list[bytes]]:
    """(Dauer in s, Stufen) aus einem 16-kHz-mono-s16-WAV."""
    with wave.open(str(wav), "rb") as w:
        rate, kanaele, breite, n = (w.getframerate(), w.getnchannels(),
                                    w.getsampwidth(), w.getnframes())
        if breite != 2:
            raise ValueError(f"WAV mit {breite * 8} Bit — erwartet 16")
        roh = w.readframes(n)
    a = array("h")
    a.frombytes(roh)
    if kanaele > 1:                      # Motor liefert mono; zur Sicherheit
        a = a[::kanaele]
    je_bin = max(1, rate * BIN_MS // 1000)
    basis = bytearray()
    # max/min je Bin laufen in C (array-Slices) — 3,4 h in wenigen Sekunden
    for i in range(0, len(a), je_bin):
        s = a[i:i + je_bin]
        amp = max(max(s), -min(s)) if len(s) else 0
        basis.append(min(255, amp * 255 // 32768))
    stufen = [bytes(basis)]
    for _ in range(STUFEN - 1):
        vorher = stufen[-1]
        stufen.append(bytes(max(vorher[i:i + 10]) if vorher[i:i + 10] else 0
                            for i in range(0, len(vorher), 10)))
    return len(a) / rate, stufen


def ausschnitt(dauer: float, stufen: list[bytes], t0: float, t1: float,
               buckets: int) -> list[int]:
    """Ein Wert je Bucket zwischen t0 und t1 — Port von PrepareMedias
    `peaks()`: die gröbste Stufe, die noch ≥ 10 Bins je Bucket hat."""
    buckets = max(1, min(20_000, int(buckets)))
    if not stufen or not stufen[0] or t1 <= t0:
        return [0] * buckets
    je_bucket_ms = (t1 - t0) * 1000.0 / buckets
    stufe, bin_ms = 0, float(BIN_MS)
    while stufe + 1 < len(stufen) and bin_ms * 10.0 <= je_bucket_ms:
        stufe += 1
        bin_ms *= 10.0
    daten = stufen[stufe]
    aus = []
    for i in range(buckets):
        a = max(0, int((t0 * 1000.0 + i * je_bucket_ms) // bin_ms))
        b = min(len(daten), int(-(-(t0 * 1000.0 + (i + 1) * je_bucket_ms) // bin_ms)))
        aus.append(max(daten[a:b]) if a < b else 0)
    return aus


def _lade(pfad: Path) -> dict | None:
    try:
        d = json.loads(pfad.read_text("utf-8"))
        if d.get("version") != VERSION or d.get("bin_ms") != BIN_MS:
            return None
        return {"dauer": float(d["dauer_s"]),
                "stufen": [base64.b64decode(s) for s in d["stufen"]]}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _baue(eid: str, audio: Path) -> dict:
    from .motor import motor
    with tempfile.TemporaryDirectory(prefix="lt-welle-") as td:
        wav = Path(td) / "welle.wav"
        motor().wav16k(audio, wav)
        dauer, stufen = pyramide(wav)
    ziel = bibliothek.eintrag_pfad(eid) / DATEI
    tmp = ziel.with_suffix(".tmp")
    tmp.write_text(json.dumps({
        "version": VERSION, "bin_ms": BIN_MS, "dauer_s": round(dauer, 3),
        "stufen": [base64.b64encode(s).decode("ascii") for s in stufen]}),
        "utf-8")
    tmp.replace(ziel)
    return {"dauer": dauer, "stufen": stufen}


def fuer(eid: str) -> dict:
    """Pyramide des Eintrags — aus dem Speicher, der Cache-Datei oder
    frisch gebaut (einmal je Eintrag; 3,4 h ≈ 10 s)."""
    with _LOCK:
        if eid in _CACHE:
            return _CACHE[eid]
    audio = bibliothek.audio_pfad(eid)
    if audio is None:
        raise BibliothekFehler("Kein Audio")
    cache = bibliothek.eintrag_pfad(eid) / DATEI
    d = _lade(cache) if cache.is_file() else None
    if d is None:
        d = _baue(eid, audio)
    with _LOCK:
        _CACHE[eid] = d
    return d
