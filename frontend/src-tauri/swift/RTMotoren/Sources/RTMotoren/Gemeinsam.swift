//  Gemeinsam.swift — JSON-Rückgaben, Callback-Typen, Fehler, WAV-Lesen/-Schreiben.
//  Alle rt_*-Funktionen liefern JSON-C-Strings (rt_free!), Fehler als {"error":"…"}.

import Foundation

public typealias RTAbbruchCb = @convention(c) (UnsafeMutableRawPointer?) -> Bool
public typealias RTFortschrittCb = @convention(c) (Double, UnsafeMutableRawPointer?) -> Void

struct RTFehler: Error, CustomStringConvertible {
    let text: String
    init(_ t: String) { text = t }
    var description: String { text }
}

/// Wird geworfen, wenn der Abbruch-Callback true liefert.
struct RTAbgebrochen: Error {}

func jsonString(_ obj: Any) -> UnsafeMutablePointer<CChar>? {
    guard JSONSerialization.isValidJSONObject(obj),
          let d = try? JSONSerialization.data(withJSONObject: obj, options: [.sortedKeys]),
          let s = String(data: d, encoding: .utf8) else {
        return strdup("{\"error\":\"JSON-Kodierung fehlgeschlagen\"}")
    }
    return strdup(s)
}

func jsonFehler(_ e: Error) -> UnsafeMutablePointer<CChar>? {
    if e is RTAbgebrochen { return jsonString(["error": "abgebrochen"]) }
    if e is CancellationError { return jsonString(["error": "abgebrochen"]) }
    if let f = e as? RTFehler { return jsonString(["error": f.text]) }
    let ns = e as NSError
    var t = ns.localizedDescription
    if let r = ns.userInfo[NSLocalizedFailureReasonErrorKey] as? String { t += " (\(r))" }
    return jsonString(["error": "\(ns.domain) \(ns.code): \(t)"])
}

func jetzt() -> Double { CFAbsoluteTimeGetCurrent() }

func fourcc(_ v: FourCharCode) -> String {
    let b = [UInt8(v >> 24 & 0xff), UInt8(v >> 16 & 0xff), UInt8(v >> 8 & 0xff), UInt8(v & 0xff)]
    return String(bytes: b, encoding: .macOSRoman) ?? "????"
}

/// Fortschritt monoton 0..1 an den C-Callback melden.
final class Fortschritt {
    let cb: RTFortschrittCb?
    let ctx: UnsafeMutableRawPointer?
    private var letzter = -1.0
    private let lock = NSLock()
    init(_ cb: RTFortschrittCb?, _ ctx: UnsafeMutableRawPointer?) { self.cb = cb; self.ctx = ctx }
    func melde(_ anteil: Double) {
        guard let cb else { return }
        let a = min(1.0, max(0.0, anteil))
        lock.lock()
        guard a > letzter else { lock.unlock(); return }
        letzter = a
        lock.unlock()
        cb(a, ctx)
    }
}

/// Abbruch-Callback prüfen; wirft RTAbgebrochen.
@inline(__always)
func pruefeAbbruch(_ cb: RTAbbruchCb?, _ ctx: UnsafeMutableRawPointer?) throws {
    if let cb, cb(ctx) { throw RTAbgebrochen() }
}

// ---------- WAV ----------

/// Streamender WAV-Schreiber (RIFF, PCM s16le mono, Rate frei); Kopf wird am Ende nachgetragen.
final class WavSchreiber {
    private let fh: FileHandle
    private let rate: Int
    private(set) var frames = 0
    let pfad: String

    init(pfad: String, rate: Int) throws {
        self.pfad = pfad; self.rate = rate
        let fm = FileManager.default
        if fm.fileExists(atPath: pfad) { try fm.removeItem(atPath: pfad) }
        guard fm.createFile(atPath: pfad, contents: nil) else { throw RTFehler("Zieldatei nicht anlegbar: \(pfad)") }
        fh = try FileHandle(forWritingTo: URL(fileURLWithPath: pfad))
        try fh.write(contentsOf: kopf(bytes: 0))
    }

    private func kopf(bytes: Int) -> Data {
        var d = Data()
        func u32(_ v: UInt32) { var x = v.littleEndian; d.append(Data(bytes: &x, count: 4)) }
        func u16(_ v: UInt16) { var x = v.littleEndian; d.append(Data(bytes: &x, count: 2)) }
        d.append("RIFF".data(using: .ascii)!); u32(UInt32(36 + bytes)); d.append("WAVE".data(using: .ascii)!)
        d.append("fmt ".data(using: .ascii)!); u32(16); u16(1); u16(1); u32(UInt32(rate)); u32(UInt32(rate * 2)); u16(2); u16(16)
        d.append("data".data(using: .ascii)!); u32(UInt32(bytes))
        return d
    }

    /// Float → s16 (Rundung, Sättigung wie avspike.schreibeWav16).
    func schreibe(_ p: UnsafePointer<Float>, _ n: Int) throws {
        guard n > 0 else { return }
        var pcm = [Int16](repeating: 0, count: n)
        for i in 0..<n { pcm[i] = Int16(max(-32768, min(32767, (p[i] * 32768).rounded()))) }
        try pcm.withUnsafeBytes { try fh.write(contentsOf: Data($0)) }
        frames += n
    }

    func schliesse() throws {
        try fh.seek(toOffset: 0)
        try fh.write(contentsOf: kopf(bytes: frames * 2))
        try fh.close()
    }

    /// Bei Abbruch/Fehler: Datei schliessen und löschen.
    func verwerfe() {
        try? fh.close()
        try? FileManager.default.removeItem(atPath: pfad)
    }
}

/// WAV lesen (PCM s16 oder IEEE-Float32, mono) → Float-Samples wie AVAudioFile/hound (i16/32768).
func leseWavMono(_ pfad: String) throws -> (samples: [Float], rate: Int) {
    guard let d = FileManager.default.contents(atPath: pfad) else { throw RTFehler("WAV nicht lesbar: \(pfad)") }
    guard d.count >= 12, String(bytes: d[0..<4], encoding: .ascii) == "RIFF",
          String(bytes: d[8..<12], encoding: .ascii) == "WAVE" else { throw RTFehler("kein RIFF/WAVE: \(pfad)") }
    return try d.withUnsafeBytes { raw -> ([Float], Int) in
        let p = raw.baseAddress!
        var off = 12
        var format = 0, rate = 0, ch = 0, bits = 0
        while off + 8 <= d.count {
            let id = String(bytes: raw[off..<off+4], encoding: .ascii) ?? ""
            let size = Int(p.loadUnaligned(fromByteOffset: off + 4, as: UInt32.self))
            if id == "fmt " {
                format = Int(p.loadUnaligned(fromByteOffset: off + 8, as: UInt16.self))
                ch = Int(p.loadUnaligned(fromByteOffset: off + 10, as: UInt16.self))
                rate = Int(p.loadUnaligned(fromByteOffset: off + 12, as: UInt32.self))
                bits = Int(p.loadUnaligned(fromByteOffset: off + 22, as: UInt16.self))
                if format == 0xFFFE, size >= 26 {   // WAVE_FORMAT_EXTENSIBLE: SubFormat-Anfang
                    format = Int(p.loadUnaligned(fromByteOffset: off + 32, as: UInt16.self))
                }
            } else if id == "data" {
                guard ch == 1 else { throw RTFehler("WAV muss mono sein (ch=\(ch))") }
                let n = min(size, d.count - off - 8)
                let base = p.advanced(by: off + 8)
                var samples: [Float]
                if format == 1 && bits == 16 {
                    samples = [Float](repeating: 0, count: n / 2)
                    for i in 0..<samples.count { samples[i] = Float(base.loadUnaligned(fromByteOffset: 2 * i, as: Int16.self)) / 32768 }
                } else if format == 3 && bits == 32 {
                    samples = [Float](repeating: 0, count: n / 4)
                    for i in 0..<samples.count { samples[i] = base.loadUnaligned(fromByteOffset: 4 * i, as: Float.self) }
                } else {
                    throw RTFehler("WAV-Format nicht unterstützt (format=\(format) bits=\(bits)); erwartet s16 oder f32")
                }
                return (samples, rate)
            }
            off += 8 + size + (size & 1)
        }
        throw RTFehler("WAV ohne data-Chunk: \(pfad)")
    }
}

/// Von rt_* gelieferten String freigeben.
@_cdecl("rt_free")
public func rt_free(_ p: UnsafeMutablePointer<CChar>?) {
    free(p)
}
