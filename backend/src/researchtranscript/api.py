"""Funktions-Fassade über alle Befehle der App — transportfrei.

Zwei Aufrufer, dieselben Funktionen:
- `main.py` (FastAPI, Browser-Dev, Playwright, pytest): jede Route ist
  eine dünne Übersetzung Route → Funktion, `ApiFehler` → HTTPException.
- die Tauri-Hülle (PyO3, `src-tauri/src/python.rs`): `rufe_json(name,
  args)` — EIN Dispatcher, JSON rein, JSON raus, `ApiFehler` mit
  Statuscode als Python-Ausnahme.

Kein `fastapi`-Import hier (Plan §4 1.2): die Fassade muss im Bundle
ohne den Server laufen. Pydantic prüft die Argumente an derselben
Stelle wie früher der Router — die Fehlerform `{status, detail}` bleibt.

Statuscodes (sechs): 400 unbrauchbare Eingabe · 404 unbekannt · 409
Konflikt/abgelehnt · 422 Prüfung · 424 Voraussetzung (Zotero) · 500.
"""
from __future__ import annotations

import inspect
import json
import tempfile
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from . import bibliothek, config, exporte, jobs
from .bibliothek import BibliothekFehler

VIDEO_MEDIA = {".mp4": "video/mp4", ".m4v": "video/mp4",
               ".mov": "video/quicktime"}
AUDIO_MEDIA = {".mp3": "audio/mpeg", ".m4a": "audio/mp4",
               ".aac": "audio/aac", ".wav": "audio/wav",
               ".ogg": "audio/ogg", ".flac": "audio/flac",
               ".webm": "audio/webm"}


class ApiFehler(Exception):
    """Fehler mit HTTP-Statuscode — `main.py` macht daraus eine
    HTTPException, die Hülle ein `{status, detail}`."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def tmpdatei(suffix: str, prefix: str) -> Path:
    """mkstemp OHNE fd-Leck (Review-Befund: der fd wurde nie
    geschlossen — drei Aufrufstellen)."""
    import os
    fd, name = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return Path(name)


def _err(e: Exception) -> ApiFehler:
    if isinstance(e, BibliothekFehler):
        return ApiFehler(404, str(e))
    return ApiFehler(500, str(e))


# ---------- Dispatcher ----------

BEFEHLE: dict[str, Callable[..., object]] = {}


def befehl(fn: Callable[..., object]) -> Callable[..., object]:
    """Registriert eine Fassaden-Funktion unter ihrem Namen für
    `rufe_json`. Argumente kommen als Dict mit den Parameternamen."""
    BEFEHLE[fn.__name__] = fn
    return fn


def _pruefe(modell: type[ApiModel], daten: object) -> ApiModel:
    if not isinstance(daten, dict):
        raise ApiFehler(422, "Objekt erwartet")
    try:
        return modell.model_validate(daten)
    except ValidationError as e:
        raise ApiFehler(422, e.errors()[0].get("msg", "ungültig")) from e


def rufe(name: str, args: dict | None = None) -> object:
    """Befehl per Name mit Schlüsselwort-Argumenten. Unbekannter Name
    oder falsche Argumente → 404/422, nie ein TypeError nach draussen."""
    fn = BEFEHLE.get(name)
    if fn is None:
        raise ApiFehler(404, f"Unbekannter Befehl: {name}")
    args = args or {}
    if not isinstance(args, dict):
        raise ApiFehler(422, "Argumente müssen ein Objekt sein")
    sig = inspect.signature(fn)
    try:
        sig.bind(**args)
    except TypeError as e:
        raise ApiFehler(422, f"{name}: {e}") from e
    return fn(**args)


def rufe_json(name: str, args_json: str) -> str:
    """Für die Hülle: JSON-Text rein, JSON-Text raus. Ergebnis-Bytes
    (Hörprobe) kommen nicht hier durch, dafür gibt es eigene Befehle."""
    try:
        args = json.loads(args_json) if args_json else {}
    except ValueError as e:
        raise ApiFehler(422, f"Argumente kein JSON: {e}") from e
    return json.dumps(rufe(name, args), ensure_ascii=False)


# ---------- Health / Modelle / Einstellungen ----------

@befehl
def health() -> dict:
    return {"status": "ok", "app": config.APP_NAME,
            "version": config.APP_VERSION}


@befehl
def ping() -> dict:
    """Herzschlag der Hülle (Plan R4): muss ohne Bibliothek, ohne
    Config, ohne Sperre antworten."""
    return {"pong": True}


@befehl
def models() -> dict:
    """Mitgelieferte + eigene Modelle. Jeder Aufruf ist ein Scan (ein
    Glob) — ein in `<Bibliothek>/Modelle/` abgelegtes Modell erscheint
    beim nächsten Öffnen der Einstellungen. Der Ordner wird hier
    angelegt, damit er im Finder existiert."""
    eigene = config.get_eigene_modelle_dir()
    if eigene is not None:
        try:
            eigene.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    return {"models": config.get_available_models(),
            "models_dir": str(config.get_models_dir()),
            "eigene_dir": str(eigene) if eigene else None,
            "ungueltig": config.get_ungueltige_modelle()}


@befehl
def settings_get() -> dict:
    cfg = config.read_config()
    cfg["default_library_root"] = str(config.default_library_root())
    return cfg


class SettingsReq(ApiModel):
    model_config = ConfigDict(extra="allow")


@befehl
def settings_post(aend: dict) -> dict:
    aend = dict(_pruefe(SettingsReq, aend).model_dump())
    mail = aend.get("user_email")
    if mail is not None:
        mail = str(mail).strip()
        if mail and ("@" not in mail or " " in mail):
            raise ApiFehler(422, "Keine E-Mail-Adresse")
        aend["user_email"] = mail
    if aend.get("install_id") == "neu":          # Einstellungen: «Neu erzeugen»
        aend["install_id"] = config.neue_install_id()
    elif "install_id" in aend:
        aend.pop("install_id")                    # sonst nie von aussen setzbar
    root = aend.get("library_root")
    if root == "default":
        p = config.default_library_root()
        p.mkdir(parents=True, exist_ok=True)
        aend["library_root"] = str(p)
    elif root:
        p = Path(root).expanduser()
        if not p.is_dir():
            raise ApiFehler(409, f"Kein Ordner: {p}")
        aend["library_root"] = str(p)
    return config.write_config(aend)


# ---------- Transkription ----------

def params(model: str, language: str, speaker_range: str,
           cluster_threshold: float, diarize: bool) -> dict:
    min_sp = max_sp = 0
    if speaker_range and speaker_range != "auto" \
            and "-" in speaker_range:
        a, _, b = speaker_range.partition("-")
        try:
            min_sp, max_sp = int(a), int(b)
        except ValueError:
            min_sp = max_sp = 0
    return {"model": model, "language": language,
            "min_speakers": min_sp, "max_speakers": max_sp,
            "speaker_range": speaker_range or "auto",
            "cluster_threshold": cluster_threshold, "diarize": diarize}


def video_pruefen(p: Path, *, aufraeumen: bool = False) -> None:
    """Abweisen VOR dem Job (422 mit Hinweis), nie still im Thread."""
    from . import video
    try:
        video.pruefe(p)
    except video.VideoFehler as e:
        if aufraeumen:
            p.unlink(missing_ok=True)
        raise ApiFehler(422, str(e)) from e


def endung_erlaubt(endung: str) -> bool:
    return endung in bibliothek.AUDIO_ENDUNGEN + bibliothek.VIDEO_ENDUNGEN


class TranscribePathReq(ApiModel):
    path: str
    model: str = "large-v3-turbo"
    language: str = "de"
    speaker_range: str = "auto"
    cluster_threshold: float = 0.5
    diarize: bool = True


@befehl
def transcribe_path(args: dict) -> dict:
    """App-Weg (nativer Datei-Drop): Pfad statt Multipart — große
    Audios werden nie durch HTTP kopiert."""
    req = _pruefe(TranscribePathReq, args)
    p = Path(req.path).expanduser()
    if not p.is_file():
        raise ApiFehler(404, f"{p} fehlt")
    if not endung_erlaubt(p.suffix.lower()):
        raise ApiFehler(400, f"Nicht unterstützt: {p.suffix}")
    video_pruefen(p)
    job = jobs.starte(p, p.name,
                      params(req.model, req.language, req.speaker_range,
                             req.cluster_threshold, req.diarize))
    return {"job_id": job["id"]}


def transcribe_temp(tmp: Path, name: str, args: dict) -> dict:
    """Upload-Weg (nur Browser): die Datei liegt schon als Temp-Kopie."""
    if not endung_erlaubt(Path(name).suffix.lower()):
        tmp.unlink(missing_ok=True)
        raise ApiFehler(400, f"Nicht unterstützt: {Path(name).suffix.lower()}")
    video_pruefen(tmp, aufraeumen=True)
    job = jobs.starte(tmp, name, params(**args), quelle_ist_temp=True)
    return {"job_id": job["id"]}


# ---------- Warteliste (Plan R2 / 1.17) ----------
# Abgelegte Dateien warten in der Oberfläche mit ihrer Sprecherzahl, bis
# «Starten» gedrückt wird. Bis 0.4.0 lebte diese Liste nur im
# Frontend-State — ein Absturz oder ein versehentliches Beenden nahm sie
# mit. Jetzt spiegelt die Oberfläche sie hierher (Pfade, nie Dateiinhalte;
# Browser-Uploads haben keinen Pfad und bleiben flüchtig).

def _warteliste_datei() -> Path:
    return config._config_dir() / "warteliste.json"


class WartendReq(ApiModel):
    name: str
    pfad: str
    zahl: str = ""


@befehl
def warteliste_get() -> dict:
    try:
        roh = json.loads(_warteliste_datei().read_text("utf-8"))
    except (OSError, ValueError):
        return {"eintraege": []}
    aus = []
    for e in roh if isinstance(roh, list) else []:
        try:
            w = WartendReq.model_validate(e)
        except ValidationError:
            continue
        if Path(w.pfad).is_file():          # verschwundene Dateien fallen weg
            aus.append(w.model_dump())
    return {"eintraege": aus}


@befehl
def warteliste_set(eintraege: list) -> dict:
    if not isinstance(eintraege, list):
        raise ApiFehler(422, "Liste erwartet")
    daten = [_pruefe(WartendReq, e).model_dump() for e in eintraege]
    d = _warteliste_datei()
    d.parent.mkdir(parents=True, exist_ok=True)
    tmp = d.with_suffix(".tmp")
    tmp.write_text(json.dumps(daten, ensure_ascii=False, indent=1), "utf-8")
    tmp.replace(d)
    return {"eintraege": daten}


@befehl
def jobs_liste() -> dict:
    return {"jobs": [jobs.sicht(j) for j in list(jobs.JOBS.values())]}


@befehl
def job_get(job_id: str) -> dict:
    j = jobs.JOBS.get(job_id)
    if j is None:
        raise ApiFehler(404, "Job unbekannt")
    return jobs.sicht(j)


@befehl
def job_cancel(job_id: str) -> dict:
    if job_id not in jobs.JOBS:
        raise ApiFehler(404, "Job unbekannt")
    jobs.abbrechen(job_id)
    return {"status": "cancelling"}


# ---------- Import ----------

def import_turns(turns: list[dict], name: str, quelle_art: str,
                 audio: Path | None) -> dict:
    """`audio` darf auch ein Video sein: dann wird der Ton gezogen und
    das Video unverändert mitgenommen (BACKLOG 8)."""
    import shutil

    from . import video as _video
    tmp: Path | None = None
    try:
        video_pfad: Path | None = None
        if audio is not None and audio.is_file() \
                and audio.suffix.lower() in bibliothek.VIDEO_ENDUNGEN:
            video_pruefen(audio)
            # Video nur, wenn ein Bild drin ist (pruefe() sagt es) — ein
            # reiner Ton-Container (.m4a-artige .mp4) wird zur mp3
            if _video.pruefe(audio) is not None:
                video_pfad = audio
            tmp = Path(tempfile.mkdtemp(prefix="lt-imp-video-"))
            try:
                audio = _video.ton_extrahieren(audio, tmp / "audio.mp3")
            except RuntimeError as e:
                raise ApiFehler(422, str(e)) from e
        return _import_turns_roh(turns, name, quelle_art, audio, video_pfad)
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)


def _import_turns_roh(turns: list[dict], name: str, quelle_art: str,
                      audio: Path | None, video: Path | None) -> dict:
    if not turns:
        raise ApiFehler(400, "Keine Segmente gefunden")
    namen: list[str] = []
    for t in turns:
        sp = (t.get("speaker") or "").strip()
        if sp and sp not in namen:
            namen.append(sp)
    sprecher = [{"id": f"sp{i + 1}", "name": n}
                for i, n in enumerate(namen)]
    sid = {s["name"]: s["id"] for s in sprecher}
    segmente = [{"start": t["t0_s"], "end": t["t1_s"],
                 "sprecher": sid.get((t.get("speaker") or "").strip()),
                 "text": t["text"]} for t in turns]
    # Eine fremde VTT/CSV ist die Quelle, wie sie kam — `source`
    eintrag = bibliothek.anlegen(
        name=name, segmente=segmente, sprecher=sprecher,
        quelle={"datei": name, "erzeugt": quelle_art}, audio=audio,
        video=video, origin="source")
    return {"eintrag": eintrag["id"], "segmente": len(segmente),
            "sprecher": len(sprecher)}


def import_paket(daten: bytes, fallback: str) -> dict:
    """.enrich (Datei, Verzeichnis oder .zip) → Eintrag. NUR transkript.json und Audio werden
    gezogen; Analyse-Schichten fallen weg — nach dem ersten Edit
    stimmte keine davon mehr (User-Regel 2026-09-09)."""
    from . import paket
    try:
        p = paket.lies(daten)
    except paket.PaketFehler as e:
        raise ApiFehler(400, str(e)) from e
    audio_tmp: Path | None = None
    try:
        if p["audio_bytes"]:
            audio_tmp = tmpdatei(Path(p["audio_name"]).suffix, "lt-paket-")
            audio_tmp.write_bytes(p["audio_bytes"])
        # Herkunftsflags kommen aus dem Paket mit (FORMAT.md §5); das
        # Journal wird übernommen und um den Import-Run verlängert.
        eintrag = bibliothek.anlegen(
            name=p["name"] or fallback,
            segmente=p["segmente"], sprecher=p["sprecher"],
            quelle={"datei": f"{fallback}.enrich",
                    "erzeugt": "import-enrich",
                    "genau": p["genau"]},
            audio=audio_tmp, origin="source",
            journal=p.get("journal") or [], zotero=p.get("zotero"))
    finally:
        if audio_tmp is not None:
            audio_tmp.unlink(missing_ok=True)
    return {"eintrag": eintrag["id"], "segmente": len(p["segmente"]),
            "sprecher": len(p["sprecher"]), "genau": p["genau"]}


def parse_import(daten: bytes, endung: str) -> list[dict]:
    from .enrich_export.turns import parse_transkript_csv, parse_transkript_vtt
    if endung in (".vtt", ".webvtt"):
        return parse_transkript_vtt(daten)
    if endung == ".csv":
        return parse_transkript_csv(daten)
    raise ApiFehler(400, f"Nur .vtt/.csv/.enrich — nicht {endung}")


class ImportPathReq(ApiModel):
    path: str
    audio_path: str | None = None


@befehl
def import_path(args: dict) -> dict:
    from . import paket
    req = _pruefe(ImportPathReq, args)
    p = Path(req.path).expanduser()
    if not p.exists():
        raise ApiFehler(404, f"{p} fehlt")
    if paket.ist_paket(p):
        # Datei, Verzeichnis (macOS-Package) oder .zip — ein Leser
        try:
            daten = p.read_bytes() if p.is_file() else None
        except OSError as e:
            raise ApiFehler(400, str(e)) from e
        if daten is None:
            from .exporte import packe_verzeichnis
            daten = packe_verzeichnis(p)
        return import_paket(daten, p.stem.removesuffix(".enrich"))
    if not p.is_file():
        raise ApiFehler(400, f"{p.name} ist ein Ordner, kein Transkript")
    turns = parse_import(p.read_bytes(), p.suffix.lower())
    audio: Path | None = None
    if req.audio_path:
        a = Path(req.audio_path).expanduser()
        if a.is_file():
            audio = a
    if audio is None:
        for endung in bibliothek.AUDIO_ENDUNGEN + bibliothek.VIDEO_ENDUNGEN:
            k = p.with_suffix(endung)
            if k.is_file():
                audio = k
                break
    return import_turns(turns, p.stem, f"import-{p.suffix.lstrip('.')}",
                        audio)


# ---------- Zotero (Metadaten, lokal, lesend, mit Einwilligung) ----------

@befehl
def zotero_status() -> dict:
    from . import zotero
    return zotero.status()


@befehl
def zotero_candidates(q: str = "") -> dict:
    from . import zotero
    try:
        return {"candidates": zotero.kandidaten(q)}
    except zotero.ZoteroFehler as e:
        raise ApiFehler(424, str(e)) from e


class ZoteroLinkReq(ApiModel):
    item_key: str
    roles: list[str]


def _lese_oder_404(eid: str) -> dict:
    try:
        return bibliothek.lese(eid)
    except (OSError, ValueError, BibliothekFehler) as e:
        raise ApiFehler(404, eid) from e


@befehl
def zotero_link(eid: str, args: dict) -> dict:
    from . import zotero
    req = _pruefe(ZoteroLinkReq, args)
    _lese_oder_404(eid)
    try:
        it = zotero.eintrag(req.item_key)
    except zotero.ZoteroFehler as e:
        raise ApiFehler(424, str(e)) from e
    d = bibliothek.zotero_setzen(eid, zotero.schnappschuss(it, req.roles))
    return {"status": "linked", "zotero": d["zotero"]}


@befehl
def zotero_unlink(eid: str) -> dict:
    _lese_oder_404(eid)
    bibliothek.zotero_loesen(eid)
    return {"status": "unlinked"}


# ---------- Bibliothek ----------

@befehl
def transcripts() -> dict:
    return {"transcripts": bibliothek.liste(),
            "library_root": str(config.library_root() or "")}


@befehl
def transcript_get(eid: str) -> dict:
    try:
        return bibliothek.lese(eid)
    except BibliothekFehler as e:
        raise _err(e) from e


class SprecherReq(ApiModel):
    id: str
    name: str
    #: kommt vom GET zurück; beim Schreiben ignoriert — die Bibliothek
    #: entscheidet, was `human` wird (FORMAT.md §0.1: nie ableitbar)
    origin: str | None = None


class SegmentReq(ApiModel):
    id: str = ""
    start: float
    end: float
    sprecher: str | None = None
    text: str
    origin: str | None = None


class SaveReq(ApiModel):
    sprecher: list[SprecherReq]
    segmente: list[SegmentReq]


@befehl
def transcript_put(eid: str, args: dict) -> dict:
    req = _pruefe(SaveReq, args)
    try:
        d = bibliothek.lese(eid)
    except BibliothekFehler as e:
        raise _err(e) from e
    ids = {s.id for s in req.sprecher}
    for seg in req.segmente:
        if seg.sprecher and seg.sprecher not in ids:
            raise ApiFehler(422, f"Unbekannter Sprecher: {seg.sprecher}")
    # Der Editor schickt Records ohne origin — die Bibliothek setzt
    # `human` auf alles, was sich gegenüber dem alten Stand geändert
    # hat, und lässt den Rest, wie er war.
    alt_seg = {s["id"]: s for s in d.get("segmente", [])}
    alt_sp = {p["id"]: p for p in d.get("sprecher", [])}
    d["sprecher"] = [{**alt_sp.get(s.id, {}), **s.model_dump(exclude={"origin"})}
                     for s in req.sprecher]
    d["segmente"] = [{**alt_seg.get(s.id, {}), **s.model_dump(exclude={"origin"})}
                     for s in req.segmente]
    d = bibliothek.schreibe(eid, d)
    return {"status": "saved", "updated": d["updated"]}


class RenameReq(ApiModel):
    name: str


@befehl
def transcript_rename(eid: str, args: dict) -> dict:
    req = _pruefe(RenameReq, args)
    try:
        d = bibliothek.umbenennen(eid, req.name)
    except BibliothekFehler as e:
        raise _err(e) from e
    return {"status": "renamed", "name": d["name"]}


class DeleteReq(ApiModel):
    confirm: str


@befehl
def transcript_delete(eid: str, args: dict) -> dict:
    req = _pruefe(DeleteReq, args)
    if req.confirm != eid:
        raise ApiFehler(409, "confirm muss die ID sein")
    try:
        bibliothek.loeschen(eid)
    except BibliothekFehler as e:
        raise _err(e) from e
    return {"status": "deleted"}


# ---------- Medien ----------

@befehl
def video_pfad(eid: str) -> dict:
    """Pfad + MIME des unveränderten Videos — die Hülle macht daraus
    eine `asset://`-URL; der Browser-Server streamt die Datei."""
    try:
        p = bibliothek.video_pfad(eid)
    except BibliothekFehler as e:
        raise _err(e) from e
    if p is None:
        raise ApiFehler(404, "Kein Video")
    return {"path": str(p), "media": VIDEO_MEDIA.get(
        p.suffix.lower(), "application/octet-stream")}


@befehl
def audio_pfad(eid: str) -> dict:
    try:
        p = bibliothek.audio_pfad(eid)
    except BibliothekFehler as e:
        raise _err(e) from e
    if p is None:
        raise ApiFehler(404, "Kein Audio")
    return {"path": str(p), "media": AUDIO_MEDIA.get(
        p.suffix.lower(), "application/octet-stream")}


def sprecher_probe_bytes(eid: str, sid: str) -> bytes:
    """~8-s-Hörprobe: das LÄNGSTE Segment dieses Sprechers, aus dem
    Bibliotheks-Audio geschnitten (v2: braucht keine Diarisierungs-
    Rohdaten mehr — funktioniert auch für Importe und nach Neustarts).
    Liefert WAV-Bytes; keine Temp-Datei überlebt den Aufruf."""
    from .motor import MotorFehler, motor
    try:
        d = bibliothek.lese(eid)
        audio = bibliothek.audio_pfad(eid)
    except BibliothekFehler as e:
        raise _err(e) from e
    if audio is None:
        raise ApiFehler(404, "Kein Audio")
    kandidaten = [s for s in d["segmente"] if s.get("sprecher") == sid]
    if not kandidaten:
        raise ApiFehler(404, "Sprecher leer")
    seg = max(kandidaten, key=lambda s: s["end"] - s["start"])
    dauer = min(8.0, max(seg["end"] - seg["start"], 1.0))
    tmp = tmpdatei(".wav", "lt-sample-")
    try:
        try:
            motor().wav16k(audio, tmp, start=float(seg["start"]), dauer=dauer)
        except MotorFehler as e:
            raise ApiFehler(500, f"Probe fehlgeschlagen ({e})") from e
        return tmp.read_bytes()
    finally:
        tmp.unlink(missing_ok=True)


# ---------- Export ----------

def export_bytes(eid: str, format: str) -> tuple[bytes, str, str]:
    """Download-Weg (nur Browser): Inhalt, Dateiname, MIME."""
    try:
        return exporte.export_bytes(eid, format)
    except (BibliothekFehler, ValueError) as e:
        raise ApiFehler(409, str(e)) from e


def export_nach_temp(eid: str, format: str, tmp: Path) -> str:
    try:
        return exporte.export_nach(eid, format, tmp)
    except (BibliothekFehler, ValueError) as e:
        tmp.unlink(missing_ok=True)
        raise ApiFehler(409, str(e)) from e


class ExportReq(ApiModel):
    format: str
    path: str


@befehl
def export_datei(eid: str, args: dict) -> dict:
    """App-Weg: nativer Save-Dialog liefert den Zielpfad."""
    req = _pruefe(ExportReq, args)
    ziel = Path(req.path).expanduser().resolve()
    if not ziel.parent.is_dir():
        raise ApiFehler(409, f"Ordner fehlt: {ziel.parent}")
    # Review-Befund: beliebige Pfade konnten JEDE User-Datei
    # überschreiben (~/.zshrc, LaunchAgents) — die Endung muss zum
    # Format passen, mehr Constraint erlaubt der freie Save-Dialog nicht
    erlaubt = {"vtt": ".vtt", "csv": ".csv", "txt": ".txt",
               "enrich": ".enrich", "qdpx": ".zip",
               "qdpx-video": ".zip"}.get(req.format)
    if erlaubt is None:
        raise ApiFehler(409, f"Unbekanntes Format: {req.format}")
    if ziel.suffix.lower() != erlaubt:
        raise ApiFehler(409, f"Zieldatei muss auf {erlaubt} enden")
    try:
        exporte.export_nach(eid, req.format, ziel)
    except (BibliothekFehler, ValueError) as e:
        raise ApiFehler(409, str(e)) from e
    return {"status": "exported", "path": str(ziel)}
