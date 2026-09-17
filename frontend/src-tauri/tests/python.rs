//! Integrationstest (Plan 1.15): die gebündelte Laufzeit aus
//! `resources/` im Testprozess starten und die Fassade rufen — genau
//! der Weg der Hülle, ohne Fenster. Braucht `node
//! scripts/bundle-resources.mjs` (python-runtime + python/site-packages)
//! und PYO3_CONFIG_FILE beim Bauen; fehlt beides, wird übersprungen.
use std::path::PathBuf;

use researchtranscript_app_lib::python;

#[test]
fn fassade_im_prozess() {
    let res = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources");
    if !res.join("python-runtime/lib/libpython3.13.dylib").is_file() {
        eprintln!("übersprungen: resources/python-runtime fehlt");
        return;
    }
    let scratch = std::env::temp_dir().join(format!("rt-test-{}", std::process::id()));
    std::env::set_var("LT_CONFIG_DIR", &scratch);
    let ms = python::init_pfad(&res, None).expect("Interpreter startet");
    assert!(ms < 5000.0, "Start dauerte {ms} ms");

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

    let p = python::selbstpruefung(&res);
    assert!(p.iter().all(|x| x.contains("argmax") || x.contains("fehlt in den Ressourcen")), "{p:?}");
    let _ = std::fs::remove_dir_all(&scratch);
}

/// Mit Feature `motoren`: das Rust-Modul ist importierbar, und die
/// Sondierung liest die Demo-Aufnahme (mp3, kein Video).
#[cfg(feature = "motoren")]
#[test]
fn motoren_modul_im_prozess() {
    let res = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("resources");
    if !res.join("python-runtime/lib/libpython3.13.dylib").is_file() { return; }
    std::env::set_var("LT_CONFIG_DIR", std::env::temp_dir().join(format!("rt-test-m-{}", std::process::id())));
    python::init_pfad(&res, None).expect("Interpreter startet");
    let demo = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../docs/demo/housing-cooperatives-interview.mp3");
    let aus = pyo3::Python::attach(|py| -> pyo3::PyResult<String> {
        let m = py.import("researchtranscript_motoren")?;
        let info = m.getattr("sondiere")?.call1((demo.to_string_lossy().as_ref(),))?;
        Ok(info.str()?.to_string())
    }).expect("sondiere");
    assert!(aus.contains("'audio_codec': 'mp3'"), "{aus}");
    assert!(aus.contains("'video_codec': None"), "{aus}");
}
