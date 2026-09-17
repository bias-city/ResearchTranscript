//! Phase-0-Spike F2 (docs/appstore-plan.md §3): Medien ohne HTTP-Server.
//! Eigenes Schema `rtmedia://localhost/<schluessel>` mit Range-Antworten
//! nach dem Muster von Tauris asset-Protokoll: Blockdeckel 4 MB, bei einer
//! Anfrage OHNE Range nur der erste Block als 206. Der Schlüssel zeigt auf
//! einen Pfad, den ein Befehl vorher eingetragen hat — im Handler läuft
//! kein Python. Jede Anfrage wird protokolliert (Messpunkte F2).
use std::collections::HashMap;
use std::io::{Read, Seek, SeekFrom};
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::Instant;
use tauri::http::{header, Request, Response, StatusCode};
use tauri::Manager;

pub struct Medien(pub Mutex<HashMap<String, PathBuf>>);

const BLOCK: u64 = 4 * 1024 * 1024;

fn mime(p: &std::path::Path) -> &'static str {
    match p.extension().and_then(|e| e.to_str()).map(|e| e.to_ascii_lowercase()).as_deref() {
        Some("mp3") => "audio/mpeg",
        Some("wav") => "audio/wav",
        Some("m4a") => "audio/mp4",
        Some("aac") => "audio/aac",
        Some("flac") => "audio/flac",
        Some("ogg") => "audio/ogg",
        Some("mp4") | Some("m4v") => "video/mp4",
        Some("mov") => "video/quicktime",
        _ => "application/octet-stream",
    }
}

fn protokoll(zeile: &str) {
    println!("[rtmedia] {zeile}");
    if let Ok(home) = std::env::var("HOME") {
        use std::io::Write;
        if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(format!("{home}/spike.log")) {
            let _ = writeln!(f, "rtmedia {zeile}");
        }
    }
}

/// Pfad registrieren; gibt den Schlüssel für die URL zurück.
#[tauri::command]
pub fn spike_medien_registrieren(app: tauri::AppHandle, pfad: String) -> Result<String, String> {
    let p = PathBuf::from(&pfad);
    let laenge = std::fs::metadata(&p).map_err(|e| format!("{pfad}: {e}"))?.len();
    let schluessel = format!("m{}", app.state::<Medien>().0.lock().unwrap().len() + 1);
    app.state::<Medien>().0.lock().unwrap().insert(schluessel.clone(), p);
    protokoll(&format!("registriert {schluessel} → {pfad} ({laenge} Bytes)"));
    Ok(schluessel)
}

fn antwort(status: StatusCode, body: Vec<u8>, kopf: &[(&'static str, String)]) -> Response<Vec<u8>> {
    let mut b = Response::builder().status(status);
    for (k, v) in kopf { b = b.header(*k, v); }
    b.body(body).unwrap()
}

/// Handler für `rtmedia://localhost/<schluessel>`.
pub fn bedienen(app: &tauri::AppHandle, req: Request<Vec<u8>>) -> Response<Vec<u8>> {
    let t0 = Instant::now();
    let schluessel = req.uri().path().trim_start_matches('/').to_string();
    let pfad = app.state::<Medien>().0.lock().unwrap().get(&schluessel).cloned();
    let Some(pfad) = pfad else {
        protokoll(&format!("{schluessel}: unbekannt → 404"));
        return antwort(StatusCode::NOT_FOUND, Vec::new(), &[]);
    };
    let Ok(mut datei) = std::fs::File::open(&pfad) else {
        protokoll(&format!("{schluessel}: nicht lesbar → 403"));
        return antwort(StatusCode::FORBIDDEN, Vec::new(), &[]);
    };
    let gesamt = datei.metadata().map(|m| m.len()).unwrap_or(0);
    let range = req.headers().get(header::RANGE).and_then(|v| v.to_str().ok()).map(|s| s.to_string());
    // bytes=start-end | bytes=start- ; ohne Range: erster Block als 206
    let (start, ende) = match range.as_deref().and_then(|r| r.strip_prefix("bytes=")) {
        Some(r) => {
            let mut teile = r.splitn(2, '-');
            let s: u64 = teile.next().and_then(|x| x.parse().ok()).unwrap_or(0);
            let e: u64 = teile.next().and_then(|x| x.parse().ok()).unwrap_or(gesamt.saturating_sub(1));
            (s, e.min(gesamt.saturating_sub(1)))
        }
        None => (0, gesamt.saturating_sub(1)),
    };
    if start >= gesamt {
        return antwort(StatusCode::RANGE_NOT_SATISFIABLE, Vec::new(), &[("Content-Range", format!("bytes */{gesamt}"))]);
    }
    let ende = ende.min(start + BLOCK - 1);
    let laenge = ende - start + 1;
    let mut puffer = vec![0u8; laenge as usize];
    if datei.seek(SeekFrom::Start(start)).is_err() || datei.read_exact(&mut puffer).is_err() {
        protokoll(&format!("{schluessel}: Lesefehler bei {start}"));
        return antwort(StatusCode::INTERNAL_SERVER_ERROR, Vec::new(), &[]);
    }
    protokoll(&format!("{schluessel}: Range={} → 206 bytes {start}-{ende}/{gesamt} ({laenge} B, {:.1} ms)",
                       range.as_deref().unwrap_or("–"), t0.elapsed().as_secs_f64() * 1000.0));
    antwort(StatusCode::PARTIAL_CONTENT, puffer, &[
        ("Content-Type", mime(&pfad).to_string()),
        ("Accept-Ranges", "bytes".to_string()),
        ("Content-Range", format!("bytes {start}-{ende}/{gesamt}")),
        ("Content-Length", laenge.to_string()),
        ("Cache-Control", "no-store".to_string()),
        ("Access-Control-Allow-Origin", "*".to_string()),
    ])
}
