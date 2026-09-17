//  SpeakerKitShim — exportiert rt_diarize / rt_free als C-Funktionen.
//
//  Eingabe: f32-Samples 16 kHz mono. Ausgabe: JSON-C-String, den der
//  Aufrufer mit rt_free freigibt. Erfolg: {"segments":[{"start","end",
//  "speaker"}],"speaker_count":N,...}. Fehler: {"error":"..."}.
//  Die async-API von SpeakerKit wird über eine DispatchSemaphore
//  synchron gemacht; die geladene SpeakerKit-Instanz bleibt je
//  Modellordner im Prozess (zweiter Aufruf ohne Modell-Laden).

import Foundation
import SpeakerKit

public typealias RTProgressCallback = @convention(c) (Int32) -> Void

private struct ShimSegment: Encodable {
    let start: Float
    let end: Float
    let speaker: String
}

private struct ShimResult: Encodable {
    let segments: [ShimSegment]
    let speaker_count: Int
    let model_load_ms: Double
    let diarize_ms: Double
}

private struct ShimError: Encodable {
    let error: String
}

/// Ein SpeakerKit je Modellordner, geschützt über einen Lock.
private final class Cache: @unchecked Sendable {
    static let shared = Cache()
    private let lock = NSLock()
    private var kits: [String: SpeakerKit] = [:]

    func get(_ dir: String) -> SpeakerKit? {
        lock.lock(); defer { lock.unlock() }
        return kits[dir]
    }
    func put(_ dir: String, _ kit: SpeakerKit) {
        lock.lock(); defer { lock.unlock() }
        kits[dir] = kit
    }
    func drop(_ dir: String) -> SpeakerKit? {
        lock.lock(); defer { lock.unlock() }
        return kits.removeValue(forKey: dir)
    }
}

/// Label wie argmax-cli: A, B, C … (65 + id % 26); -1 → UNKNOWN.
private func label(_ id: Int?) -> String {
    guard let id, id >= 0 else { return "UNKNOWN" }
    return String(UnicodeScalar(UInt8(65 + id % 26)))
}

private func encode<T: Encodable>(_ v: T) -> UnsafeMutablePointer<CChar>? {
    let enc = JSONEncoder()
    guard let data = try? enc.encode(v),
          let s = String(data: data, encoding: .utf8) else {
        return strdup("{\"error\":\"JSON-Kodierung fehlgeschlagen\"}")
    }
    return strdup(s)
}

private final class ResultBox<T>: @unchecked Sendable { var value: Result<T, Error>? }

private func runSync<T: Sendable>(_ body: @escaping @Sendable () async throws -> T) -> Result<T, Error> {
    let sem = DispatchSemaphore(value: 0)
    let box = ResultBox<T>()
    Task.detached(priority: .userInitiated) {
        do { box.value = .success(try await body()) }
        catch { box.value = .failure(error) }
        sem.signal()
    }
    sem.wait()
    return box.value!
}

/// Diarisieren. Gibt einen JSON-C-String zurück (rt_free!).
@_cdecl("rt_diarize")
public func rt_diarize(
    _ samples: UnsafePointer<Float>?,
    _ count: Int,
    _ numSpeakers: Int32,
    _ clusterDistanceThreshold: Float,
    _ exclusive: Bool,
    _ modelDir: UnsafePointer<CChar>?,
    _ progress: RTProgressCallback?
) -> UnsafeMutablePointer<CChar>? {
    guard let modelDir else { return encode(ShimError(error: "model_dir ist NULL")) }
    let dir = String(cString: modelDir)
    guard let samples, count > 0 else { return encode(ShimError(error: "keine Samples")) }
    let audio = Array(UnsafeBufferPointer(start: samples, count: count))
    var isDir: ObjCBool = false
    guard FileManager.default.fileExists(atPath: dir, isDirectory: &isDir), isDir.boolValue else {
        return encode(ShimError(error: "Modellordner fehlt: \(dir)"))
    }

    let options = PyannoteDiarizationOptions(
        numberOfSpeakers: numSpeakers > 0 ? Int(numSpeakers) : nil,
        clusterDistanceThreshold: clusterDistanceThreshold,
        useExclusiveReconciliation: exclusive
    )

    let result = runSync { () async throws -> ShimResult in
        let t0 = Date()
        let kit: SpeakerKit
        if let cached = Cache.shared.get(dir) {
            kit = cached
        } else {
            // Wie DiarizeCLI.setupSpeakerKit: lokaler Ordner, kein Download.
            let config = PyannoteConfig(
                modelFolder: dir,
                download: false,
                verbose: false,
                logLevel: .none,
                fullRedundancy: true
            )
            kit = try await SpeakerKit(config)
            try await kit.ensureModelsLoaded()
            Cache.shared.put(dir, kit)
        }
        let t1 = Date()
        let cb: (@Sendable (Progress) -> Void)? = progress.map { p in
            { @Sendable prog in p(Int32(clamping: prog.completedUnitCount)) }
        }
        let raw = try await kit.diarize(audioArray: audio, options: options, progressCallback: cb)
        let t2 = Date()
        // Wie SpeakerKit.generateRTTM ohne Transkript: minActiveOffset 0.
        var r = raw
        r.updateSegments(minActiveOffset: 0.0)
        let segs = r.segments.map {
            ShimSegment(start: $0.startTime, end: $0.endTime, speaker: label($0.speaker.speakerId))
        }
        return ShimResult(
            segments: segs,
            speaker_count: r.speakerCount,
            model_load_ms: t1.timeIntervalSince(t0) * 1000,
            diarize_ms: t2.timeIntervalSince(t1) * 1000
        )
    }
    switch result {
    case .success(let r): return encode(r)
    case .failure(let e): return encode(ShimError(error: "\(e)"))
    }
}

/// Modelle eines Ordners aus dem Speicher werfen.
@_cdecl("rt_unload")
public func rt_unload(_ modelDir: UnsafePointer<CChar>?) {
    guard let modelDir else { return }
    let dir = String(cString: modelDir)
    guard let kit = Cache.shared.drop(dir) else { return }
    _ = runSync { await kit.unloadModels() }
}

/// Von rt_diarize gelieferten String freigeben.
@_cdecl("rt_free")
public func rt_free(_ p: UnsafeMutablePointer<CChar>?) {
    free(p)
}
