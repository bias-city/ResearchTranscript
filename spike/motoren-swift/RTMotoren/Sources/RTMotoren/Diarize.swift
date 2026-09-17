//  Diarize.swift — SpeakerKit im Prozess, wie spike/speakerkit-shim/Shim.swift:
//  async-API über Task.detached + DispatchSemaphore synchron; ein SpeakerKit je
//  Modellordner bleibt im Prozess. Neu: WAV-Eingabe, Abbruch (Task.cancel,
//  alle 100 ms gepollt) und Fortschritt 0..1 aus dem SpeakerKit-Callback.

import Foundation
import SpeakerKit

private final class Cache: @unchecked Sendable {
    static let shared = Cache()
    private let lock = NSLock()
    private var kits: [String: SpeakerKit] = [:]
    func get(_ dir: String) -> SpeakerKit? { lock.lock(); defer { lock.unlock() }; return kits[dir] }
    func put(_ dir: String, _ kit: SpeakerKit) { lock.lock(); defer { lock.unlock() }; kits[dir] = kit }
    func drop(_ dir: String) -> SpeakerKit? { lock.lock(); defer { lock.unlock() }; return kits.removeValue(forKey: dir) }
}

/// Label wie argmax-cli: A, B, C … (65 + id % 26); -1 → UNKNOWN.
private func label(_ id: Int?) -> String {
    guard let id, id >= 0 else { return "UNKNOWN" }
    return String(UnicodeScalar(UInt8(65 + id % 26)))
}

private final class ResultBox<T>: @unchecked Sendable { var value: Result<T, Error>? }

/// async → sync; solange gewartet wird, alle 100 ms den Abbruch-Callback fragen und den Task abbrechen.
private func runSync<T: Sendable>(abbruch: RTAbbruchCb?, ctx: UnsafeMutableRawPointer?,
                                  _ body: @escaping @Sendable () async throws -> T) -> Result<T, Error> {
    let sem = DispatchSemaphore(value: 0)
    let box = ResultBox<T>()
    let task = Task.detached(priority: .userInitiated) {
        do { box.value = .success(try await body()) }
        catch { box.value = .failure(error) }
        sem.signal()
    }
    var abgebrochen = false
    while sem.wait(timeout: .now() + .milliseconds(100)) == .timedOut {
        if !abgebrochen, let abbruch, abbruch(ctx) {
            abgebrochen = true
            task.cancel()
        }
    }
    if abgebrochen { return .failure(RTAbgebrochen()) }
    return box.value!
}

@_cdecl("rt_diarize_wav")
public func rt_diarize_wav(_ wavPfad: UnsafePointer<CChar>?, _ numSpeakers: Int32,
                           _ clusterDistanceThreshold: Float, _ exclusive: Bool,
                           _ modelDir: UnsafePointer<CChar>?,
                           _ abbruch: RTAbbruchCb?, _ fortschritt: RTFortschrittCb?,
                           _ ctx: UnsafeMutableRawPointer?) -> UnsafeMutablePointer<CChar>? {
    guard let wavPfad, let modelDir else { return jsonString(["error": "wav_pfad/model_dir ist NULL"]) }
    let dir = String(cString: modelDir)
    var isDir: ObjCBool = false
    guard FileManager.default.fileExists(atPath: dir, isDirectory: &isDir), isDir.boolValue else {
        return jsonString(["error": "Modellordner fehlt: \(dir)"])
    }
    let audio: [Float]
    do {
        let w = try leseWavMono(String(cString: wavPfad))
        guard w.rate == 16000 else { return jsonString(["error": "WAV muss 16 kHz haben (ist \(w.rate))"]) }
        guard !w.samples.isEmpty else { return jsonString(["error": "WAV ohne Samples"]) }
        audio = w.samples
    } catch { return jsonFehler(error) }

    let options = PyannoteDiarizationOptions(
        numberOfSpeakers: numSpeakers > 0 ? Int(numSpeakers) : nil,
        clusterDistanceThreshold: clusterDistanceThreshold,
        useExclusiveReconciliation: exclusive
    )
    let fort = Fortschritt(fortschritt, ctx)

    let result = runSync(abbruch: abbruch, ctx: ctx) { () async throws -> [String: Any] in
        let t0 = Date()
        let kit: SpeakerKit
        if let cached = Cache.shared.get(dir) {
            kit = cached
        } else {
            // Wie DiarizeCLI.setupSpeakerKit: lokaler Ordner, kein Download.
            let config = PyannoteConfig(modelFolder: dir, download: false, verbose: false, logLevel: .none, fullRedundancy: true)
            kit = try await SpeakerKit(config)
            try await kit.ensureModelsLoaded()
            Cache.shared.put(dir, kit)
        }
        try Task.checkCancellation()
        let t1 = Date()
        fort.melde(0)
        let cb: (@Sendable (Progress) -> Void)? = fortschritt == nil ? nil : { @Sendable prog in
            fort.melde(Double(prog.completedUnitCount) / 100)
        }
        let raw = try await kit.diarize(audioArray: audio, options: options, progressCallback: cb)
        try Task.checkCancellation()
        let t2 = Date()
        var r = raw
        r.updateSegments(minActiveOffset: 0.0)   // wie SpeakerKit.generateRTTM ohne Transkript
        let segs: [[String: Any]] = r.segments.map {
            ["start": Double($0.startTime), "end": Double($0.endTime), "speaker": label($0.speaker.speakerId)]
        }
        return ["segments": segs, "speaker_count": r.speakerCount,
                "model_load_ms": t1.timeIntervalSince(t0) * 1000, "diarize_ms": t2.timeIntervalSince(t1) * 1000]
    }
    switch result {
    case .success(let r): fort.melde(1); return jsonString(r)
    case .failure(let e): return jsonFehler(e)
    }
}

@_cdecl("rt_unload_models")
public func rt_unload_models(_ modelDir: UnsafePointer<CChar>?) {
    guard let modelDir else { return }
    guard let kit = Cache.shared.drop(String(cString: modelDir)) else { return }
    _ = runSync(abbruch: nil, ctx: nil) { await kit.unloadModels() }
}
