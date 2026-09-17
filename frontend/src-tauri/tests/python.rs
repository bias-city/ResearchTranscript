//! Integrationstests (Plan 1.15): die gebündelte Laufzeit aus `resources/`
//! im Testprozess starten und die Fassade rufen — genau der Weg der
//! Hülle, ohne Fenster. Braucht `node scripts/bundle-resources.mjs` und
//! PYO3_CONFIG_FILE beim Bauen; fehlt beides, wird übersprungen.
//!
//! Ein Interpreter je Prozess, `os.environ` ist ein Schnappschuss vom
//! Start: LT_CONFIG_DIR und LT_MOTOR werden EINMAL vor dem ersten Start
//! gesetzt (`start()`), alle Tests teilen sich den Scratch-Ordner und
//! räumen ihn nicht weg. Mit `--features motoren` läuft alles über den
//! Prozess-Motor (LT_MOTOR=prozess).
use std::path::PathBuf;
use std::sync::OnceLock;

use researchtranscript_app_lib::python;
#[cfg(feature = "motoren")]
use pyo3::prelude::*;

static SCRATCH: OnceLock<Option<PathBuf>> = OnceLock::new();

fn resources() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources")
}

fn demo() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../docs/demo/housing-cooperatives-interview.mp3")
}

/// Einmaliger Start; None, wenn die Ressourcen fehlen (Test überspringt).
fn start() -> Option<PathBuf> {
    SCRATCH.get_or_init(|| {
        let res = resources();
        if !res.join("python-runtime/lib/libpython3.13.dylib").is_file() {
            eprintln!("übersprungen: resources/python-runtime fehlt");
            return None;
        }
        let scratch = std::env::temp_dir().join(format!("rt-test-{}", std::process::id()));
        std::fs::create_dir_all(scratch.join("lib")).unwrap();
        std::env::set_var("LT_CONFIG_DIR", scratch.join("cfg"));
        if cfg!(feature = "motoren") { std::env::set_var("LT_MOTOR", "prozess"); }
        let ms = python::init_pfad(&res, None).expect("Interpreter startet");
        assert!(ms < 5000.0, "Start dauerte {ms} ms");
        python::rufe("settings_post", &serde_json::json!({"aend": {"library_root": scratch.join("lib").to_string_lossy()}})).unwrap();
        Some(scratch)
    }).clone()
}

#[test]
fn fassade_im_prozess() {
    let Some(_) = start() else { return };
    let h = python::rufe("health", &serde_json::json!({})).expect("health");
    assert_eq!(h["status"], "ok");
    assert_eq!(h["version"], env!("CARGO_PKG_VERSION"));
    assert_eq!(python::rufe("ping", &serde_json::json!({})).unwrap()["pong"], true);

    // Fehlerform: unbekannter Befehl → 404, falsche Argumente → 422
    let e = python::rufe("gibt_es_nicht", &serde_json::json!({})).unwrap_err();
    assert_eq!(e.status, 404);
    let e = python::rufe("job_get", &serde_json::json!({"falsch": 1})).unwrap_err();
    assert_eq!(e.status, 422);

    // Umlaute durch den ganzen Weg (UTF-8-Modus, Befund 3)
    let s = python::rufe("settings_post", &serde_json::json!({"aend": {"user_email": "ü@bias.city"}})).unwrap();
    assert_eq!(s["user_email"], "ü@bias.city");

    let p = python::selbstpruefung(&resources());
    assert!(p.iter().all(|x| x.contains("argmax") || x.contains("fehlt in den Ressourcen")), "{p:?}");
}

/// Mit Feature `motoren`: das Rust-Modul ist importierbar, sondiert die
/// Demo (mp3, kein Video), dekodiert 10 s nach 16 kHz mit Fortschritt und
/// kodiert mp3 über die gebündelte LAME.
#[cfg(feature = "motoren")]
#[test]
fn motoren_modul_im_prozess() {
    let Some(scratch) = start() else { return };
    let demo = demo();
    let tmp = scratch.join("motoren");
    std::fs::create_dir_all(&tmp).unwrap();
    let (wav, mp3) = (tmp.join("a.wav"), tmp.join("a.mp3"));
    let (info, samples, bytes) = pyo3::Python::attach(|py| -> pyo3::PyResult<(String, i64, i64)> {
        let m = py.import("researchtranscript_motoren")?;
        let ns = pyo3::types::PyDict::new(py);
        ns.set_item("m", &m)?;
        ns.set_item("wav", wav.to_string_lossy().as_ref())?;
        ns.set_item("mp3", mp3.to_string_lossy().as_ref())?;
        ns.set_item("demo", demo.to_string_lossy().as_ref())?;
        py.run(c"
info = m.sondiere(demo)
schritte = []
r1 = m.wav16k(demo, wav, 0.0, 10.0, abbruch=lambda: False, fortschritt=schritte.append)
assert schritte and schritte[-1] == 1.0 and all(a <= b for a, b in zip(schritte, schritte[1:])), schritte
r2 = m.nach_mp3(demo, mp3, 2)
", Some(&ns), None)?;
        let info = ns.get_item("info")?.unwrap().str()?.to_string();
        let r1 = ns.get_item("r1")?.unwrap();
        let r2 = ns.get_item("r2")?.unwrap();
        Ok((info, r1.get_item("samples")?.extract()?, r2.get_item("bytes")?.extract()?))
    }).expect("motoren");
    assert!(info.contains("'audio_codec': 'mp3'"), "{info}");
    assert!(info.contains("'video_codec': None"), "{info}");
    assert_eq!(samples, 160_000, "10 s bei 16 kHz");
    assert!(bytes > 100_000, "mp3 {bytes} Bytes");
    assert_eq!(std::fs::metadata(&mp3).unwrap().len() as i64, bytes);
}

/// Ganzer Job im Prozess-Motor: Demo dekodieren (AVFoundation), trennen
/// (SpeakerKit-Shim), transkribieren (whisper-cli als Kind) — bis zum
/// Bibliothekseintrag. Braucht resources/bin/whisper-cli und
/// resources/models; ~30 s.
#[cfg(feature = "motoren")]
#[test]
fn job_im_prozess_motor() {
    let Some(_) = start() else { return };
    let res = resources();
    if !res.join("bin/whisper-cli").is_file() || !res.join("models").is_dir() { return; }
    let j = python::rufe("transcribe_path", &serde_json::json!({"args": {"path": demo().to_string_lossy(), "speaker_range": "2-2"}})).expect("start");
    let jid = j["job_id"].as_str().unwrap().to_string();
    let t0 = std::time::Instant::now();
    let mut job = serde_json::Value::Null;
    while t0.elapsed().as_secs() < 240 {
        job = python::rufe("job_get", &serde_json::json!({"job_id": jid})).unwrap();
        if ["completed", "failed", "cancelled"].contains(&job["status"].as_str().unwrap_or("")) { break; }
        std::thread::sleep(std::time::Duration::from_millis(500));
    }
    assert_eq!(job["status"], "completed", "{job}");
    let eid = job["eintrag"].as_str().unwrap();
    let d = python::rufe("transcript_get", &serde_json::json!({"eid": eid})).unwrap();
    let n = d["segmente"].as_array().unwrap().len();
    let s = d["sprecher"].as_array().unwrap().len();
    // Kind-Motor an derselben Datei: 33 Segmente, 2 Sprecher (Dev-Server 17.9.)
    assert_eq!(s, 2, "{n} Segmente, {s} Sprecher");
    assert!((28..=38).contains(&n), "{n} Segmente");
    assert_eq!(d["audio"], "audio.mp3");
    eprintln!("Prozess-Motor: {n} Segmente, {s} Sprecher in {:.0} s", t0.elapsed().as_secs_f64());
}
