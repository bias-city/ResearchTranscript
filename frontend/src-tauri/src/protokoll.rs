//! Rotierendes Protokoll der Hülle (Plan R3): Python-stdout/stderr,
//! Rust-Panics, Herzschlag und Startfehler landen in EINER Datei unter
//! `~/Library/Logs/city.bias.researchtranscript/researchtranscript.log`
//! (in der Sandbox im Container). Zwei Generationen à 1 MB — genug für
//! eine Fehlermeldung samt Vorgeschichte, klein genug zum Mitschicken.
use std::io::Write;
use std::path::PathBuf;
use std::sync::{Mutex, OnceLock};

const MAX_BYTES: u64 = 1_000_000;
static DATEI: OnceLock<Mutex<PathBuf>> = OnceLock::new();

pub fn einrichten(ordner: PathBuf) -> PathBuf {
    let _ = std::fs::create_dir_all(&ordner);
    let pfad = ordner.join("researchtranscript.log");
    let _ = DATEI.set(Mutex::new(pfad.clone()));
    pfad
}

pub fn pfad() -> Option<PathBuf> {
    DATEI.get().and_then(|m| m.lock().ok()).map(|p| p.clone())
}

fn zeitstempel() -> String {
    // Ohne chrono: Sekunden seit Start reichen nicht, ein Datum schon —
    // `date`-Format aus der Systemzeit, UTC, ohne Bibliothek.
    let s = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let (tage, rest) = (s / 86_400, s % 86_400);
    // Zivilkalender aus Tagen seit 1970 (Howard Hinnant, days_from_civil⁻¹)
    let z = tage as i64 + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    format!("{y:04}-{m:02}-{d:02} {:02}:{:02}:{:02}Z", rest / 3600, rest % 3600 / 60, rest % 60)
}

/// Eine Zeile anhängen; `quelle` ist ein kurzes Kürzel (py, rust, herz …).
pub fn schreibe(quelle: &str, text: &str) {
    let zeile = format!("{} [{quelle}] {}", zeitstempel(), text.trim_end());
    #[cfg(debug_assertions)]
    eprintln!("{zeile}");
    let Some(m) = DATEI.get() else { return };
    let Ok(pfad) = m.lock() else { return };
    if let Ok(meta) = std::fs::metadata(&*pfad) {
        if meta.len() > MAX_BYTES {
            let alt = pfad.with_extension("log.1");
            let _ = std::fs::rename(&*pfad, alt);
        }
    }
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(&*pfad) {
        let _ = writeln!(f, "{zeile}");
    }
}

/// Rust-Panics ebenfalls ins Protokoll — ein Absturz ohne Zeile wäre
/// für Nutzerrückmeldungen blind.
pub fn panics_fangen() {
    let vorher = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        schreibe("panic", &format!("{info}"));
        vorher(info);
    }));
}
