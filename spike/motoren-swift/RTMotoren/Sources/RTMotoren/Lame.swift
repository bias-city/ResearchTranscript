//  Lame.swift — MP3 über libmp3lame per dlopen (LGPL, dynamisch), VBR wie
//  ffmpegs libmp3lame-Wrapper (-q:a N → lame_set_VBR_quality(N)), Xing/LAME-Tag
//  nach lame_encode_flush an den Dateianfang zurückschreiben. Weg aus M4.

import Foundation

typealias LameT = OpaquePointer?

/// Symbole einer geöffneten libmp3lame; je Pfad einmal geöffnet (dlopen-Handle bleibt).
final class Lame {
    static let lock = NSLock()
    static var geladen: [String: Lame] = [:]

    let version: String
    let lame_init: @convention(c) () -> LameT
    let set_in_rate: @convention(c) (LameT, Int32) -> Int32
    let set_ch: @convention(c) (LameT, Int32) -> Int32
    let set_vbr: @convention(c) (LameT, Int32) -> Int32
    let set_vbr_q: @convention(c) (LameT, Float) -> Int32
    let set_vbrtag: @convention(c) (LameT, Int32) -> Int32
    let set_id3auto: @convention(c) (LameT, Int32) -> Int32
    let init_params: @convention(c) (LameT) -> Int32
    let enc_float: @convention(c) (LameT, UnsafePointer<Float>, UnsafePointer<Float>, Int32, UnsafeMutablePointer<UInt8>, Int32) -> Int32
    let enc_il_float: @convention(c) (LameT, UnsafePointer<Float>, Int32, UnsafeMutablePointer<UInt8>, Int32) -> Int32
    let flush: @convention(c) (LameT, UnsafeMutablePointer<UInt8>, Int32) -> Int32
    let lametag: @convention(c) (LameT, UnsafeMutablePointer<UInt8>?, Int) -> Int
    let close: @convention(c) (LameT) -> Int32

    static func hole(_ pfad: String) throws -> Lame {
        lock.lock(); defer { lock.unlock() }
        if let l = geladen[pfad] { return l }
        let l = try Lame(pfad)
        geladen[pfad] = l
        return l
    }

    private init(_ pfad: String) throws {
        guard let h = dlopen(pfad, RTLD_NOW) else {
            throw RTFehler("dlopen(\(pfad)): \(String(cString: dlerror()))")
        }
        func sym<T>(_ n: String, _: T.Type) throws -> T {
            guard let p = dlsym(h, n) else { throw RTFehler("Symbol fehlt in \(pfad): \(n)") }
            return unsafeBitCast(p, to: T.self)
        }
        let get_version = try sym("get_lame_version", (@convention(c) () -> UnsafePointer<CChar>).self)
        version = String(cString: get_version())
        lame_init = try sym("lame_init", (@convention(c) () -> LameT).self)
        set_in_rate = try sym("lame_set_in_samplerate", (@convention(c) (LameT, Int32) -> Int32).self)
        set_ch = try sym("lame_set_num_channels", (@convention(c) (LameT, Int32) -> Int32).self)
        set_vbr = try sym("lame_set_VBR", (@convention(c) (LameT, Int32) -> Int32).self)
        set_vbr_q = try sym("lame_set_VBR_quality", (@convention(c) (LameT, Float) -> Int32).self)
        set_vbrtag = try sym("lame_set_bWriteVbrTag", (@convention(c) (LameT, Int32) -> Int32).self)
        set_id3auto = try sym("lame_set_write_id3tag_automatic", (@convention(c) (LameT, Int32) -> Int32).self)
        init_params = try sym("lame_init_params", (@convention(c) (LameT) -> Int32).self)
        enc_float = try sym("lame_encode_buffer_ieee_float", (@convention(c) (LameT, UnsafePointer<Float>, UnsafePointer<Float>, Int32, UnsafeMutablePointer<UInt8>, Int32) -> Int32).self)
        enc_il_float = try sym("lame_encode_buffer_interleaved_ieee_float", (@convention(c) (LameT, UnsafePointer<Float>, Int32, UnsafeMutablePointer<UInt8>, Int32) -> Int32).self)
        flush = try sym("lame_encode_flush", (@convention(c) (LameT, UnsafeMutablePointer<UInt8>, Int32) -> Int32).self)
        lametag = try sym("lame_get_lametag_frame", (@convention(c) (LameT, UnsafeMutablePointer<UInt8>?, Int) -> Int).self)
        close = try sym("lame_close", (@convention(c) (LameT) -> Int32).self)
    }
}

/// Kern: Datei → MP3 (native Rate, mono/stereo), streamend.
func nachMp3(pfad: String, ziel: String, vbrQ: Int, dylib: String,
             abbruch: RTAbbruchCb?, fortschritt: RTFortschrittCb?, ctx: UnsafeMutableRawPointer?) throws -> [String: Any] {
    let t0 = jetzt()
    let lame = try Lame.hole(dylib)
    let leser = try NativLeser(url: URL(fileURLWithPath: pfad))
    let rate = leser.rate, ch = leser.channels
    guard rate > 0, ch > 0 else { throw RTFehler("Tonspur ohne Format") }
    // LAME kodiert mono/stereo; mehr Kanäle → (Summe)/n mono (Grenze, dokumentiert).
    let outCh = ch >= 2 ? 2 : 1
    let fort = Fortschritt(fortschritt, ctx)
    let gesamt = leser.trackDauer * rate

    let fm = FileManager.default
    if fm.fileExists(atPath: ziel) { try fm.removeItem(atPath: ziel) }
    guard fm.createFile(atPath: ziel, contents: nil) else { throw RTFehler("Zieldatei nicht anlegbar: \(ziel)") }
    let fh = try FileHandle(forWritingTo: URL(fileURLWithPath: ziel))

    let gf = lame.lame_init()
    guard gf != nil else { throw RTFehler("lame_init") }
    _ = lame.set_in_rate(gf, Int32(rate)); _ = lame.set_ch(gf, Int32(outCh))
    _ = lame.set_vbr(gf, 4)                  // vbr_mtrh = vbr_default, wie ffmpeg libmp3lame
    _ = lame.set_vbr_q(gf, Float(vbrQ))      // ffmpeg -q:a N → lame_set_VBR_quality(N)
    _ = lame.set_vbrtag(gf, 1); _ = lame.set_id3auto(gf, 0)
    guard lame.init_params(gf) >= 0 else { _ = lame.close(gf); throw RTFehler("lame_init_params fehlgeschlagen (rate \(rate), ch \(outCh))") }

    var buf = [UInt8](repeating: 0, count: 0)
    var frames = 0.0, seitPruefung = 0.0, bytes = 0
    func schreibe(_ n: Int32) throws {
        guard n >= 0 else { throw RTFehler("lame_encode: \(n)") }
        if n > 0 { try buf.withUnsafeBytes { try fh.write(contentsOf: Data($0.prefix(Int(n)))) }; bytes += Int(n) }
    }
    do {
        try pruefeAbbruch(abbruch, ctx)
        fort.melde(0)
        while let b = try leser.naechster() {
            let need = Int(1.25 * Double(b.frames)) + 7200
            if buf.count < need { buf = [UInt8](repeating: 0, count: need) }
            let w: Int32
            if ch == 2 {
                w = b.samples.withUnsafeBufferPointer { lame.enc_il_float(gf, $0.baseAddress!, Int32(b.frames), &buf, Int32(buf.count)) }
            } else if ch == 1 {
                w = b.samples.withUnsafeBufferPointer { lame.enc_float(gf, $0.baseAddress!, $0.baseAddress!, Int32(b.frames), &buf, Int32(buf.count)) }
            } else {
                let mono = downmix(b.samples, frames: b.frames, channels: ch)
                w = mono.withUnsafeBufferPointer { lame.enc_float(gf, $0.baseAddress!, $0.baseAddress!, Int32(b.frames), &buf, Int32(buf.count)) }
            }
            try schreibe(w)
            frames += Double(b.frames); seitPruefung += Double(b.frames)
            if gesamt > 0 { fort.melde(min(0.999, frames / gesamt)) }
            if seitPruefung >= 0.5 * rate {
                seitPruefung = 0
                try pruefeAbbruch(abbruch, ctx)
            }
        }
        try pruefeAbbruch(abbruch, ctx)
        if buf.count < 7200 { buf = [UInt8](repeating: 0, count: 7200) }
        try schreibe(lame.flush(gf, &buf, Int32(buf.count)))
        // Xing/LAME-Tag: LAME hat im ersten Block einen Platzhalter gleicher Grösse geschrieben — überschreiben.
        let need = lame.lametag(gf, nil, 0)
        if need > 0 {
            var tag = [UInt8](repeating: 0, count: need)
            let got = lame.lametag(gf, &tag, need)
            try fh.seek(toOffset: 0)
            try fh.write(contentsOf: Data(tag[0..<got]))
        }
        _ = lame.close(gf)
        try fh.close()
    } catch {
        _ = lame.close(gf)
        leser.abbrechen()
        try? fh.close()
        try? fm.removeItem(atPath: ziel)
        throw error
    }
    fort.melde(1)
    return ["bytes": bytes, "dauer_s": frames / rate, "ms": (jetzt() - t0) * 1000,
            "rate": rate, "kanaele": outCh, "lame": lame.version]
}

@_cdecl("rt_nach_mp3")
public func rt_nach_mp3(_ pfad: UnsafePointer<CChar>?, _ ziel: UnsafePointer<CChar>?, _ vbrQ: Int32,
                        _ dylib: UnsafePointer<CChar>?,
                        _ abbruch: RTAbbruchCb?, _ fortschritt: RTFortschrittCb?,
                        _ ctx: UnsafeMutableRawPointer?) -> UnsafeMutablePointer<CChar>? {
    guard let pfad, let ziel else { return jsonString(["error": "pfad/ziel_mp3 ist NULL"]) }
    let lib = dylib.map { String(cString: $0) } ?? "libmp3lame.dylib"
    do {
        return jsonString(try nachMp3(pfad: String(cString: pfad), ziel: String(cString: ziel), vbrQ: Int(vbrQ), dylib: lib,
                                      abbruch: abbruch, fortschritt: fortschritt, ctx: ctx))
    } catch { return jsonFehler(error) }
}
