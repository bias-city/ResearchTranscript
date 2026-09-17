//! Probe für die C-Schnittstelle RTMotoren (include/rtmotoren.h).
//!
//!   probe sondiere <datei>
//!   probe wav16k <datei> <ziel.wav> [start dauer]
//!   probe mp3 <datei> <ziel.mp3>                  (RT_LAME_DYLIB, sonst Homebrew-Pfad; RT_VBR_Q, sonst 2)
//!   probe diarize <wav> <modelldir> [n] [aus.rttm]  (Schwelle RT_SCHWELLE, sonst 0.62; exclusive; RT_WIEDERHOLE=k)
//!   probe parallel <wav> <modelldir> <datei> <ziel.wav> [<datei2> <ziel2> …]
//!                                                  (Thread 0: diarize, Threads 1..k: wav16k, gleichzeitig)
//!   probe parallel-diarize <wav> <modelldir> <k>   (k Diarisierungen gleichzeitig)
//!
//! Abbruch: RT_ABBRUCH_NACH_S=<s> → der Abbruch-Callback liefert nach s Sekunden true.
//! Jeder Aufruf hat seinen eigenen ctx (Zustand): Startzeit, Fortschrittsfolge.

use std::ffi::{c_char, c_void, CStr, CString};
use std::io::Write;
use std::sync::Mutex;
use std::time::Instant;

type AbbruchCb = extern "C" fn(*mut c_void) -> bool;
type FortschrittCb = extern "C" fn(f64, *mut c_void);

extern "C" {
    fn rt_sondiere(pfad: *const c_char) -> *mut c_char;
    fn rt_dekodiere_wav16k(pfad: *const c_char, ziel: *const c_char, start_s: f64, dauer_s: f64,
                           abbruch: Option<AbbruchCb>, fortschritt: Option<FortschrittCb>, ctx: *mut c_void) -> *mut c_char;
    fn rt_nach_mp3(pfad: *const c_char, ziel: *const c_char, vbr_q: i32, lame_dylib: *const c_char,
                   abbruch: Option<AbbruchCb>, fortschritt: Option<FortschrittCb>, ctx: *mut c_void) -> *mut c_char;
    fn rt_diarize_wav(wav: *const c_char, num_speakers: i32, cluster_distance_threshold: f32, exclusive: bool,
                      model_dir: *const c_char, abbruch: Option<AbbruchCb>, fortschritt: Option<FortschrittCb>,
                      ctx: *mut c_void) -> *mut c_char;
    #[allow(dead_code)]
    fn rt_unload_models(model_dir: *const c_char);
    fn rt_free(p: *mut c_char);
}

struct Zustand {
    name: String,
    start: Instant,
    abbruch_nach_s: Option<f64>,
    fortschritt: Mutex<Vec<(f64, f64)>>, // (Sekunden seit Start, Anteil)
    abbruch_gemeldet: Mutex<Option<f64>>,
}

impl Zustand {
    fn neu(name: &str) -> Box<Zustand> {
        Box::new(Zustand {
            name: name.into(),
            start: Instant::now(),
            abbruch_nach_s: std::env::var("RT_ABBRUCH_NACH_S").ok().and_then(|s| s.parse().ok()),
            fortschritt: Mutex::new(Vec::new()),
            abbruch_gemeldet: Mutex::new(None),
        })
    }
}

extern "C" fn abbruch_cb(ctx: *mut c_void) -> bool {
    let z = unsafe { &*(ctx as *const Zustand) };
    match z.abbruch_nach_s {
        Some(s) if z.start.elapsed().as_secs_f64() >= s => {
            let mut g = z.abbruch_gemeldet.lock().unwrap();
            if g.is_none() { *g = Some(z.start.elapsed().as_secs_f64()); }
            true
        }
        _ => false,
    }
}

extern "C" fn fortschritt_cb(anteil: f64, ctx: *mut c_void) {
    let z = unsafe { &*(ctx as *const Zustand) };
    z.fortschritt.lock().unwrap().push((z.start.elapsed().as_secs_f64(), anteil));
}

fn nimm(p: *mut c_char) -> String {
    assert!(!p.is_null(), "rt_* gab NULL zurück");
    let s = unsafe { CStr::from_ptr(p) }.to_string_lossy().into_owned();
    unsafe { rt_free(p) };
    s
}

fn c(s: &str) -> CString { CString::new(s).unwrap() }

/// Ergebnis + Messung ausgeben; Rückgabe: (JSON, Fehler?)
fn bericht(z: &Zustand, json: &str) -> bool {
    let wall = z.start.elapsed().as_secs_f64();
    let f = z.fortschritt.lock().unwrap();
    let monoton = f.windows(2).all(|w| w[0].1 <= w[1].1);
    let fehler = serde_json::from_str::<serde_json::Value>(json).ok()
        .and_then(|v| v.get("error").and_then(|e| e.as_str()).map(|s| s.to_string()));
    eprintln!(
        "[{}] wall={:.3}s fortschritt: n={} erst={:?} letzt={:?} monoton={} abbruch_gemeldet_bei={:?} {}",
        z.name, wall, f.len(), f.first().map(|x| x.1), f.last().map(|x| x.1), monoton,
        *z.abbruch_gemeldet.lock().unwrap(),
        fehler.as_ref().map(|e| format!("FEHLER: {e}")).unwrap_or_default()
    );
    if std::env::var("RT_FORTSCHRITT_ALLE").is_ok() {
        eprintln!("[{}] folge: {:?}", z.name, f.iter().map(|(t, a)| format!("{t:.2}s:{a:.3}")).collect::<Vec<_>>());
    }
    fehler.is_some()
}

fn lame_dylib() -> String {
    std::env::var("RT_LAME_DYLIB").unwrap_or_else(|_| "/opt/homebrew/opt/lame/lib/libmp3lame.dylib".into())
}

fn wav16k(name: &str, datei: &str, ziel: &str, start: f64, dauer: f64) -> (String, bool) {
    let z = Zustand::neu(name);
    let ctx = &*z as *const Zustand as *mut c_void;
    let json = nimm(unsafe {
        rt_dekodiere_wav16k(c(datei).as_ptr(), c(ziel).as_ptr(), start, dauer, Some(abbruch_cb), Some(fortschritt_cb), ctx)
    });
    let fehler = bericht(&z, &json);
    (json, fehler)
}

fn diarize(name: &str, wav: &str, modelldir: &str, n: i32) -> (String, bool) {
    let schwelle: f32 = std::env::var("RT_SCHWELLE").ok().and_then(|s| s.parse().ok()).unwrap_or(0.62);
    let z = Zustand::neu(name);
    let ctx = &*z as *const Zustand as *mut c_void;
    let json = nimm(unsafe {
        rt_diarize_wav(c(wav).as_ptr(), n, schwelle, true, c(modelldir).as_ptr(), Some(abbruch_cb), Some(fortschritt_cb), ctx)
    });
    let fehler = bericht(&z, &json);
    (json, fehler)
}

#[derive(serde::Deserialize)]
struct Segment { start: f64, end: f64, speaker: String }
#[derive(serde::Deserialize)]
struct DiarizeErgebnis { segments: Vec<Segment>, speaker_count: usize, model_load_ms: f64, diarize_ms: f64 }

fn rttm(json: &str, file_id: &str) -> String {
    let r: DiarizeErgebnis = serde_json::from_str(json).expect("Diarize-JSON");
    eprintln!("segmente={} sprecher={} model_load={:.0}ms diarize={:.0}ms",
              r.segments.len(), r.speaker_count, r.model_load_ms, r.diarize_ms);
    let mut out = String::new();
    for s in &r.segments {
        out.push_str(&format!("SPEAKER {} 1 {:.3} {:.3} <NA> <NA> {} <NA> <NA>\n", file_id, s.start, s.end - s.start, s.speaker));
    }
    out
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let cmd = a.get(1).map(String::as_str).unwrap_or("");
    let mut fehler = false;
    match cmd {
        "sondiere" => {
            let z = Zustand::neu("sondiere");
            let json = nimm(unsafe { rt_sondiere(c(&a[2]).as_ptr()) });
            fehler = bericht(&z, &json);
            println!("{json}");
        }
        "wav16k" => {
            let start = a.get(4).map(|s| s.parse().unwrap()).unwrap_or(0.0);
            let dauer = a.get(5).map(|s| s.parse().unwrap()).unwrap_or(0.0);
            let (json, f) = wav16k("wav16k", &a[2], &a[3], start, dauer);
            fehler = f;
            println!("{json}");
        }
        "mp3" => {
            let q: i32 = std::env::var("RT_VBR_Q").ok().and_then(|s| s.parse().ok()).unwrap_or(2);
            let z = Zustand::neu("mp3");
            let ctx = &*z as *const Zustand as *mut c_void;
            let json = nimm(unsafe {
                rt_nach_mp3(c(&a[2]).as_ptr(), c(&a[3]).as_ptr(), q, c(&lame_dylib()).as_ptr(), Some(abbruch_cb), Some(fortschritt_cb), ctx)
            });
            fehler = bericht(&z, &json);
            println!("{json}");
        }
        "diarize" => {
            let n: i32 = a.get(4).map(|s| s.parse().unwrap()).unwrap_or(0);
            // RT_WIEDERHOLE=k: k Aufrufe im selben Prozess (Modelle bleiben warm), letzter zählt.
            let k: usize = std::env::var("RT_WIEDERHOLE").ok().and_then(|s| s.parse().ok()).unwrap_or(1);
            for _ in 1..k { diarize("diarize warm", &a[2], &a[3], n); }
            let (json, f) = diarize("diarize", &a[2], &a[3], n);
            fehler = f;
            if !f {
                let out = rttm(&json, "ton");
                match a.get(5) {
                    Some(p) => std::fs::write(p, out).unwrap(),
                    None => std::io::stdout().write_all(out.as_bytes()).unwrap(),
                }
            } else { println!("{json}"); }
        }
        "parallel" => {
            // Thread 0: diarize; Threads 1..k: wav16k — alle gleichzeitig.
            let wav = a[2].clone(); let modelldir = a[3].clone();
            let paare: Vec<(String, String)> = a[4..].chunks(2).map(|p| (p[0].clone(), p[1].clone())).collect();
            let t0 = Instant::now();
            let mut hs = Vec::new();
            hs.push(std::thread::spawn(move || { let (j, f) = diarize("T0 diarize", &wav, &modelldir, 0); if !f { print!("{}", rttm(&j, "ton")); } f }));
            for (i, (d, z)) in paare.into_iter().enumerate() {
                hs.push(std::thread::spawn(move || wav16k(&format!("T{} wav16k", i + 1), &d, &z, 0.0, 0.0).1));
            }
            for h in hs { fehler |= h.join().unwrap(); }
            eprintln!("parallel gesamt wall={:.3}s", t0.elapsed().as_secs_f64());
        }
        "parallel-diarize" => {
            let k: usize = a[4].parse().unwrap();
            let t0 = Instant::now();
            let hs: Vec<_> = (0..k).map(|i| { let wav = a[2].clone(); let m = a[3].clone();
                std::thread::spawn(move || { let (j, f) = diarize(&format!("T{i} diarize"), &wav, &m, 0); (j, f) }) }).collect();
            let mut jsons = Vec::new();
            for h in hs { let (j, f) = h.join().unwrap(); fehler |= f; jsons.push(j); }
            let segs = |j: &str| serde_json::from_str::<serde_json::Value>(j).ok().and_then(|v| v.get("segments").cloned());
            let gleich = jsons.windows(2).all(|w| segs(&w[0]) == segs(&w[1]));
            eprintln!("parallel-diarize k={k} gesamt wall={:.3}s segmente identisch={gleich}", t0.elapsed().as_secs_f64());
            if !fehler { print!("{}", rttm(&jsons[0], "ton")); }
        }
        _ => { eprintln!("Unterbefehl: sondiere | wav16k | mp3 | diarize | parallel | parallel-diarize"); std::process::exit(64); }
    }
    std::process::exit(if fehler { 2 } else { 0 });
}
