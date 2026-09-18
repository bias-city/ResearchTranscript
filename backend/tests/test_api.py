"""Fassade `api.py` ohne HTTP (Plan §4 1.2/1.5/1.15): Dispatcher,
Fehlerform, Beobachter, Aufräumen, Bundle-Regel — und ein Drift-Wächter,
der jede Route in `main.py` an die Fassade bindet."""
from __future__ import annotations

import inspect
import json
import re
import time

import pytest

from researchtranscript import api, config, jobs
from researchtranscript.api import ApiFehler


@pytest.fixture()
def bibliothek(tmp_path, monkeypatch):
    monkeypatch.setenv("LT_CONFIG_DIR", str(tmp_path / "cfg"))
    lib = tmp_path / "bibliothek"
    lib.mkdir()
    config.write_config({"library_root": str(lib)})
    return lib


# ---------- Dispatcher ----------

def test_rufe_json_health():
    aus = json.loads(api.rufe_json("health", "{}"))
    assert aus["status"] == "ok"
    assert aus["version"] == config.APP_VERSION
    assert json.loads(api.rufe_json("ping", "")) == {"pong": True}


def test_rufe_unbekannter_befehl_und_argumente():
    with pytest.raises(ApiFehler) as e:
        api.rufe("gibt_es_nicht")
    assert e.value.status == 404
    with pytest.raises(ApiFehler) as e:
        api.rufe("job_get", {"falsch": 1})
    assert e.value.status == 422
    with pytest.raises(ApiFehler) as e:
        api.rufe_json("health", "kein json")
    assert e.value.status == 422


def test_pydantic_prueft_wie_frueher_der_router(bibliothek):
    # extra="forbid": ein fremdes Feld ist 422, kein stiller Durchlauf
    with pytest.raises(ApiFehler) as e:
        api.transcribe_path({"path": "x.mp3", "unbekannt": True})
    assert e.value.status == 422
    # Pflichtfeld fehlt
    with pytest.raises(ApiFehler) as e:
        api.export_datei("e1", {"format": "vtt"})
    assert e.value.status == 422
    # Einstellungen dürfen Fremdes tragen (extra="allow"), aber nur
    # DEFAULTS werden geschrieben
    cfg = api.settings_post({"language": "fr", "fremd": 1})
    assert cfg["language"] == "fr" and "fremd" not in cfg


def test_fehlerform_status_detail(bibliothek):
    with pytest.raises(ApiFehler) as e:
        api.transcript_get("nicht-da")
    assert e.value.status == 404 and "nicht-da" in e.value.detail
    with pytest.raises(ApiFehler) as e:
        api.transcript_delete("e1", {"confirm": "e2"})
    assert e.value.status == 409
    with pytest.raises(ApiFehler) as e:
        api.export_datei("e1", {"format": "docx", "path": "/tmp/x.docx"})
    assert e.value.status == 409


# ---------- Jobs: Beobachter, Abbruch, Aufräumen ----------

def test_beobachter_meldet_gedrosselt_und_statuswechsel_sofort(
        bibliothek, tmp_path, monkeypatch):
    audio = tmp_path / "a.mp3"
    audio.write_bytes(b"ID3fake")
    monkeypatch.setattr(config, "max_parallel", lambda: 1)

    def langsam(job, quelle, d):
        for i in range(30):
            jobs._pruefe_abbruch(job)
            jobs._setze(job, progress=i)        # 30 Meldungen in ~0,3 s
            time.sleep(0.01)
        raise RuntimeError("Ende gewollt")
    monkeypatch.setattr(jobs, "_konvertiere", langsam)
    from researchtranscript import video
    monkeypatch.setattr(video, "pruefe", lambda p: None)

    meldungen: list[dict] = []
    jobs.setze_beobachter(meldungen.append)
    try:
        jid = api.transcribe_path({"path": str(audio)})["job_id"]
        frist = time.time() + 5
        while time.time() < frist and api.job_get(jid)["status"] != "failed":
            time.sleep(0.02)
    finally:
        jobs.setze_beobachter(None)
    stati = [m["status"] for m in meldungen]
    assert stati[0] == "pending"                 # Anlegen sofort
    assert stati[-1] == "failed"                 # Ende sofort
    # gedrosselt: deutlich weniger als 30 Fortschritts-Meldungen
    assert 2 <= len(meldungen) < 20, len(meldungen)
    assert all("_quelle_tmp" not in m for m in meldungen)


def test_aufraeumen_vergisst_alte_beendete_jobs():
    alt = {"id": "alt1", "status": "completed",
           "created_at": "2020-01-01T00:00:00+00:00"}
    frisch = {"id": "neu1", "status": "completed",
              "created_at": "2099-01-01T00:00:00+00:00"}
    laeuft = {"id": "lauf1", "status": "transcribing",
              "created_at": "2020-01-01T00:00:00+00:00"}
    for j in (alt, frisch, laeuft):
        jobs.JOBS[j["id"]] = j
    try:
        assert jobs.aufraeumen() == 1
        assert "alt1" not in jobs.JOBS
        assert "neu1" in jobs.JOBS and "lauf1" in jobs.JOBS
    finally:
        for j in (alt, frisch, laeuft):
            jobs.JOBS.pop(j["id"], None)


def test_alle_abbrechen_beendet_laufende_jobs(bibliothek, tmp_path,
                                              monkeypatch):
    audio = tmp_path / "b.mp3"
    audio.write_bytes(b"ID3fake")

    def endlos(job, quelle, d):
        while True:
            jobs._pruefe_abbruch(job)
            time.sleep(0.01)
    monkeypatch.setattr(jobs, "_konvertiere", endlos)
    from researchtranscript import video
    monkeypatch.setattr(video, "pruefe", lambda p: None)
    jid = api.transcribe_path({"path": str(audio)})["job_id"]
    time.sleep(0.05)
    t0 = time.monotonic()
    jobs.alle_abbrechen(frist_s=2.0)
    assert time.monotonic() - t0 < 2.0
    assert api.job_get(jid)["status"] == "cancelled"


# ---------- Sprecherfarbe (User 2026-09-17) ----------

def test_sprecherfarbe_wird_gespeichert_und_geprueft(client, eintrag):
    from researchtranscript import api
    d = api.transcript_get(eintrag)
    sp = [dict(s) for s in d["sprecher"]]
    sp[0]["farbe"] = "ruby"
    api.transcript_put(eintrag, {"sprecher": sp, "segmente": d["segmente"]})
    assert api.transcript_get(eintrag)["sprecher"][0]["farbe"] == "ruby"
    sp[0]["farbe"] = "neonpink"
    with pytest.raises(ApiFehler) as e:
        api.transcript_put(eintrag, {"sprecher": sp, "segmente": d["segmente"]})
    assert e.value.status == 422


# ---------- Memo je Zeile (User 2026-09-17) ----------

def test_memo_speichern_csv_und_qdpx(client, eintrag):
    import io
    import zipfile

    from researchtranscript import api, exporte
    d = api.transcript_get(eintrag)
    seg = [dict(s) for s in d["segmente"]]
    origin_vorher = seg[0].get("origin")
    journal_vorher = len(d.get("journal") or [])
    seg[0]["memo"] = "  Hier lacht Anna —\nIronie?  "
    seg[1]["memo"] = ""
    api.transcript_put(eintrag, {"sprecher": d["sprecher"], "segmente": seg})
    d2 = api.transcript_get(eintrag)
    assert d2["segmente"][0]["memo"] == "Hier lacht Anna —\nIronie?"
    assert "memo" not in d2["segmente"][1]
    # ein Memo ist kein Eingriff in den Wortlaut: origin und Journal bleiben
    assert d2["segmente"][0].get("origin") == origin_vorher
    assert len(d2.get("journal") or []) == journal_vorher
    csv_text = exporte.export_bytes(eintrag, "csv")[0].decode("utf-8-sig")
    kopf, erste = csv_text.splitlines()[0], csv_text.splitlines()[1]
    assert kopf.endswith('"Memo"') and "Hier lacht Anna — Ironie?" in erste
    # REFI-QDA: Note + NoteRef an der Selection
    z = zipfile.ZipFile(io.BytesIO(exporte.export_bytes(eintrag, "qdpx")[0]))
    innen = next(n for n in z.namelist() if n.endswith(".qdpx"))
    qdpx = zipfile.ZipFile(io.BytesIO(z.read(innen)))
    qde = qdpx.read(next(n for n in qdpx.namelist() if n.endswith(".qde"))).decode()
    assert "<Notes>" in qde and "Hier lacht Anna — Ironie?" in qde
    assert qde.count("<NoteRef") == 1 and qde.index("<Sources>") < qde.index("<Notes>")
    # enrich-Dossier: baut weiter (Memo geht dort nicht mit, Format 0.1.0)
    assert exporte.export_bytes(eintrag, "enrich")[0][:2] == b"PK"


# ---------- Warteliste (R2) ----------

def test_warteliste_ueberlebt_und_vergisst_verschwundene(tmp_path, monkeypatch):
    monkeypatch.setenv("LT_CONFIG_DIR", str(tmp_path / "cfg"))
    a = tmp_path / "a.mp3"; a.write_bytes(b"x")
    b = tmp_path / "b.mp3"; b.write_bytes(b"x")
    api.warteliste_set([{"name": "a.mp3", "pfad": str(a), "zahl": "2-2"},
                        {"name": "b.mp3", "pfad": str(b)}])
    b.unlink()
    aus = api.warteliste_get()["eintraege"]
    assert [e["pfad"] for e in aus] == [str(a)]
    assert aus[0]["zahl"] == "2-2"
    with pytest.raises(ApiFehler):
        api.warteliste_set([{"name": "x"}])          # pfad fehlt → 422


# ---------- Bundle-Regel (R6) ----------

def test_im_bundle_kein_homebrew_rueckfall(tmp_path, monkeypatch):
    monkeypatch.setenv("LT_BUNDLED", "1")
    monkeypatch.setenv("LT_APP_ROOT", str(tmp_path))
    with pytest.raises(FileNotFoundError) as e:
        config.get_ffmpeg_cli()
    assert "Bundle" in str(e.value)
    (tmp_path / "bin").mkdir()
    exe = tmp_path / "bin" / "ffmpeg"
    exe.write_text("#!/bin/sh\n")
    exe.chmod(0o755)
    assert config.get_ffmpeg_cli() == str(exe)


# ---------- Drift-Wächter Routen ↔ Fassade ----------

def test_jede_route_ruft_die_fassade():
    """`main.py` darf keine Logik mehr tragen: jeder Handler ruft
    `api.<name>`; jeder registrierte Befehl ist von irgendeiner Route
    erreichbar (sonst driftet die App vom Browser-Betrieb weg)."""
    from researchtranscript import main
    quelle = inspect.getsource(main)
    handler = re.findall(r"@app\.(?:get|post|put|delete)\([^)]*\)\s*\n"
                         r"(?:async )?def (\w+)\(", quelle)
    assert len(handler) >= 24, handler
    for name in handler:
        src = inspect.getsource(getattr(main, name))
        assert "api." in src, f"Route {name} ruft die Fassade nicht"
    # Befehle ohne HTTP-Gegenstück: nur die, die es bewusst nicht haben
    nur_app = {"ping"}
    for befehl in api.BEFEHLE:
        if befehl in nur_app:
            continue
        assert f"api.{befehl}(" in quelle, f"Befehl {befehl} ohne Route"
