fn main() {
    // Phase-0-Spike (F1): libpython liegt im Bundle unter Contents/Frameworks
    // (tauri.spike.conf.json → bundle.macOS.frameworks); die Hülle findet sie
    // über diesen rpath. Ausserhalb des Bundles (cargo run) greift zusätzlich
    // der lib_dir aus pyo3-config.txt.
    println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path/../Frameworks");
    tauri_build::build()
}
