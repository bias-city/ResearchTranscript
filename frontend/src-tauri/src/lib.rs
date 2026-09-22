// ResearchTranscript-Hülle (Variante A, Plan §4): Python läuft IM Prozess
// (python.rs), die Oberfläche ruft `api(name, args)` statt HTTP. Kein
// Port, keine Merkdatei, kein Kindprozess `python3` — die ganze
// Prozessverwaltung von 0.4.0 (uvicorn, lsof, ps, kill, venv_fixen) ist
// weg. Kindprozesse bleiben nur die Motoren (whisper-cli, ffmpeg,
// argmax-cli), und die verwaltet jobs.py.
//
// Was die Hülle noch tut: Fenster, Menü, Dialoge, Dateien vom Finder,
// Medien-Freigabe für `asset://`, Herzschlag (R4), Protokoll (R3),
// Start-Selbstprüfung (R5).
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::Duration;

use tauri::{Emitter, Manager, RunEvent};

pub mod bookmarks;
#[cfg(feature = "motoren")]
pub mod motoren;
pub mod protokoll;
pub mod python;

/// Pfade, die macOS zum Öffnen gab (Info.plist: .enrich) — gesammelt,
/// bis das Frontend sie abholt; beim Start per Doppelklick kommt das
/// Ereignis, bevor ein Listener steht.
struct Geoeffnet(Mutex<Vec<String>>);

#[tauri::command]
fn geoeffnete_dateien(state: tauri::State<'_, Geoeffnet>) -> Vec<String> {
    state.0.lock().map(|mut g| std::mem::take(&mut *g)).unwrap_or_default()
}

/// Adressen, die die Oberfläche dem System übergeben darf. Alles andere gilt als
/// Dateipfad. Die Liste ist eng, weil der Opener die Adresse an LaunchServices
/// weiterreicht (über `/usr/bin/open`): ein offener Öffner beliebiger Schemata ist
/// genau das, was App Review unter 2.5.2 als Installationsweg liest — die Ablehnung
/// von 0.6.0 nannte `itms-services://`. `zotero://` braucht der Editor, um einen
/// Eintrag in Zotero zu zeigen.
const ERLAUBTE_SCHEMATA: [&str; 4] = ["http://", "https://", "mailto:", "zotero://"];

/// Endungen, die als Dokument geöffnet werden dürfen. Alles andere — besonders
/// `.app`, `.pkg`, `.command`, `.sh`, `.scpt` — wird nur im Finder gezeigt. So kann
/// über diesen Weg nie ein Programm starten, auch wenn ein Pfad aus der Oberfläche
/// je manipuliert würde.
const ERLAUBTE_ENDUNGEN: [&str; 10] = ["md", "txt", "log", "json", "csv", "vtt", "srt", "pdf", "docx", "qdpx"];

/// Ordner im Finder zeigen, ein Dokument öffnen oder eine erlaubte Adresse aufrufen.
/// Der Opener reicht das an LaunchServices weiter (dafür startet er `/usr/bin/open`
/// als losgelöstes Kind, in der Sandbox zulässig). Drei Fälle, in dieser Reihenfolge:
/// erlaubtes Schema → öffnen; Verzeichnis → öffnen; Datei → nur bei bekannter,
/// nicht ausführbarer Endung öffnen, sonst im Finder zeigen.
#[tauri::command]
fn ordner_oeffnen(pfad: String) -> Result<(), String> {
    if ERLAUBTE_SCHEMATA.iter().any(|s| pfad.starts_with(s)) {
        return tauri_plugin_opener::open_url(&pfad, None::<&str>).map_err(|e| e.to_string());
    }
    // Ein Pfad, keine Adresse: alles mit «schema:» davor lehnen wir ab, statt es
    // dem System zu reichen.
    if let Some(i) = pfad.find(':') {
        if i > 1 && !pfad.starts_with('/') && pfad[..i].chars().all(|c| c.is_ascii_alphanumeric() || c == '+' || c == '-' || c == '.') {
            return Err(format!("Adressschema nicht erlaubt: {}", &pfad[..i]));
        }
    }
    let p = PathBuf::from(&pfad);
    if p.is_dir() {
        return tauri_plugin_opener::open_path(&pfad, None::<&str>).map_err(|e| e.to_string());
    }
    let endung = p.extension().map(|e| e.to_string_lossy().to_lowercase()).unwrap_or_default();
    if ERLAUBTE_ENDUNGEN.contains(&endung.as_str()) {
        return tauri_plugin_opener::open_path(&pfad, None::<&str>).map_err(|e| e.to_string());
    }
    tauri_plugin_opener::reveal_item_in_dir(&pfad).map_err(|e| e.to_string())
}

/// DER Befehl: Name + Argumente an die Python-Fassade. Immer async →
/// spawn_blocking, nie auf dem Hauptthread (python.rs-Kopf).
#[tauri::command]
async fn api(name: String, args: Option<serde_json::Value>) -> Result<serde_json::Value, python::ApiFehler> {
    let args = args.unwrap_or(serde_json::Value::Object(Default::default()));
    let t0 = std::time::Instant::now();
    let r = tauri::async_runtime::spawn_blocking({ let name = name.clone(); move || python::rufe(&name, &args) })
        .await
        .map_err(|e| python::ApiFehler { status: 500, detail: format!("Befehl abgebrochen: {e}") })?;
    // Eine Zeile je Befehl (R3): was die Oberfläche wollte, was sie bekam
    let ms = t0.elapsed().as_secs_f64() * 1000.0;
    match &r {
        Ok(_) => protokoll::schreibe("api", &format!("{name} ok {ms:.1} ms")),
        Err(e) => protokoll::schreibe("api", &format!("{name} {} «{}» {ms:.1} ms", e.status, e.detail)),
    }
    r
}

/// Hörprobe: rohe WAV-Bytes über den IPC (Frontend macht eine Blob-URL).
#[tauri::command]
async fn sprecher_probe(eid: String, sid: String) -> Result<tauri::ipc::Response, python::ApiFehler> {
    let bytes = tauri::async_runtime::spawn_blocking(move || python::sprecher_probe(&eid, &sid))
        .await
        .map_err(|e| python::ApiFehler { status: 500, detail: format!("Befehl abgebrochen: {e}") })??;
    Ok(tauri::ipc::Response::new(bytes))
}

/// Medien für `asset://` freigeben — je Datei, erst wenn die Oberfläche
/// sie braucht (kein Pauschal-Scope über die Platte). Liefert den Pfad,
/// das Frontend macht `convertFileSrc` daraus.
#[tauri::command]
async fn medien_pfad(app: tauri::AppHandle, eid: String, art: String) -> Result<serde_json::Value, python::ApiFehler> {
    let befehl = if art == "video" { "video_pfad" } else { "audio_pfad" };
    let v = api(befehl.to_string(), Some(serde_json::json!({ "eid": eid }))).await?;
    if let Some(p) = v.get("path").and_then(|p| p.as_str()) {
        app.asset_protocol_scope().allow_file(Path::new(p))
            .map_err(|e| python::ApiFehler { status: 500, detail: format!("Freigabe: {e}") })?;
    }
    Ok(v)
}

/// Ein per Dialog freigegebener Ordner (Bibliothek, Zotero) bleibt über
/// den Neustart hinaus erreichbar (Bookmark) und ist für asset:// offen.
#[tauri::command]
fn ordner_merken(app: tauri::AppHandle, pfad: String) -> Result<(), String> {
    let p = Path::new(&pfad);
    bookmarks::merken(p)?;
    app.asset_protocol_scope().allow_directory(p, true).map_err(|e| e.to_string())
}

/// Vorschlag für den Bibliotheksordner: das ECHTE ~/Documents der Person
/// (in der Sandbox wäre `HOME` der unsichtbare Container).
#[tauri::command]
fn standard_ordner() -> String {
    bookmarks::echtes_home().join("Documents").to_string_lossy().into_owned()
}

#[tauri::command]
fn ist_sandboxed() -> bool { bookmarks::sandboxed() }

/// Vertriebskanal dieses Builds: "mas" (Mac App Store) oder "dmg".
#[tauri::command]
fn kanal() -> &'static str { if cfg!(feature = "mas") { "mas" } else { "dmg" } }

/// Die Drittanbieter-Lizenzliste (THIRD_PARTY_LICENSES.md) — im Bundle
/// unter Resources/licenses, im Checkout an der Repo-Wurzel.
#[tauri::command]
fn lizenzen_pfad(app: tauri::AppHandle) -> Option<String> {
    let mut kandidaten = Vec::new();
    if let Ok(r) = app.path().resource_dir() { kandidaten.push(r.join("licenses/THIRD_PARTY_LICENSES.md")); }
    kandidaten.push(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../THIRD_PARTY_LICENSES.md"));
    kandidaten.into_iter().find(|p| p.is_file()).map(|p| p.to_string_lossy().into_owned())
}

#[tauri::command]
fn protokoll_pfad() -> Option<String> {
    protokoll::pfad().map(|p| p.to_string_lossy().into_owned())
}

#[tauri::command]
fn neustart(app: tauri::AppHandle) {
    protokoll::schreibe("hülle", "Neustart auf Wunsch der Oberfläche");
    python::alle_abbrechen();
    app.restart();
}

/// Herzschlag (Plan R4): alle 5 s ein `ping` an die Fassade auf einem
/// eigenen Thread; bleibt die Antwort 10 s aus, hält jemand den GIL —
/// heilen kann das niemand, aber die Oberfläche zeigt es und bietet
/// den Neustart an.
fn herzschlag(app: tauri::AppHandle) {
    std::thread::Builder::new().name("herzschlag".into()).spawn(move || {
        let mut gemeldet = false;
        loop {
            std::thread::sleep(Duration::from_secs(5));
            let (tx, rx) = std::sync::mpsc::channel();
            std::thread::spawn(move || {
                let _ = tx.send(python::rufe("ping", &serde_json::json!({})).is_ok());
            });
            match rx.recv_timeout(Duration::from_secs(10)) {
                Ok(true) => {
                    if gemeldet {
                        protokoll::schreibe("herz", "Python antwortet wieder");
                        let _ = app.emit("blockiert", false);
                        gemeldet = false;
                    }
                }
                Ok(false) => protokoll::schreibe("herz", "ping mit Fehler"),
                Err(_) => {
                    if !gemeldet {
                        protokoll::schreibe("herz", "Python antwortet seit 10 s nicht (GIL blockiert?)");
                        let _ = app.emit("blockiert", true);
                        gemeldet = true;
                    }
                }
            }
        }
    }).ok();
}

/// Nur das Nötige (User 2026-09-09): das Standardmenü schleppte File,
/// View, Help und ein Services-Untermenü mit — leer oder mit fremden
/// Entwickler-Werkzeugen gefüllt. Bleiben: „Über/Ausblenden/Beenden",
/// die Textbefehle (die App ist ein Editor — ⌘Z/⌘X/⌘C/⌘V sind Pflicht)
/// und die Fensterbefehle. Beschriftungen kommen von macOS und folgen
/// Englisch wie die vordefinierten Einträge (About/Hide/Quit,
/// Undo/Cut/Copy liefert muda auf Englisch) — deutsche
/// Untermenü-Titel daneben wären ein Sprachmischmasch. Das
/// Menü folgt damit NICHT der Oberflächensprache der App.
fn menue(handle: &tauri::AppHandle) -> tauri::Result<tauri::menu::Menu<tauri::Wry>> {
    use tauri::menu::{Menu, MenuItem, PredefinedMenuItem, Submenu};
    // EIGENER Über-Eintrag statt PredefinedMenuItem::about: das
    // macOS-Standardpanel zeigt nur Name, Version und Credits —
    // license/website/comments aus AboutMetadata fallen dort unter den
    // Tisch, und Links darin wären nicht anklickbar. Der Eintrag
    // schickt ein Ereignis ans Frontend, das seinen eigenen Dialog
    // öffnet: übersetzt, mit klickbaren Quellen (User 2026-09-09).
    let app = Submenu::with_items(
        handle,
        "ResearchTranscript",
        true,
        &[
            &MenuItem::with_id(handle, "ueber", "About ResearchTranscript",
                               true, None::<&str>)?,
            &PredefinedMenuItem::separator(handle)?,
            &PredefinedMenuItem::hide(handle, None)?,
            &PredefinedMenuItem::separator(handle)?,
            &PredefinedMenuItem::quit(handle, None)?,
        ],
    )?;
    let text = Submenu::with_items(
        handle,
        "Edit",
        true,
        &[
            &PredefinedMenuItem::undo(handle, None)?,
            &PredefinedMenuItem::redo(handle, None)?,
            &PredefinedMenuItem::separator(handle)?,
            &PredefinedMenuItem::cut(handle, None)?,
            &PredefinedMenuItem::copy(handle, None)?,
            &PredefinedMenuItem::paste(handle, None)?,
            &PredefinedMenuItem::select_all(handle, None)?,
        ],
    )?;
    let fenster = Submenu::with_items(
        handle,
        "Window",
        true,
        &[
            &PredefinedMenuItem::minimize(handle, None)?,
            &PredefinedMenuItem::fullscreen(handle, None)?,
            &PredefinedMenuItem::separator(handle)?,
            &PredefinedMenuItem::close_window(handle, None)?,
        ],
    )?;
    // Hilfe (User 2026-09-18): eigenes Fenster mit dem durchsuchbaren
    // Handbuch. Als Hilfemenü angemeldet, zeigt macOS darin sein Suchfeld
    // für Menübefehle. Das Kürzel ⌘? ist Kür — scheitert es, dann ohne.
    let eintrag = MenuItem::with_id(handle, "hilfe", "ResearchTranscript Help",
                                    true, Some("Cmd+Shift+/"))
        .or_else(|_| MenuItem::with_id(handle, "hilfe", "ResearchTranscript Help",
                                       true, None::<&str>))?;
    let hilfe = Submenu::with_items(handle, "Help", true, &[&eintrag])?;
    let menu = Menu::with_items(handle, &[&app, &text, &fenster, &hilfe])?;
    #[cfg(target_os = "macos")]
    let _ = hilfe.set_as_help_menu_for_nsapp();
    Ok(menu)
}

/// Hilfefenster öffnen oder nach vorn holen. Dieselbe Oberfläche
/// (index.html), die Marke «#hilfe» schaltet sie aufs Handbuch.
fn hilfe_fenster(handle: &tauri::AppHandle) {
    if let Some(w) = handle.get_webview_window("hilfe") {
        let _ = w.unminimize();
        let _ = w.set_focus();
        return;
    }
    let r = tauri::WebviewWindowBuilder::new(
        handle, "hilfe", tauri::WebviewUrl::App("index.html#hilfe".into()))
        .title("ResearchTranscript Help")
        .inner_size(1000.0, 780.0)
        .min_inner_size(640.0, 480.0)
        .build();
    if let Err(e) = r { protokoll::schreibe("hilfe", &format!("Fenster: {e}")); }
}

#[tauri::command]
async fn hilfe_oeffnen(app: tauri::AppHandle) {
    let h = app.clone();
    let _ = app.run_on_main_thread(move || hilfe_fenster(&h));
}

/// Startfehler: Klartext-Dialog mit Protokollpfad, dann Ende — nie ein
/// leeres Fenster (Plan R5; im Spike zweimal Stunden gekostet).
fn startfehler(app: &tauri::AppHandle, text: &str) -> ! {
    use tauri_plugin_dialog::{DialogExt, MessageDialogKind};
    protokoll::schreibe("start", text);
    let pfad = protokoll::pfad().map(|p| p.to_string_lossy().into_owned()).unwrap_or_default();
    app.dialog()
        .message(format!("{text}\n\nProtokoll: {pfad}"))
        .title("ResearchTranscript kann nicht starten")
        .kind(MessageDialogKind::Error)
        .blocking_show();
    std::process::exit(1)
}

pub fn run() {
    let app = tauri::Builder::default()
        .menu(menue)
        .on_menu_event(|handle, ereignis| {
            if ereignis.id() == "ueber" {
                let _ = handle.emit("ueber", ());
            } else if ereignis.id() == "hilfe" {
                hilfe_fenster(handle);
            }
        })
        // Das Hilfefenster hält die App nicht am Leben: schliesst das
        // Hauptfenster, geht es mit.
        .on_window_event(|fenster, ereignis| {
            if fenster.label() == "main" {
                if let tauri::WindowEvent::Destroyed = ereignis {
                    if let Some(w) = fenster.app_handle().get_webview_window("hilfe") {
                        let _ = w.close();
                    }
                }
            }
        })
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let handle = app.handle().clone();
            let ordner = handle.path().app_log_dir().unwrap_or_else(|_| std::env::temp_dir());
            protokoll::einrichten(ordner);
            protokoll::panics_fangen();
            protokoll::schreibe("start", &format!("Sandbox: {}", bookmarks::sandboxed()));
            // VOR Python: gemerkte Ordner freigeben (Sandbox-Erweiterung gilt
            // dann für Python, Core ML und das Whisper-Kind) und für asset://
            for p in bookmarks::wiederherstellen() {
                let _ = handle.asset_protocol_scope().allow_directory(&p, true);
            }
            // Whisper als Sidecar in Contents/MacOS (Store: inherit-Entitlement)
            if let Ok(exe) = std::env::current_exe() {
                let kind = exe.with_file_name("whisper-cli");
                if kind.is_file() { std::env::set_var("LT_WHISPER_CLI", &kind); }
            }
            // Interpreter + Fassade: ~150 ms, VOR dem ersten Befehl der
            // Oberfläche — auf einem Arbeits-Thread, nie auf dem
            // Hauptthread (python.rs-Kopf).
            let h = handle.clone();
            let r = std::thread::spawn(move || -> Result<(f64, Vec<String>), String> {
                let ms = python::init(&h)?;
                let res = python::resources(&h)?;
                Ok((ms, python::selbstpruefung(&res)))
            }).join().unwrap_or_else(|_| Err("Start-Thread abgestürzt".into()));
            match r {
                Ok((ms, probleme)) if probleme.is_empty() => {
                    protokoll::schreibe("start", &format!("Python bereit in {ms:.0} ms"));
                }
                Ok((_, probleme)) => startfehler(&handle, &probleme.join("\n")),
                Err(e) => startfehler(&handle, &e),
            }
            herzschlag(handle);
            Ok(())
        })
        .manage(Geoeffnet(Mutex::new(Vec::new())))
        .invoke_handler(tauri::generate_handler![api, sprecher_probe, medien_pfad,
                                                 ordner_oeffnen, geoeffnete_dateien,
                                                 protokoll_pfad, neustart, ordner_merken,
                                                 standard_ordner, ist_sandboxed, lizenzen_pfad, kanal, hilfe_oeffnen])
        .build(tauri::generate_context!())
        .expect("ResearchTranscript konnte nicht starten");

    app.run(|handle, event| {
        // Doppelklick auf ein .enrich (Info.plist): Pfade merken und dem
        // Frontend ein Signal geben (Review 2026-09-11 — vorher wurde
        // das Ereignis verworfen, die App ging nur nach vorn).
        if let RunEvent::Opened { urls } = &event {
            let pfade: Vec<String> = urls
                .iter()
                .filter_map(|u| u.to_file_path().ok())
                .map(|p| p.to_string_lossy().into_owned())
                .collect();
            if let Ok(mut g) = handle.state::<Geoeffnet>().0.lock() {
                g.extend(pfade);
            }
            let _ = handle.emit("dateien", ());
        }
        if let RunEvent::Exit = event {
            // Laufende Jobs abbrechen (Kinder töten), dann Prozessende —
            // kein Py_FinalizeEx (python.rs-Kopf).
            python::alle_abbrechen();
            protokoll::schreibe("exit", "Ende");
        }
    });
}
