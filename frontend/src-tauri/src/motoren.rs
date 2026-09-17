//! Motoren im Prozess (Plan §5): das Python-Modul `researchtranscript_motoren`
//! über die C-Schnittstelle des Swift-Pakets RTMotoren (AVFoundation +
//! libmp3lame für den Ton, SpeakerKit-Shim für die Sprechertrennung).
//! Whisper bleibt Kindprozess (User-Entscheid 17.9.2026) — kommt hier
//! nicht vor.
//!
//! Jede Rechnung läuft in `py.detach` (GIL frei — sonst friert jeder
//! Befehl samt Abbruch, python.rs-Kopf). Rückrufe aus Swift (Abbruch?
//! Fortschritt) holen den GIL kurz zurück (`Python::attach`), gedrosselt
//! auf 10 Hz. Ergebnisse sind JSON-Texte aus Swift → `json.loads`.
//!
//! Nur mit Cargo-Feature `motoren` (SwiftLinker in build.rs); ohne das
//! Feature fehlt das Modul, und `LT_MOTOR=prozess` scheitert laut in
//! motor.py.
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::ffi::{c_char, c_void, CStr, CString};
use std::time::{Duration, Instant};

type AbbruchCb = Option<unsafe extern "C" fn(*mut c_void) -> bool>;
type FortschrittCb = Option<unsafe extern "C" fn(f64, *mut c_void)>;

extern "C" {
    fn rt_sondiere(pfad: *const c_char) -> *mut c_char;
    fn rt_dekodiere_wav16k(pfad: *const c_char, ziel: *const c_char, start_s: f64, dauer_s: f64,
                           abbruch: AbbruchCb, fortschritt: FortschrittCb, ctx: *mut c_void) -> *mut c_char;
    fn rt_nach_mp3(pfad: *const c_char, ziel: *const c_char, vbr_q: i32, lame_dylib: *const c_char,
                   abbruch: AbbruchCb, fortschritt: FortschrittCb, ctx: *mut c_void) -> *mut c_char;
    fn rt_diarize_wav(wav: *const c_char, num_speakers: i32, schwelle: f32, exklusiv: bool, modelle: *const c_char,
                      abbruch: AbbruchCb, fortschritt: FortschrittCb, ctx: *mut c_void) -> *mut c_char;
    fn rt_free(p: *mut c_char);
}

/// Rückruf-Kontext: die Python-Callables des Jobs plus Drossel.
struct Kontext {
    abbruch: Option<Py<PyAny>>,
    fortschritt: Option<Py<PyAny>>,
    zuletzt_abbruch: Instant,
    abgebrochen: bool,
    zuletzt_fortschritt: Instant,
}

const DROSSEL: Duration = Duration::from_millis(100);

unsafe extern "C" fn abbruch_tramp(ctx: *mut c_void) -> bool {
    let k = &mut *(ctx as *mut Kontext);
    if k.abgebrochen { return true; }
    let Some(cb) = &k.abbruch else { return false };
    if k.zuletzt_abbruch.elapsed() < DROSSEL { return false; }
    k.zuletzt_abbruch = Instant::now();
    k.abgebrochen = Python::attach(|py| cb.call0(py).and_then(|v| v.is_truthy(py)).unwrap_or(false));
    k.abgebrochen
}

unsafe extern "C" fn fortschritt_tramp(anteil: f64, ctx: *mut c_void) {
    let k = &mut *(ctx as *mut Kontext);
    let Some(cb) = &k.fortschritt else { return };
    if anteil < 1.0 && k.zuletzt_fortschritt.elapsed() < DROSSEL { return; }
    k.zuletzt_fortschritt = Instant::now();
    Python::attach(|py| { let _ = cb.call1(py, (anteil,)); });
}

fn c(s: &str) -> PyResult<CString> {
    CString::new(s).map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Pfad mit NUL: {e}")))
}

/// JSON-Text aus Swift → Python-Objekt; der C-String wird freigegeben.
fn ergebnis(py: Python<'_>, p: *mut c_char) -> PyResult<Py<PyAny>> {
    if p.is_null() {
        return Err(pyo3::exceptions::PyRuntimeError::new_err("Motor lieferte nichts"));
    }
    let text = unsafe { CStr::from_ptr(p) }.to_string_lossy().into_owned();
    unsafe { rt_free(p) };
    Ok(py.import("json")?.getattr("loads")?.call1((text,))?.unbind())
}

fn kontext(abbruch: Option<Py<PyAny>>, fortschritt: Option<Py<PyAny>>) -> Kontext {
    let t = Instant::now() - DROSSEL;
    Kontext { abbruch, fortschritt, zuletzt_abbruch: t, abgebrochen: false, zuletzt_fortschritt: t }
}

#[pyfunction]
fn sondiere(py: Python<'_>, pfad: &str) -> PyResult<Py<PyAny>> {
    let pfad = c(pfad)?;
    // Rohzeiger sind nicht Send — als usize durch detach tragen
    let p = py.detach(|| unsafe { rt_sondiere(pfad.as_ptr()) } as usize);
    ergebnis(py, p as *mut c_char)
}

#[pyfunction]
#[pyo3(signature = (quelle, ziel, start=0.0, dauer=0.0, abbruch=None, fortschritt=None))]
fn wav16k(py: Python<'_>, quelle: &str, ziel: &str, start: f64, dauer: f64,
          abbruch: Option<Py<PyAny>>, fortschritt: Option<Py<PyAny>>) -> PyResult<Py<PyAny>> {
    let (quelle, ziel) = (c(quelle)?, c(ziel)?);
    let mut k = kontext(abbruch, fortschritt);
    let p = py.detach(|| unsafe {
        rt_dekodiere_wav16k(quelle.as_ptr(), ziel.as_ptr(), start, dauer,
                            Some(abbruch_tramp), Some(fortschritt_tramp), &mut k as *mut Kontext as *mut c_void) as usize
    });
    ergebnis(py, p as *mut c_char)
}

#[pyfunction]
#[pyo3(signature = (quelle, ziel, q=2, abbruch=None, fortschritt=None))]
fn nach_mp3(py: Python<'_>, quelle: &str, ziel: &str, q: i32,
            abbruch: Option<Py<PyAny>>, fortschritt: Option<Py<PyAny>>) -> PyResult<Py<PyAny>> {
    let (quelle, ziel) = (c(quelle)?, c(ziel)?);
    let lame = c(&std::env::var("LT_LAME_DYLIB").unwrap_or_default())?;
    let mut k = kontext(abbruch, fortschritt);
    let p = py.detach(|| unsafe {
        rt_nach_mp3(quelle.as_ptr(), ziel.as_ptr(), q, lame.as_ptr(),
                    Some(abbruch_tramp), Some(fortschritt_tramp), &mut k as *mut Kontext as *mut c_void) as usize
    });
    ergebnis(py, p as *mut c_char)
}

#[pyfunction]
#[pyo3(signature = (wav, n=0, schwelle=0.6, exklusiv=true, modelle="", abbruch=None, fortschritt=None))]
fn trenne(py: Python<'_>, wav: &str, n: i32, schwelle: f32, exklusiv: bool, modelle: &str,
          abbruch: Option<Py<PyAny>>, fortschritt: Option<Py<PyAny>>) -> PyResult<Py<PyAny>> {
    let (wav, modelle) = (c(wav)?, c(modelle)?);
    let mut k = kontext(abbruch, fortschritt);
    let p = py.detach(|| unsafe {
        rt_diarize_wav(wav.as_ptr(), n, schwelle, exklusiv, modelle.as_ptr(),
                       Some(abbruch_tramp), Some(fortschritt_tramp), &mut k as *mut Kontext as *mut c_void) as usize
    });
    ergebnis(py, p as *mut c_char)
}

/// Das Modul, das motor.py als `researchtranscript_motoren` importiert.
/// Muss VOR `Py_InitializeFromConfig` in die inittab (python.rs).
#[pymodule]
pub fn researchtranscript_motoren(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sondiere, m)?)?;
    m.add_function(wrap_pyfunction!(wav16k, m)?)?;
    m.add_function(wrap_pyfunction!(nach_mp3, m)?)?;
    m.add_function(wrap_pyfunction!(trenne, m)?)?;
    let d = PyDict::new(m.py());
    d.set_item("ton", "AVFoundation + libmp3lame")?;
    d.set_item("sprecher", "SpeakerKit (Core ML, Shim im Prozess)")?;
    m.add("UMSETZUNG", d)?;
    Ok(())
}
