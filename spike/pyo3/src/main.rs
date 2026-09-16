#[allow(non_camel_case_types)] type libc_wchar = i32;
use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::types::{PyCFunction, PyDict};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Instant;

fn wide(s: &str) -> Vec<libc_wchar> {
    s.chars().map(|c| c as libc_wchar).chain(std::iter::once(0)).collect()
}

/// Interpreter aus einer PyConfig starten: isoliert, home = python-runtime,
/// sys.path = stdlib + lib-dynload + venv-site-packages (kein site-Import,
/// keine Umgebungsvariablen, keine .pyc-Schreibversuche).
unsafe fn init(runtime: &str, site: &str) {
    let mut cfg: ffi::PyConfig = std::mem::zeroed();
    ffi::PyConfig_InitIsolatedConfig(&mut cfg);
    cfg.site_import = 0;
    cfg.write_bytecode = 0;
    let home = wide(runtime);
    let st = ffi::PyConfig_SetString(&mut cfg, &mut cfg.home, home.as_ptr());
    assert!(ffi::PyStatus_Exception(st) == 0);
    let prog = wide("ResearchTranscript");
    ffi::PyConfig_SetString(&mut cfg, &mut cfg.program_name, prog.as_ptr());
    cfg.module_search_paths_set = 1;
    for p in [format!("{runtime}/lib/python3.13"),
              format!("{runtime}/lib/python3.13/lib-dynload"),
              site.to_string()] {
        let w = wide(&p);
        let st = ffi::PyWideStringList_Append(&mut cfg.module_search_paths, w.as_ptr());
        assert!(ffi::PyStatus_Exception(st) == 0);
    }
    let st = ffi::Py_InitializeFromConfig(&cfg);
    ffi::PyConfig_Clear(&mut cfg);
    if ffi::PyStatus_Exception(st) != 0 {
        ffi::Py_ExitStatusException(st);
    }
    // Der Hauptthread hält nach Py_InitializeFromConfig den GIL — freigeben,
    // damit PyO3s attach/detach-Modell ab jetzt gilt.
    ffi::PyEval_SaveThread();
}

fn main() -> PyResult<()> {
    let runtime = std::env::var("RT").unwrap();
    let site = std::env::var("SITE").unwrap();
    let cfgdir = std::env::var("LT_CONFIG_DIR").unwrap();
    let t0 = Instant::now();
    unsafe { init(&runtime, &site) };
    println!("init: {:?}", t0.elapsed());

    let ticks = Arc::new(AtomicUsize::new(0));
    let t1 = Instant::now();
    let job_id: String = Python::attach(|py| -> PyResult<String> {
        let sys = py.import("sys")?;
        println!("sys.prefix={} exec={}", sys.getattr("prefix")?, sys.getattr("executable")?);
        println!("sys.flags.isolated={}", sys.getattr("flags")?.getattr("isolated")?);
        // native Erweiterung + enrich-core + unser Paket
        let pc = py.import("pydantic_core")?;
        println!("pydantic_core {} from {}", pc.getattr("__version__")?, pc.getattr("__file__")?);
        py.import("enrich_core")?;
        let os = py.import("os")?;
        os.getattr("environ")?.set_item("LT_CONFIG_DIR", &cfgdir)?;
        let config = py.import("researchtranscript.config")?;
        let d = PyDict::new(py);
        d.set_item("library_root", &cfgdir)?;
        config.getattr("write_config")?.call1((d,))?;
        let jobs = py.import("researchtranscript.jobs")?;
        println!("import jobs+pydantic+enrich_core: {:?}", t1.elapsed());
        // Fake-Pipeline wie in tests/test_jobs.py, plus Rust-Callback
        let ticks2 = ticks.clone();
        let cb = PyCFunction::new_closure(py, None, None, move |args, _kw| -> PyResult<()> {
            let (pct,): (i64,) = args.extract()?;
            ticks2.fetch_add(1, Ordering::SeqCst);
            println!("  [rust-callback aus Python-Thread {:?}] progress={pct}", std::thread::current().id());
            Ok(())
        })?;
        let ns = PyDict::new(py);
        ns.set_item("jobs", &jobs)?;
        ns.set_item("rust_cb", &cb)?;
        py.run(c"
import time
from pathlib import Path
def langsam(job, quelle, d):
    for i in range(50):
        jobs._pruefe_abbruch(job)
        rust_cb(i * 2)
        time.sleep(0.05)
    return quelle
jobs._konvertiere = langsam
", Some(&ns), None)?;
        let quelle = format!("{cfgdir}/probe.mp3");
        std::fs::write(&quelle, b"ID3fake").unwrap();
        let params = PyDict::new(py);
        for (k, v) in [("model", "x"), ("language", "de"), ("speaker_range", "auto")] { params.set_item(k, v)?; }
        params.set_item("diarize", false)?;
        params.set_item("min_speakers", 0)?; params.set_item("max_speakers", 0)?;
        params.set_item("cluster_threshold", 0.5)?;
        let pathlib = py.import("pathlib")?;
        let p = pathlib.getattr("Path")?.call1((quelle,))?;
        let job = jobs.getattr("starte")?.call1((p, "probe.mp3", params))?;
        job.get_item("id")?.extract()
    })?;
    println!("job {job_id} gestartet, Rust-Thread {:?} läuft weiter (GIL frei)", std::thread::current().id());
    // Pollen wie ein Tauri-Command: attach → sicht() → detach
    for _ in 0..6 {
        std::thread::sleep(std::time::Duration::from_millis(150));
        let st: String = Python::attach(|py| -> PyResult<String> {
            let jobs = py.import("researchtranscript.jobs")?;
            let j = jobs.getattr("JOBS")?.get_item(&job_id)?;
            Ok(format!("{} {}%", j.get_item("status")?, j.get_item("progress")?))
        })?;
        println!("poll: {st}");
    }
    let ok: bool = Python::attach(|py| -> PyResult<bool> {
        py.import("researchtranscript.jobs")?.getattr("abbrechen")?.call1((&job_id,))?.extract()
    })?;
    println!("abbrechen → {ok}");
    std::thread::sleep(std::time::Duration::from_millis(400));
    Python::attach(|py| -> PyResult<()> {
        let j = py.import("researchtranscript.jobs")?.getattr("JOBS")?.get_item(&job_id)?;
        println!("ende: status={} message={}", j.get_item("status")?, j.get_item("message")?);
        Ok(())
    })?;
    println!("callbacks empfangen: {}", ticks.load(Ordering::SeqCst));
    Ok(())
}
