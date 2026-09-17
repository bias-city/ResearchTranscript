"""ResearchTranscript — dünne HTTP-Hülle (FastAPI, Loopback, Port 5628).

Seit Variante A (App-Store-Plan §4) ist das hier nur noch Transport:
jede Route übersetzt in eine Funktion aus `api.py` und `ApiFehler` in
eine HTTPException. Die App selbst spricht nicht mehr HTTP — sie ruft
die Fassade im Prozess (PyO3). Der Server bleibt für den Browser-Betrieb
(Vite-Proxy, Playwright, Screenshots) und für pytest (`TestClient`).

Nur hier: Upload-Routen (Multipart), Download-Routen, Streaming von
Medien, statisches Frontend, CORS, Host-Wache.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse, Response

from . import api, config
from .api import ApiFehler

app = FastAPI(title=config.APP_NAME, version=config.APP_VERSION)

# Das Tauri-Fenster (Origin tauri://localhost) sprach 127.0.0.1:5628
# CROSS-origin — ohne CORS blockt WebKit die Antwort („Load failed",
# Live-Befund 2026-08-30). Bleibt für den Dev-Server (`tauri dev` mit
# Vite) — die gebaute App braucht es nicht mehr.
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://tauri.localhost",
                   "http://localhost:1421"],
    allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def host_wache(request, call_next):
    """DNS-Rebinding-Schutz (Review-Befund): eine fremde Domain, die
    per Rebinding auf 127.0.0.1 zeigt, trägt ihren eigenen Host-Header
    — nur echte lokale Hosts kommen durch."""
    host = (request.headers.get("host") or "").split(":")[0]
    if host not in ("127.0.0.1", "localhost", "tauri.localhost"):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=421,
                            content={"detail": f"Host nicht erlaubt: {host}"})
    return await call_next(request)


@app.exception_handler(ApiFehler)
async def _api_fehler(_request, e: ApiFehler):
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=e.status, content={"detail": e.detail})


# ---------- Health / Modelle / Einstellungen ----------

@app.get("/api/health")
def health() -> dict:
    return api.health()


@app.get("/api/models")
def models() -> dict:
    return api.models()


@app.get("/api/settings")
def settings_get() -> dict:
    return api.settings_get()


@app.post("/api/settings")
def settings_post(req: dict) -> dict:
    return api.settings_post(req)


# ---------- Transkription ----------

@app.post("/api/transcribe")
async def transcribe_upload(file: UploadFile = File(...),
                            model: str = Form("large-v3-turbo"),
                            language: str = Form("de"),
                            speaker_range: str = Form("auto"),
                            cluster_threshold: float = Form(0.5),
                            diarize: bool = Form(True)) -> dict:
    name = file.filename or "audio"
    endung = Path(name).suffix.lower()
    if not api.endung_erlaubt(endung):
        raise HTTPException(status_code=400,
                            detail=f"Nicht unterstützt: {endung}")
    tmp = api.tmpdatei(endung, "lt-up-")
    with tmp.open("wb") as f:
        while chunk := await file.read(1 << 20):
            f.write(chunk)
    return api.transcribe_temp(tmp, name, {
        "model": model, "language": language,
        "speaker_range": speaker_range,
        "cluster_threshold": cluster_threshold, "diarize": diarize})


@app.post("/api/transcribe-path")
def transcribe_path(req: dict) -> dict:
    return api.transcribe_path(req)


@app.get("/api/jobs")
def jobs_liste() -> dict:
    return api.jobs_liste()


@app.get("/api/jobs/{job_id}")
def job_get(job_id: str) -> dict:
    return api.job_get(job_id)


@app.post("/api/jobs/{job_id}/cancel")
def job_cancel(job_id: str) -> dict:
    return api.job_cancel(job_id)


# ---------- Import ----------

@app.post("/api/import")
async def import_upload(datei: UploadFile = File(...),
                        audio: UploadFile | None = File(None)) -> dict:
    name = Path(datei.filename or "transkript")
    roh = await datei.read()
    if name.suffix.lower() == ".enrich" or name.name.lower().endswith(".enrich.zip"):
        return api.import_paket(roh, name.stem.removesuffix(".enrich"))
    turns = api.parse_import(roh, name.suffix.lower())
    audio_tmp: Path | None = None
    try:
        if audio is not None and audio.filename:
            endung = Path(audio.filename).suffix.lower()
            if api.endung_erlaubt(endung):
                audio_tmp = api.tmpdatei(endung, "lt-imp-")
                audio_tmp.write_bytes(await audio.read())
        return api.import_turns(turns, name.stem,
                                f"import-{name.suffix.lstrip('.')}",
                                audio_tmp)
    finally:
        if audio_tmp is not None:
            audio_tmp.unlink(missing_ok=True)


@app.post("/api/import-path")
def import_path(req: dict) -> dict:
    return api.import_path(req)


# ---------- Zotero ----------

@app.get("/api/zotero/status")
def zotero_status() -> dict:
    return api.zotero_status()


@app.get("/api/zotero/candidates")
def zotero_candidates(q: str = "") -> dict:
    return api.zotero_candidates(q)


@app.post("/api/transcripts/{eid}/zotero")
def zotero_link(eid: str, req: dict) -> dict:
    return api.zotero_link(eid, req)


@app.delete("/api/transcripts/{eid}/zotero")
def zotero_unlink(eid: str) -> dict:
    return api.zotero_unlink(eid)


# ---------- Bibliothek ----------

@app.get("/api/transcripts")
def transcripts() -> dict:
    return api.transcripts()


@app.get("/api/transcripts/{eid}")
def transcript_get(eid: str) -> dict:
    return api.transcript_get(eid)


@app.put("/api/transcripts/{eid}")
def transcript_put(eid: str, req: dict) -> dict:
    return api.transcript_put(eid, req)


@app.post("/api/transcripts/{eid}/rename")
def transcript_rename(eid: str, req: dict) -> dict:
    return api.transcript_rename(eid, req)


@app.post("/api/transcripts/{eid}/delete")
def transcript_delete(eid: str, req: dict) -> dict:
    return api.transcript_delete(eid, req)


# ---------- Medien (nur Browser: die App nutzt asset://) ----------

@app.get("/api/transcripts/{eid}/video")
def transcript_video(eid: str):
    """Das Video unverändert; FileResponse beantwortet Range-Anfragen —
    der Browser springt damit direkt an die Stelle."""
    v = api.video_pfad(eid)
    return FileResponse(v["path"], media_type=v["media"])


@app.get("/api/transcripts/{eid}/audio")
def transcript_audio(eid: str):
    a = api.audio_pfad(eid)
    return FileResponse(a["path"], media_type=a["media"])


@app.get("/api/transcripts/{eid}/sprecher/{sid}/sample")
def sprecher_sample(eid: str, sid: str):
    return Response(api.sprecher_probe_bytes(eid, sid),
                    media_type="audio/wav")


# ---------- Export ----------

@app.get("/api/transcripts/{eid}/export/{format}")
def export_download(eid: str, format: str) -> Response:
    if format == "qdpx-video":
        # Das Video kann Gigabytes haben: auf die Platte streamen, nie
        # als ein bytes-Objekt (Review 2026-09-11)
        from starlette.background import BackgroundTask
        tmp = api.tmpdatei(".zip", "lt-exp-")
        name = api.export_nach_temp(eid, format, tmp)
        return FileResponse(tmp, media_type="application/zip", filename=name,
                            background=BackgroundTask(tmp.unlink, missing_ok=True))
    inhalt, name, media = api.export_bytes(eid, format)
    return Response(inhalt, media_type=media, headers={
        "Content-Disposition": f'attachment; filename="{name}"'})


@app.post("/api/transcripts/{eid}/export")
def export_datei(eid: str, req: dict) -> dict:
    return api.export_datei(eid, req)


# ---------- Statisches Frontend (Browser-Betrieb) ----------

_DIST = Path(__file__).resolve().parent.parent.parent.parent \
    / "frontend" / "dist"
# Im Bundle liegt das GEBAUTE Frontend unter Resources/frontend; im
# Dev-Repo ist frontend/ der QUELL-Ordner (eigene index.html!) — dort
# zählt nur dist/.
_KANDIDATEN = ([config.get_app_root() / "frontend"]
               if config.is_bundled() else []) + [_DIST]
for kandidat in _KANDIDATEN:
    if (kandidat / "index.html").is_file():
        import mimetypes

        from fastapi.staticfiles import StaticFiles

        # macOS-Python kennt .js teils nur als octet-stream —
        # Strict-MIME-Checking bricht dann jedes ES-Modul
        mimetypes.add_type("text/javascript", ".js")
        mimetypes.add_type("text/css", ".css")
        app.mount("/", StaticFiles(directory=kandidat, html=True),
                  name="static")
        break

def cli() -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=config.PORT)
