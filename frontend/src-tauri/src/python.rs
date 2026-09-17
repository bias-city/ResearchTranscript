//! Phase-0-Spike F1 (docs/appstore-plan.md §3): CPython aus dem Bundle im
//! Prozess der Hülle starten und die Messpunkte als Tauri-Befehle anbieten.
//! Kein Teil der eigentlichen App — die Befehle heissen alle `spike_*`.
use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::types::{PyCFunction, PyDict};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Mutex, Once};
use std::time::Instant;
use tauri::Manager;

static INIT: Once = Once::new();
static INIT_MS: Mutex<f64> = Mutex::new(0.0);
static TICKS: AtomicUsize = AtomicUsize::new(0);

#[allow(non_camel_case_types)]
type WChar = i32; // wchar_t auf macOS

fn wide(s: &str) -> Vec<WChar> {
    s.chars().map(|c| c as WChar).chain(std::iter::once(0)).collect()
}

/// Isolierte Konfiguration: home = python-runtime, sys.path nur Stdlib,
/// lib-dynload und das site-packages des venv; kein site-Import, keine
/// Umgebungsvariablen, keine .pyc-Schreibversuche (Bundle ist versiegelt).
unsafe fn interpreter_starten(runtime: &Path, site: &Path) -> Result<(), String> {
    // Ohne Umgebung (isoliert) fiele Python auf die C-Locale zurück: Datei-
    // system- und open()-Encoding ASCII — Umlaute in Pfaden und Texten
    // brechen (Messung 4). UTF-8-Modus in der Vorkonfiguration erzwingen.
    let mut pre: ffi::PyPreConfig = std::mem::zeroed();
    ffi::PyPreConfig_InitIsolatedConfig(&mut pre);
    pre.utf8_mode = 1;
    if ffi::PyStatus_Exception(ffi::Py_PreInitialize(&pre)) != 0 {
        return Err("Py_PreInitialize fehlgeschlagen".into());
    }
    let mut cfg: ffi::PyConfig = std::mem::zeroed();
    ffi::PyConfig_InitIsolatedConfig(&mut cfg);
    cfg.site_import = 0;
    cfg.write_bytecode = 0;
    let home = wide(&runtime.to_string_lossy());
    if ffi::PyStatus_Exception(ffi::PyConfig_SetString(&mut cfg, &mut cfg.home, home.as_ptr())) != 0 {
        return Err("PyConfig home".into());
    }
    let prog = wide("ResearchTranscript");
    ffi::PyConfig_SetString(&mut cfg, &mut cfg.program_name, prog.as_ptr());
    cfg.module_search_paths_set = 1;
    for p in [runtime.join("lib/python3.13"), runtime.join("lib/python3.13/lib-dynload"), site.to_path_buf()] {
        let w = wide(&p.to_string_lossy());
        if ffi::PyStatus_Exception(ffi::PyWideStringList_Append(&mut cfg.module_search_paths, w.as_ptr())) != 0 {
            return Err(format!("sys.path: {}", p.display()));
        }
    }
    let st = ffi::Py_InitializeFromConfig(&cfg);
    ffi::PyConfig_Clear(&mut cfg);
    if ffi::PyStatus_Exception(st) != 0 {
        return Err("Py_InitializeFromConfig fehlgeschlagen".into());
    }
    ffi::PyEval_SaveThread(); // GIL freigeben: ab jetzt attach/detach
    Ok(())
}

fn resources(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    app.path().resource_dir().map_err(|e| e.to_string())
}

fn sicherstellen(app: &tauri::AppHandle) -> Result<(), String> {
    let res = resources(app)?;
    let mut fehler: Option<String> = None;
    // Das Backend leitet seine Wurzel aus __file__ ab (Repo-Layout); im
    // Bundle liegt das Paket im venv — die Wurzel muss der Engine setzen.
    std::env::set_var("LT_APP_ROOT", &res);
    std::env::set_var("LT_BUNDLED", "1");
    INIT.call_once(|| {
        let t0 = Instant::now();
        let r = unsafe {
            interpreter_starten(&res.join("python-runtime"), &res.join("venv/lib/python3.13/site-packages"))
        };
        match r {
            Ok(()) => *INIT_MS.lock().unwrap() = t0.elapsed().as_secs_f64() * 1000.0,
            Err(e) => fehler = Some(e),
        }
    });
    match fehler { Some(e) => Err(e), None => Ok(()) }
}

fn py_err(e: PyErr) -> String { format!("Python: {e}") }

pub fn protokoll(_app: &tauri::AppHandle, zeile: &str) {
    println!("[spike] {zeile}");
    if let Ok(home) = std::env::var("HOME") {
        use std::io::Write;
        if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(format!("{home}/spike.log")) {
            let _ = writeln!(f, "{zeile}");
        }
    }
}

#[tauri::command]
pub fn spike_log(app: tauri::AppHandle, zeile: String) { protokoll(&app, &zeile); }

#[tauri::command]
pub fn spike_health(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    sicherstellen(&app)?;
    let init_ms = *INIT_MS.lock().unwrap();
    let res = resources(&app)?;
    Python::attach(|py| -> PyResult<serde_json::Value> {
        let sys = py.import("sys")?;
        let cfg = py.import("researchtranscript.config")?;
        Ok(serde_json::json!({
            "init_ms": init_ms,
            "version": cfg.getattr("APP_VERSION")?.extract::<String>()?,
            "app": cfg.getattr("APP_NAME")?.extract::<String>()?,
            "prefix": sys.getattr("prefix")?.extract::<String>()?,
            "isolated": sys.getattr("flags")?.getattr("isolated")?.extract::<i64>()?,
            "home": std::env::var("HOME").unwrap_or_default(),
            "resources": res.to_string_lossy(),
            "sandboxed": std::env::var("APP_SANDBOX_CONTAINER_ID").is_ok(),
            "fs_encoding": sys.getattr("getfilesystemencoding")?.call0()?.extract::<String>()?,
            "utf8_mode": sys.getattr("flags")?.getattr("utf8_mode")?.extract::<i64>()?,
            // Umlaut-Schreibprobe im Container (Messung 4 scheiterte an ASCII)
            "umlaut_probe": py.eval(c"(lambda p: (__import__('pathlib').Path(p).write_text('Hülle ü\\n'), __import__('pathlib').Path(p).read_text().strip(), __import__('os').remove(p))[1])(__import__('tempfile').gettempdir() + '/prüfung-ü.txt')", None, None)?.extract::<String>()?,
        }))
    }).map_err(py_err)
}

#[tauri::command]
pub fn spike_import(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    sicherstellen(&app)?;
    let t0 = Instant::now();
    Python::attach(|py| -> PyResult<serde_json::Value> {
        let pc = py.import("pydantic_core")?;
        py.import("enrich_core")?;
        py.import("researchtranscript.bibliothek")?;
        py.import("researchtranscript.exporte")?;
        py.import("researchtranscript.format2")?;
        py.import("researchtranscript.jobs")?;
        Ok(serde_json::json!({
            "import_ms": t0.elapsed().as_secs_f64() * 1000.0,
            "pydantic_core": pc.getattr("__version__")?.extract::<String>()?,
            "pydantic_core_datei": pc.getattr("__file__")?.extract::<String>()?,
        }))
    }).map_err(py_err)
}

/// Vier Fake-Jobs durch jobs.py (Threads in Python) mit Rust-Callback.
#[tauri::command]
pub fn spike_job_start(app: tauri::AppHandle, anzahl: u32) -> Result<Vec<String>, String> {
    sicherstellen(&app)?;
    Python::attach(|py| -> PyResult<Vec<String>> {
        let home = std::env::var("HOME").unwrap_or_default();
        let bib = format!("{home}/Documents/ResearchTranscript");
        std::fs::create_dir_all(&bib).ok();
        let config = py.import("researchtranscript.config")?;
        let d = PyDict::new(py);
        d.set_item("library_root", &bib)?;
        d.set_item("max_parallel", anzahl)?;
        config.getattr("write_config")?.call1((d,))?;
        let jobs = py.import("researchtranscript.jobs")?;
        let cb = PyCFunction::new_closure(py, None, None, move |_args, _kw| -> PyResult<()> {
            TICKS.fetch_add(1, Ordering::SeqCst);
            Ok(())
        })?;
        let ns = PyDict::new(py);
        ns.set_item("jobs", &jobs)?;
        ns.set_item("rust_cb", &cb)?;
        py.run(c"
import time
def langsam(job, quelle, d):
    for i in range(120):
        jobs._pruefe_abbruch(job)
        jobs._setze(job, progress=int(i / 1.2))
        rust_cb(i)
        time.sleep(0.05)
    raise RuntimeError('Spike-Ende nach Konvertierung (gewollt)')
jobs._konvertiere = langsam
", Some(&ns), None)?;
        let pathlib = py.import("pathlib")?;
        let mut ids = Vec::new();
        for i in 0..anzahl {
            let quelle = format!("{home}/spike-{i}.mp3");
            std::fs::write(&quelle, b"ID3fake").map_err(|e| PyErr::new::<pyo3::exceptions::PyOSError, _>(e.to_string()))?;
            let params = PyDict::new(py);
            for (k, v) in [("model", "x"), ("language", "de"), ("speaker_range", "auto")] { params.set_item(k, v)?; }
            params.set_item("diarize", false)?;
            params.set_item("min_speakers", 0)?; params.set_item("max_speakers", 0)?;
            params.set_item("cluster_threshold", 0.5)?;
            let p = pathlib.getattr("Path")?.call1((quelle,))?;
            let job = jobs.getattr("starte")?.call1((p, format!("spike-{i}.mp3"), params))?;
            ids.push(job.get_item("id")?.extract()?);
        }
        Ok(ids)
    }).map_err(py_err)
}

#[tauri::command]
pub fn spike_job_poll(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    sicherstellen(&app)?;
    let t0 = Instant::now();
    let v = Python::attach(|py| -> PyResult<Vec<(String, String, i64)>> {
        let jobs = py.import("researchtranscript.jobs")?;
        let mut aus = Vec::new();
        for (_, j) in jobs.getattr("JOBS")?.cast::<PyDict>()?.iter() {
            let fehler: String = j.get_item("error").ok().and_then(|e| e.extract().ok()).unwrap_or_default();
            let meldung: String = j.get_item("message").ok().and_then(|e| e.extract().ok()).unwrap_or_default();
            aus.push((j.get_item("id")?.extract()?, format!("{}:{}{}", j.get_item("status")?.extract::<String>()?, meldung,
                      if fehler.is_empty() { String::new() } else { format!(" [{fehler}]") }),
                      j.get_item("progress")?.extract::<i64>().unwrap_or(0)));
        }
        Ok(aus)
    }).map_err(py_err)?;
    Ok(serde_json::json!({ "poll_ms": t0.elapsed().as_secs_f64() * 1000.0, "ticks": TICKS.load(Ordering::SeqCst), "jobs": v }))
}

#[tauri::command]
pub fn spike_job_abbruch(app: tauri::AppHandle, id: String) -> Result<bool, String> {
    sicherstellen(&app)?;
    Python::attach(|py| -> PyResult<bool> {
        py.import("researchtranscript.jobs")?.getattr("abbrechen")?.call1((id,))?.extract()
    }).map_err(py_err)
}

/// Kernfrage: gilt die Powerbox-Freigabe eines Ordners auch für Python im
/// selben Prozess? Python (nicht Rust) listet, schreibt, liest, löscht.
#[tauri::command]
pub fn spike_ordner(app: tauri::AppHandle, pfad: String) -> Result<serde_json::Value, String> {
    sicherstellen(&app)?;
    Python::attach(|py| -> PyResult<serde_json::Value> {
        let ns = PyDict::new(py);
        ns.set_item("pfad", &pfad)?;
        py.run(c"
import os, json
ergebnis = {}
try:
    ergebnis['eintraege'] = sorted(os.listdir(pfad))[:12]
    probe = os.path.join(pfad, 'researchtranscript-spike.txt')
    with open(probe, 'w') as f: f.write('Python im Prozess der Hülle\\n')
    with open(probe) as f: ergebnis['gelesen'] = f.read().strip()
    os.remove(probe)
    ergebnis['schreiben'] = 'ok'
except Exception as e:
    ergebnis['fehler'] = f'{type(e).__name__}: {e}'
ergebnis_json = json.dumps(ergebnis)
", Some(&ns), None)?;
        let s: String = ns.get_item("ergebnis_json")?.unwrap().extract()?;
        Ok(serde_json::from_str(&s).unwrap_or(serde_json::json!({"roh": s})))
    }).map_err(py_err)
}

/// F3-Nebenfrage: läuft argmax-cli als Kindprozess (app-sandbox + inherit)
/// auf ein WAV in $TMPDIR (liegt im Container)?
#[tauri::command]
pub fn spike_kind_argmax(app: tauri::AppHandle) -> Result<serde_json::Value, String> {
    sicherstellen(&app)?;
    let res = resources(&app)?;
    let tmp = std::env::temp_dir();
    let rttm = tmp.join("spike.rttm");
    // Echtes Sprach-WAV bevorzugen, wenn es von aussen in den Container gelegt wurde
    let wav = if tmp.join("spike-real.wav").is_file() { tmp.join("spike-real.wav") } else { tmp.join("spike.wav") };
    let _ = std::fs::remove_file(&rttm);
    if wav.ends_with("spike.wav") { Python::attach(|py| -> PyResult<()> {
        let ns = PyDict::new(py);
        ns.set_item("wav", wav.to_string_lossy())?;
        py.run(c"
import wave, math, struct
with wave.open(wav, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    frames = bytearray()
    for i in range(16000 * 4):
        # zwei Töne im Wechsel, damit die Trennung etwas zu tun hat
        f = 220.0 if (i // 16000) % 2 == 0 else 440.0
        frames += struct.pack('<h', int(12000 * math.sin(2 * math.pi * f * i / 16000)))
    w.writeframes(bytes(frames))
", Some(&ns), None)
    }).map_err(py_err)?; }
    let t0 = Instant::now();
    let out = std::process::Command::new(res.join("bin/argmax-cli"))
        .args(["diarize", "--audio-path"]).arg(&wav)
        .args(["--model-path"]).arg(res.join("models/speakerkit"))
        .args(["--rttm-path"]).arg(&rttm)
        .args(["--num-speakers", "2", "--use-exclusive-reconciliation"])
        .output().map_err(|e| format!("spawn: {e}"))?;
    let text = format!("{}{}", String::from_utf8_lossy(&out.stdout), String::from_utf8_lossy(&out.stderr));
    let rttm_zeilen = std::fs::read_to_string(&rttm).map(|s| s.lines().count()).unwrap_or(0);
    Ok(serde_json::json!({
        "exit": out.status.code(), "ms": t0.elapsed().as_millis(), "rttm_zeilen": rttm_zeilen,
        "rttm_datei": rttm.is_file(), "wav": wav.to_string_lossy(),
        "ausgabe_ende": text.lines().rev().take(4).collect::<Vec<_>>(), "tmpdir": tmp.to_string_lossy(),
    }))
}

#[allow(dead_code)]
pub fn ticks() -> usize { TICKS.load(Ordering::SeqCst) }

/// Messungen 1–3 und 5 ohne Oberfläche: eigener Thread, Ergebnisse ins
/// Protokoll ($HOME/spike.log im Container und stdout).
pub fn selbstlauf(app: tauri::AppHandle) {
    std::thread::spawn(move || {
        std::thread::sleep(std::time::Duration::from_millis(1500));
        let t = Instant::now();
        let z = |s: String| protokoll(&app, &format!("{:6.0} ms  {s}", t.elapsed().as_secs_f64() * 1000.0));
        z("selbstlauf: Start".into());
        match spike_health(app.clone()) { Ok(v) => z(format!("1 health: {v}")), Err(e) => { z(format!("1 FEHLER health: {e}")); return; } }
        match spike_import(app.clone()) { Ok(v) => z(format!("2 import: {v}")), Err(e) => z(format!("2 FEHLER import: {e}")) }
        let ids = match spike_job_start(app.clone(), 4) { Ok(v) => { z(format!("3 jobs: {v:?}")); v } Err(e) => { z(format!("3 FEHLER jobs: {e}")); Vec::new() } };
        let mut abgebrochen_um: Option<Instant> = None;
        for n in 0..40u32 {
            std::thread::sleep(std::time::Duration::from_millis(500));
            let p = match spike_job_poll(app.clone()) { Ok(v) => v, Err(e) => { z(format!("3 FEHLER poll: {e}")); break; } };
            let jobs = p["jobs"].as_array().cloned().unwrap_or_default();
            let kurz: Vec<String> = jobs.iter().map(|j| format!("{}:{}:{}%", j[0], j[1], j[2])).collect();
            z(format!("  poll {:.1} ms ticks {} {}", p["poll_ms"].as_f64().unwrap_or(0.0), p["ticks"], kurz.join(" ")));
            if n == 3 && !ids.is_empty() {
                let ok = spike_job_abbruch(app.clone(), ids[0].clone()).unwrap_or(false);
                abgebrochen_um = Some(Instant::now());
                z(format!("  abbrechen {} → {ok}", ids[0]));
            }
            if let Some(t0) = abgebrochen_um {
                if jobs.iter().any(|j| j[0] == ids[0].as_str() && j[1] == "cancelled") {
                    z(format!("  Abbruch wirksam nach {} ms", t0.elapsed().as_millis()));
                    abgebrochen_um = None;
                }
            }
            if !jobs.is_empty() && jobs.iter().all(|j| ["completed", "failed", "cancelled"].contains(&j[1].as_str().unwrap_or(""))) {
                z("3 alle Jobs beendet".into()); break;
            }
        }
        match spike_kind_argmax(app.clone()) { Ok(v) => z(format!("5 kind argmax: {v}")), Err(e) => z(format!("5 FEHLER kind: {e}")) }
        z("selbstlauf: Ende — für Messung 4 bitte im Fenster einen Ordner wählen".into());
        // Dauerlauf (Plan §9 Risiko 3): SPIKE_DAUER_S Sekunden lang Runden à
        // vier Fake-Jobs, dazwischen Poll alle 500 ms; je Runde Speicher
        // (max. RSS), Python-Threads und Zahl der Jobs.
        let dauer: u64 = std::env::var("SPIKE_DAUER_S").ok().and_then(|v| v.parse().ok()).unwrap_or(0);
        if dauer == 0 { return; }
        let start = Instant::now();
        let mut runde = 0u32;
        while start.elapsed().as_secs() < dauer {
            runde += 1;
            let ids = match spike_job_start(app.clone(), 4) { Ok(v) => v, Err(e) => { z(format!("dauer FEHLER start: {e}")); break; } };
            let mut polls = 0u32;
            loop {
                std::thread::sleep(std::time::Duration::from_millis(500));
                polls += 1;
                let p = match spike_job_poll(app.clone()) { Ok(v) => v, Err(e) => { z(format!("dauer FEHLER poll: {e}")); break; } };
                let jobs = p["jobs"].as_array().cloned().unwrap_or_default();
                if polls == 2 { let _ = spike_job_abbruch(app.clone(), ids[0].clone()); }
                let fertig = jobs.iter().filter(|j| ids.contains(&j[0].as_str().unwrap_or("").to_string()))
                    .all(|j| ["completed", "failed", "cancelled"].contains(&j[1].as_str().unwrap_or("")));
                if fertig || polls > 60 { break; }
            }
            let mess = Python::attach(|py| -> PyResult<String> {
                py.eval(c"(lambda r, t, j: f'rss_max={r.getrusage(r.RUSAGE_SELF).ru_maxrss // 1048576} MB threads={t.active_count()} jobs={len(j.JOBS)}')(__import__('resource'), __import__('threading'), __import__('researchtranscript.jobs').jobs)", None, None)?.extract::<String>()
            }).unwrap_or_else(|e| format!("FEHLER {e}"));
            z(format!("dauer Runde {runde} nach {} s, {polls} Polls: {mess}", start.elapsed().as_secs()));
        }
        z(format!("dauer: Ende nach {} Runden, {} s", runde, start.elapsed().as_secs()));
    });
}
