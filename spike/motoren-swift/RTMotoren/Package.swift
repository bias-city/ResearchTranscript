// swift-tools-version: 5.10
// RTMotoren — EINE C-Schnittstelle (include/rtmotoren.h) für die Motoren
// der App: Sondieren, Dekodieren nach 16 kHz, MP3 (libmp3lame per dlopen),
// Sprechertrennung (SpeakerKit). Spike zu docs/appstore-plan.md §5.
// Statische Bibliothek wie spike/speakerkit-shim/SpeakerKitShim.
import PackageDescription

let package = Package(
    name: "RTMotoren",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "RTMotoren", type: .static, targets: ["RTMotoren"]),
    ],
    dependencies: [
        // Lokaler Klon auf Commit ea872ff (wie scripts/hole-argmax.mjs, Shim-Spike).
        // Produktiv: .package(url: "https://github.com/argmaxinc/argmax-oss-swift.git", revision: "ea872ff")
        .package(path: "../../speakerkit-shim/argmax-oss-swift"),
    ],
    targets: [
        .target(
            name: "RTMotoren",
            dependencies: [
                .product(name: "SpeakerKit", package: "argmax-oss-swift"),
            ],
            linkerSettings: [
                .linkedFramework("AVFoundation"),
                .linkedFramework("AudioToolbox"),
                .linkedFramework("Accelerate"),
            ]
        ),
    ]
)
