// swift-tools-version: 5.10
// SpeakerKitShim — C-ABI-Hülle um SpeakerKit (Argmax, MIT) für den Aufruf
// aus Rust im selben Prozess. Spike F3, docs/appstore-plan.md §3.
import PackageDescription

let package = Package(
    name: "SpeakerKitShim",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "SpeakerKitShim", type: .static, targets: ["SpeakerKitShim"]),
    ],
    dependencies: [
        // Lokaler Klon auf Commit ea872ff (wie scripts/hole-argmax.mjs).
        // Produktiv: .package(url: "https://github.com/argmaxinc/argmax-oss-swift.git", revision: "ea872ff")
        .package(path: "../argmax-oss-swift"),
    ],
    targets: [
        .target(
            name: "SpeakerKitShim",
            dependencies: [
                .product(name: "SpeakerKit", package: "argmax-oss-swift"),
            ]
        ),
    ]
)
