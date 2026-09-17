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
    // Motoren im Prozess (Feature `motoren`): das SwiftPM-Paket RTMotoren
    // als statische Bibliothek; libswift_Concurrency käme sonst aus der
    // Xcode-Toolchain mit @rpath-Install-Name (dyld «no LC_RPATH's found»,
    // Befund F3) — deshalb der System-rpath.
    #[cfg(feature = "motoren")]
    {
        swift_rs::SwiftLinker::new("14.0")
            .with_package("RTMotoren", "../../spike/motoren-swift/RTMotoren")
            .link();
        println!("cargo:rustc-link-arg=-Wl,-rpath,/usr/lib/swift");
    }
    tauri_build::build()
}
