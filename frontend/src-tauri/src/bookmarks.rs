//! Security-scoped Bookmarks (Plan §6, «Bookmarks im Prozess»).
//!
//! In der Sandbox sieht die App nur, was die Person per Dialog oder Drop
//! freigegeben hat — und das nur bis zum Ende der Sitzung. Ein Bookmark
//! macht die Freigabe dauerhaft: beim nächsten Start wird es aufgelöst,
//! `startAccessingSecurityScopedResource` erweitert die Sandbox des
//! Prozesses — für Python, Core ML, AVFoundation und das Whisper-Kind
//! (`inherit`) gleichermassen. Ordner-Freigaben gelten rekursiv.
//!
//! Gemerkt werden nur Ordner (Bibliothek, Zotero); Ablage als Base64 in
//! `<config>/bookmarks.json` neben Pythons `config.json`. Ein Start/Stop-
//! Paar je Ordner und Sitzung: die aufgelösten NSURLs bleiben bis zum
//! Prozessende am Leben (kein Stop — die Sandbox-Erweiterung soll die
//! ganze Sitzung halten). Ohne Sandbox ist alles hier ein No-op mit
//! demselben Ergebnis: der Pfad ist erreichbar.
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::Mutex;

use objc2::rc::Retained;
use objc2_foundation::{NSData, NSString, NSURL, NSURLBookmarkCreationOptions, NSURLBookmarkResolutionOptions};

use crate::protokoll;

/// Aufgelöste URLs — leben, damit der Zugriff bestehen bleibt.
static OFFEN: Mutex<Vec<Retained<NSURL>>> = Mutex::new(Vec::new());

pub fn datei() -> PathBuf {
    if let Some(d) = std::env::var_os("LT_CONFIG_DIR") {
        return PathBuf::from(d).join("bookmarks.json");
    }
    let home = std::env::var_os("HOME").map(PathBuf::from).unwrap_or_else(|| PathBuf::from("/"));
    home.join("Library/Application Support/ResearchTranscript/bookmarks.json")
}

fn lese() -> BTreeMap<String, String> {
    std::fs::read_to_string(datei()).ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or_default()
}

fn schreibe(m: &BTreeMap<String, String>) -> Result<(), String> {
    let d = datei();
    if let Some(p) = d.parent() { std::fs::create_dir_all(p).map_err(|e| e.to_string())?; }
    let tmp = d.with_extension("tmp");
    std::fs::write(&tmp, serde_json::to_string_pretty(m).map_err(|e| e.to_string())?).map_err(|e| e.to_string())?;
    std::fs::rename(&tmp, &d).map_err(|e| e.to_string())
}

fn base64(bytes: &[u8]) -> String {
    const T: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut aus = String::with_capacity((bytes.len() + 2) / 3 * 4);
    for chunk in bytes.chunks(3) {
        let b = [chunk[0], *chunk.get(1).unwrap_or(&0), *chunk.get(2).unwrap_or(&0)];
        let n = (b[0] as u32) << 16 | (b[1] as u32) << 8 | b[2] as u32;
        aus.push(T[(n >> 18) as usize & 63] as char);
        aus.push(T[(n >> 12) as usize & 63] as char);
        aus.push(if chunk.len() > 1 { T[(n >> 6) as usize & 63] as char } else { '=' });
        aus.push(if chunk.len() > 2 { T[n as usize & 63] as char } else { '=' });
    }
    aus
}

fn unbase64(s: &str) -> Option<Vec<u8>> {
    let wert = |c: u8| -> Option<u32> {
        Some(match c { b'A'..=b'Z' => c - b'A', b'a'..=b'z' => c - b'a' + 26, b'0'..=b'9' => c - b'0' + 52, b'+' => 62, b'/' => 63, _ => return None } as u32)
    };
    let s: Vec<u8> = s.bytes().filter(|c| *c != b'=' && !c.is_ascii_whitespace()).collect();
    let mut aus = Vec::with_capacity(s.len() * 3 / 4);
    for chunk in s.chunks(4) {
        let mut n = 0u32;
        for (i, c) in chunk.iter().enumerate() { n |= wert(*c)? << (18 - 6 * i); }
        aus.push((n >> 16) as u8);
        if chunk.len() > 2 { aus.push((n >> 8) as u8); }
        if chunk.len() > 3 { aus.push(n as u8); }
    }
    Some(aus)
}

/// Bookmark für einen (gerade per Dialog freigegebenen) Ordner anlegen
/// und merken. Ausserhalb der Sandbox liefert macOS ebenfalls ein
/// Bookmark — harmlos.
pub fn merken(pfad: &Path) -> Result<(), String> {
    let url = NSURL::fileURLWithPath(&NSString::from_str(&pfad.to_string_lossy()));
    let daten = url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error(
            NSURLBookmarkCreationOptions::WithSecurityScope, None, None)
        .map_err(|e| format!("Bookmark: {e}"))?;
    let bytes = daten.to_vec();
    let mut m = lese();
    m.insert(pfad.to_string_lossy().into_owned(), base64(&bytes));
    schreibe(&m)?;
    protokoll::schreibe("bookmark", &format!("gemerkt: {} ({} Bytes)", pfad.display(), bytes.len()));
    Ok(())
}

/// Beim Start: alle gemerkten Ordner wieder freigeben. Liefert die
/// erreichbaren Pfade; veraltete Einträge (Ordner weg) fallen raus.
pub fn wiederherstellen() -> Vec<PathBuf> {
    let m = lese();
    let mut ok = Vec::new();
    let mut neu = BTreeMap::new();
    for (pfad, b64) in &m {
        let Some(bytes) = unbase64(b64) else { continue };
        let daten = NSData::with_bytes(&bytes);
        let mut veraltet = objc2::runtime::Bool::NO;
        let r = unsafe {
            NSURL::URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error(
                &daten, NSURLBookmarkResolutionOptions::WithSecurityScope, None, &mut veraltet)
        };
        match r {
            Ok(url) => {
                let zugriff = unsafe { url.startAccessingSecurityScopedResource() };
                let echt = url.path().map(|p| p.to_string()).unwrap_or_else(|| pfad.clone());
                protokoll::schreibe("bookmark", &format!("{echt}: Zugriff {}{}", if zugriff { "ja" } else { "nein" }, if veraltet.as_bool() { ", veraltet" } else { "" }));
                if veraltet.as_bool() {
                    // neu erzeugen, solange der Zugriff besteht
                    if let Ok(d) = url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error(NSURLBookmarkCreationOptions::WithSecurityScope, None, None) {
                        neu.insert(echt.clone(), base64(&d.to_vec()));
                    } else { neu.insert(pfad.clone(), b64.clone()); }
                } else {
                    neu.insert(pfad.clone(), b64.clone());
                }
                ok.push(PathBuf::from(echt));
                OFFEN.lock().unwrap().push(url);
            }
            Err(e) => protokoll::schreibe("bookmark", &format!("{pfad}: nicht auflösbar ({e}) — vergessen")),
        }
    }
    if neu != m { let _ = schreibe(&neu); }
    ok
}

/// Läuft die App in der Sandbox? (Container-Kennung setzt macOS.)
pub fn sandboxed() -> bool {
    std::env::var_os("APP_SANDBOX_CONTAINER_ID").is_some()
}

/// Das echte Home der Person — in der Sandbox ist `HOME` der Container;
/// den Dialog wollen wir trotzdem in ~/Documents öffnen.
pub fn echtes_home() -> PathBuf {
    unsafe {
        let pw = libc::getpwuid(libc::getuid());
        if !pw.is_null() && !(*pw).pw_dir.is_null() {
            if let Ok(s) = std::ffi::CStr::from_ptr((*pw).pw_dir).to_str() { return PathBuf::from(s); }
        }
    }
    std::env::var_os("HOME").map(PathBuf::from).unwrap_or_else(|| PathBuf::from("/"))
}
