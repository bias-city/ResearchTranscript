//! PyO3-Brücke: CPython aus dem Bundle im Prozess der Hülle (Plan §4 1.8).
//!
//! REGELN (Plan R4, Risiko 3 — ein GIL-Hänger friert die ganze App):
//! - `Python::attach` NIE auf dem Cocoa-Hauptthread. Jeder Tauri-Befehl
//!   ist `async fn` und ruft `rufe` in `spawn_blocking`.
//! - Lange Rechnungen (Motoren, Phase 2) laufen in `py.detach`.
//! - Der Interpreter wird EINMAL gestartet und nie finalisiert
//!   (`Py_FinalizeEx` mit laufenden Job-Threads hängt); beim Beenden
//!   `alle_abbrechen()` und dann einfach Prozessende.
//! - Kein `std::OnceLock` für Python-Objekte (Deadlock mit dem GIL) —
//!   `pyo3::sync::PyOnceLock`.
//!
//! Befund Phase 0: `PyPreConfig.utf8_mode = 1` (sonst ASCII in `open()`),
//! `LT_APP_ROOT`/`LT_BUNDLED` VOR dem Start (Python friert `os.environ`
//! beim Import ein), `network.client` für WKWebView in der Sandbox.
use pyo3::ffi;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyBytes, PyCFunction, PyDict, PyModule, PyTuple};
use std::path::{Path, PathBuf};
use std::sync::{Mutex, Once};
use tauri::{Emitter, Manager};

use crate::protokoll;

static INIT: Once = Once::new();
static INIT_FEHLER: Mutex<Option<String>> = Mutex::new(None);
static API: PyOnceLock<Py<PyModule>> = PyOnceLock::new();

/// Fehlerform der Fassade — `{status, detail}` wie die HTTP-Hülle.
#[derive(Debug, Clone, serde::Serialize)]
pub struct ApiFehler {
    pub status: u16,
    pub detail: String,
}

impl From<String> for ApiFehler {
    fn from(s: String) -> Self { ApiFehler { status: 500, detail: s } }
}

#[allow(non_camel_case_types)]
type WChar = i32; // wchar_t auf macOS

fn wide(s: &str) -> Vec<WChar> {
    s.chars().map(|c| c as WChar).chain(std::iter::once(0)).collect()
}

/// Wo liegen python-runtime, site-packages, bin, models? Im Bundle
/// `Contents/Resources`; unter `tauri dev` kopiert tauri-build die
/// Ressourcen neben die Binärdatei, sonst der Checkout.
pub fn resources(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let mut kandidaten: Vec<PathBuf> = Vec::new();
    if let Ok(p) = app.path().resource_dir() { kandidaten.push(p); }
    kandidaten.push(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources"));
    for k in &kandidaten {
        if k.join("python-runtime/lib/libpython3.13.dylib").is_file() {
            return Ok(k.clone());
        }
    }
    Err(format!("python-runtime fehlt (gesucht: {})",
                kandidaten.iter().map(|p| p.display().to_string()).collect::<Vec<_>>().join(", ")))
}

/// site-packages: neues Layout `python/site-packages` (Plan 1.13), bis
/// dahin das venv aus bundle-resources.mjs.
fn site_packages(res: &Path) -> Result<PathBuf, String> {
    for p in [res.join("python/site-packages"), res.join("venv/lib/python3.13/site-packages")] {
        if p.join("researchtranscript").is_dir() { return Ok(p); }
    }
    Err("site-packages mit researchtranscript fehlt — scripts/bundle-resources.mjs laufen lassen".into())
}

/// Isolierte Konfiguration: home = python-runtime, sys.path nur Stdlib,
/// lib-dynload und site-packages; kein site-Import, keine Umgebungs-
/// variablen, keine .pyc-Schreibversuche (Bundle ist versiegelt).
unsafe fn interpreter_starten(runtime: &Path, site: &Path) -> Result<(), String> {
    // UTF-8-Modus in der Vorkonfiguration (Befund 3): ohne Umgebung fiele
    // Python in die C-Locale, open() schriebe ASCII.
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
    cfg.install_signal_handlers = 0;
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

fn py_text(e: &PyErr, py: Python<'_>) -> String {
    let tb = e.traceback(py).and_then(|t| t.format().ok()).unwrap_or_default();
    format!("{e}\n{tb}")
}

/// Python-stdout/stderr ins Protokoll (Plan R3): in einer Finder-App
/// gingen sie ins Nichts — `threading.excepthook` wäre blind.
fn stdio_umleiten(py: Python<'_>) -> PyResult<()> {
    let cb = PyCFunction::new_closure(py, None, None, |args: &Bound<'_, PyTuple>, _k: Option<&Bound<'_, PyDict>>| -> PyResult<()> {
        let kanal: String = args.get_item(0)?.extract()?;
        let zeile: String = args.get_item(1)?.extract()?;
        protokoll::schreibe(if kanal == "err" { "py!" } else { "py" }, &zeile);
        Ok(())
    })?;
    let ns = PyDict::new(py);
    ns.set_item("cb", cb)?;
    py.run(c"
import sys
class _Aus:
    encoding = 'utf-8'
    def __init__(self, kanal): self.kanal = kanal; self._rest = ''
    def write(self, s):
        if not s: return 0
        self._rest += str(s)
        while '\\n' in self._rest:
            zeile, self._rest = self._rest.split('\\n', 1)
            if zeile.strip(): cb(self.kanal, zeile)
        return len(s)
    def flush(self):
        if self._rest.strip(): cb(self.kanal, self._rest)
        self._rest = ''
    def isatty(self): return False
    def fileno(self): raise OSError('kein fd')
sys.stdout = _Aus('out'); sys.stderr = _Aus('err')
", Some(&ns), None)
}

/// Job-Beobachter → Tauri-Ereignis `job` (gedrosselt in jobs.py).
fn beobachter_setzen(py: Python<'_>, app: tauri::AppHandle) -> PyResult<()> {
    let cb = PyCFunction::new_closure(py, None, None, move |args: &Bound<'_, PyTuple>, _k: Option<&Bound<'_, PyDict>>| -> PyResult<()> {
        let py = args.py();
        let sicht = args.get_item(0)?;
        let text: String = py.import("json")?.getattr("dumps")?.call1((sicht,))?.extract()?;
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(&text) {
            let _ = app.emit("job", v);
        }
        Ok(())
    })?;
    py.import("researchtranscript.jobs")?.getattr("setze_beobachter")?.call1((cb,))?;
    Ok(())
}

/// Einmal je Prozess: Umgebung, Interpreter, Fassade importieren,
/// stdio umleiten, Beobachter setzen. Liefert die Startzeit in ms.
pub fn init(app: &tauri::AppHandle) -> Result<f64, String> {
    let res = resources(app)?;
    init_pfad(&res, Some(app))
}

/// Dasselbe ohne Hülle — für den Integrationstest (`cargo test`),
/// der die gebündelte Laufzeit direkt aus `resources/` startet.
pub fn init_pfad(res: &Path, app: Option<&tauri::AppHandle>) -> Result<f64, String> {
    let site = site_packages(res)?;
    let t0 = std::time::Instant::now();
    INIT.call_once(|| {
        // VOR dem Start (Python friert os.environ beim os-Import ein)
        std::env::set_var("LT_APP_ROOT", res);
        std::env::set_var("LT_BUNDLED", "1");
        std::env::set_var("LT_EMBEDDED", "1");
        // Motoren im Prozess (Plan §5): das Rust-Modul muss VOR dem
        // Interpreter in die inittab; libmp3lame liegt im Bundle unter
        // Contents/Frameworks, im Checkout unter resources/frameworks.
        #[cfg(feature = "motoren")]
        {
            use crate::motoren::researchtranscript_motoren;
            pyo3::append_to_inittab!(researchtranscript_motoren);
            let lame = [res.parent().map(|p| p.join("Frameworks/libmp3lame.dylib")),
                        Some(res.join("frameworks/libmp3lame.dylib"))]
                .into_iter().flatten().find(|p| p.is_file());
            if let Some(p) = lame { std::env::set_var("LT_LAME_DYLIB", p); }
            // Standard seit 0.6.0 (E3, Parität belegt): Motoren im Prozess;
            // LT_MOTOR=kind in der Umgebung erzwingt die Kinder (Fehlersuche).
            if std::env::var_os("LT_MOTOR").is_none() { std::env::set_var("LT_MOTOR", "prozess"); }
        }
        let r = unsafe { interpreter_starten(&res.join("python-runtime"), &site) };
        if let Err(e) = r {
            *INIT_FEHLER.lock().unwrap() = Some(e);
            return;
        }
        let r = Python::attach(|py| -> PyResult<()> {
            stdio_umleiten(py)?;
            let m = py.import("researchtranscript.api")?;
            let _ = API.set(py, m.unbind());
            if let Some(app) = app { beobachter_setzen(py, app.clone())?; }
            Ok(())
        });
        if let Err(e) = r {
            let text = Python::attach(|py| py_text(&e, py));
            *INIT_FEHLER.lock().unwrap() = Some(format!("Fassade: {text}"));
        }
    });
    if let Some(e) = INIT_FEHLER.lock().unwrap().clone() {
        return Err(e);
    }
    Ok(t0.elapsed().as_secs_f64() * 1000.0)
}

fn api<'py>(py: Python<'py>) -> Result<&'py Bound<'py, PyModule>, ApiFehler> {
    API.get(py).map(|m| m.bind(py)).ok_or_else(|| ApiFehler { status: 500, detail: "Python nicht gestartet".into() })
}

fn fehler_aus(py: Python<'_>, e: PyErr) -> ApiFehler {
    let v = e.value(py);
    let status = v.getattr("status").ok().and_then(|s| s.extract::<u16>().ok());
    let detail = v.getattr("detail").ok().and_then(|d| d.extract::<String>().ok());
    match (status, detail) {
        (Some(status), Some(detail)) => ApiFehler { status, detail },
        _ => {
            let text = py_text(&e, py);
            protokoll::schreibe("py!", &text);
            ApiFehler { status: 500, detail: format!("{e}") }
        }
    }
}

/// Fassaden-Befehl: JSON rein, JSON raus. Immer aus `spawn_blocking`.
pub fn rufe(name: &str, args: &serde_json::Value) -> Result<serde_json::Value, ApiFehler> {
    let args_text = serde_json::to_string(args).map_err(|e| e.to_string())?;
    Python::attach(|py| {
        let m = api(py)?;
        let aus = m.getattr("rufe_json").map_err(|e| fehler_aus(py, e))?
            .call1((name, args_text)).map_err(|e| fehler_aus(py, e))?;
        let text: String = aus.extract().map_err(|e| fehler_aus(py, e))?;
        serde_json::from_str(&text).map_err(|e| ApiFehler { status: 500, detail: format!("Antwort kein JSON: {e}") })
    })
}

/// Hörprobe als WAV-Bytes (kein Temp-Leck, kein HTTP).
pub fn sprecher_probe(eid: &str, sid: &str) -> Result<Vec<u8>, ApiFehler> {
    Python::attach(|py| {
        let m = api(py)?;
        let aus = m.getattr("sprecher_probe_bytes").map_err(|e| fehler_aus(py, e))?
            .call1((eid, sid)).map_err(|e| fehler_aus(py, e))?;
        let b = aus.cast::<PyBytes>().map_err(|_| ApiFehler { status: 500, detail: "keine Bytes".into() })?;
        Ok(b.as_bytes().to_vec())
    })
}

/// Beim Beenden: Abbruch-Ereignisse setzen, Kinder töten, kurz warten.
pub fn alle_abbrechen() {
    if !INIT.is_completed() { return; }
    let r = Python::attach(|py| -> PyResult<()> {
        py.import("researchtranscript.jobs")?.getattr("alle_abbrechen")?.call1((2.0,))?;
        Ok(())
    });
    if let Err(e) = r {
        protokoll::schreibe("exit", &format!("alle_abbrechen: {e}"));
    }
}

/// Start-Selbstprüfung (Plan R5): was hier fehlt, meldet ein Dialog
/// mit Klartext statt eines leeren Fensters.
pub fn selbstpruefung(res: &Path) -> Vec<String> {
    let mut probleme = Vec::new();
    let r = Python::attach(|py| -> PyResult<(String, i64, String)> {
        let sys = py.import("sys")?;
        let version: String = sys.getattr("version")?.extract()?;
        let utf8: i64 = sys.getattr("flags")?.getattr("utf8_mode")?.extract()?;
        let cfg = py.import("researchtranscript.config")?;
        let app_version: String = cfg.getattr("APP_VERSION")?.extract()?;
        Ok((version, utf8, app_version))
    });
    match r {
        Ok((version, utf8, app_version)) => {
            if !version.starts_with("3.13") { probleme.push(format!("Python-Laufzeit {version}, erwartet 3.13")); }
            if utf8 != 1 { probleme.push("UTF-8-Modus nicht aktiv".into()); }
            if app_version != env!("CARGO_PKG_VERSION") {
                probleme.push(format!("Backend {app_version} passt nicht zur App {}", env!("CARGO_PKG_VERSION")));
            }
        }
        Err(e) => probleme.push(Python::attach(|py| py_text(&e, py))),
    }
    // Whisper bleibt Kind (bin/whisper-cli); ffmpeg und argmax-cli braucht
    // nur noch LT_MOTOR=kind — im Bundle liegen sie seit 0.6.0 nicht mehr.
    let prozess = std::env::var("LT_MOTOR").map(|m| m == "prozess").unwrap_or(false);
    let mut noetig = vec!["bin/whisper-cli", "models"];
    if !prozess { noetig.extend(["bin/ffmpeg", "bin/argmax-cli"]); }
    for name in noetig {
        if !res.join(name).exists() { probleme.push(format!("{name} fehlt in den Ressourcen")); }
    }
    if prozess && std::env::var_os("LT_LAME_DYLIB").is_none() {
        probleme.push("libmp3lame.dylib fehlt (Contents/Frameworks) — scripts/baue-lame.sh".into());
    }
    let motor = Python::attach(|py| -> PyResult<String> {
        Ok(py.import("researchtranscript.motor")?.getattr("motor")?.call0()?.getattr("name")?.extract()?)
    }).unwrap_or_else(|e| format!("? ({e})"));
    protokoll::schreibe("start", &format!("Motor: {motor}"));
    probleme
}
