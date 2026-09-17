fn main() {
    // libpython liegt im Bundle unter Contents/Frameworks
    // (tauri.conf.json → bundle.macOS.frameworks); die Hülle findet sie
    // über diesen rpath. Ausserhalb des Bundles (tauri dev, cargo run)
    // zusätzlich der lib_dir der gebündelten Laufzeit aus
    // pyo3-config.txt — nur im Debug-Profil, damit kein Rechnerpfad in
    // ein Release wandert.
    println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path/../Frameworks");
    if std::env::var("PROFILE").as_deref() == Ok("debug") {
        if let Some(dir) = pyo3_build_config::get().lib_dir() {
            println!("cargo:rustc-link-arg=-Wl,-rpath,{dir}");
        }
    }
    tauri_build::build()
}
