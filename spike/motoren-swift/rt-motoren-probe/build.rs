// Baut RTMotoren per `swift build -c release` (über swift-rs) und linkt die
// statische Bibliothek plus Swift-Runtime-Suchpfade — wie rt-diarize-spike.
use swift_rs::SwiftLinker;

fn main() {
    SwiftLinker::new("13.0")
        .with_package("RTMotoren", "../RTMotoren")
        .link();
    // libswift_Concurrency wird sonst aus der Xcode-Toolchain mit
    // @rpath-Install-Name gelinkt → dyld «no LC_RPATH's found».
    println!("cargo:rustc-link-arg=-Wl,-rpath,/usr/lib/swift");
}
