fn main() {
    // Bundle: Contents/MacOS/<exe> → Contents/Resources/python-runtime/lib
    println!("cargo:rustc-link-arg=-Wl,-rpath,@executable_path/../Resources/python-runtime/lib");
}
