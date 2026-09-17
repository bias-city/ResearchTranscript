//  Ton.swift — nativ dekodieren (AVAssetReaderTrackOutput ohne Konvertierung),
//  Downmix (L+R)/n selbst, AVAudioConverter (Qualität max) auf 16 kHz,
//  streamend in ein s16-WAV. Erprobter Weg aus spike/avfoundation (M4).

import AVFoundation
import Accelerate
import Foundation

/// Ein nativ dekodierter Block: interleaved Float32, Präsentationszeit des ersten Frames.
struct NativBlock {
    var samples: [Float]
    var frames: Int
    var pts: Double
}

/// AVAssetReader → Linear-PCM Float32 in nativer Rate/Kanalzahl, blockweise.
final class NativLeser {
    let asset: AVURLAsset
    let track: AVAssetTrack
    let rate: Double
    let channels: Int
    let trackDauer: Double
    private var reader: AVAssetReader
    private var output: AVAssetReaderTrackOutput

    init(url: URL, timeRange: CMTimeRange? = nil) throws {
        asset = AVURLAsset(url: url)
        let tracks = asset.tracks(withMediaType: .audio)
        guard let t = tracks.first else {
            throw RTFehler("keine Tonspur (asset.tracks=\(asset.tracks.count), readable=\(asset.isReadable))")
        }
        track = t
        var r = 0.0, c = 0
        for fd in t.formatDescriptions as! [CMFormatDescription] {
            if let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(fd) {
                r = asbd.pointee.mSampleRate; c = Int(asbd.pointee.mChannelsPerFrame); break
            }
        }
        rate = r; channels = c
        trackDauer = CMTimeGetSeconds(t.timeRange.duration)
        (reader, output) = try NativLeser.mache(asset, t, timeRange)
    }

    private static func mache(_ asset: AVURLAsset, _ t: AVAssetTrack, _ timeRange: CMTimeRange?) throws -> (AVAssetReader, AVAssetReaderTrackOutput) {
        let reader = try AVAssetReader(asset: asset)
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM,
            AVLinearPCMBitDepthKey: 32,
            AVLinearPCMIsFloatKey: true,
            AVLinearPCMIsBigEndianKey: false,
            AVLinearPCMIsNonInterleaved: false,
        ]
        let output = AVAssetReaderTrackOutput(track: t, outputSettings: settings)
        output.alwaysCopiesSampleData = false
        reader.add(output)
        if let tr = timeRange { reader.timeRange = tr }
        guard reader.startReading() else {
            throw reader.error ?? RTFehler("startReading fehlgeschlagen")
        }
        return (reader, output)
    }

    /// Neu von vorn (ohne timeRange) — wenn das Seeking im Container versagt (Ogg).
    func nochmalVonVorn() throws {
        reader.cancelReading()
        (reader, output) = try NativLeser.mache(asset, track, nil)
    }

    func naechster() throws -> NativBlock? {
        while let sb = output.copyNextSampleBuffer() {
            guard let bb = CMSampleBufferGetDataBuffer(sb) else { continue }
            var len = 0
            var ptr: UnsafeMutablePointer<Int8>?
            CMBlockBufferGetDataPointer(bb, atOffset: 0, lengthAtOffsetOut: nil, totalLengthOut: &len, dataPointerOut: &ptr)
            guard let p = ptr, len > 0 else { continue }
            let n = len / 4
            let s = p.withMemoryRebound(to: Float.self, capacity: n) { Array(UnsafeBufferPointer(start: $0, count: n)) }
            var rate = self.rate, ch = self.channels
            if let fd = CMSampleBufferGetFormatDescription(sb), let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(fd) {
                rate = asbd.pointee.mSampleRate; ch = Int(asbd.pointee.mChannelsPerFrame)
            }
            guard ch == channels, rate == self.rate else {
                throw RTFehler("Format wechselt im Strom (\(rate) Hz ch=\(ch) statt \(self.rate)/\(channels))")
            }
            let pts = CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sb))
            return NativBlock(samples: s, frames: n / max(1, ch), pts: pts)
        }
        if reader.status == .failed { throw reader.error ?? RTFehler("AVAssetReader failed") }
        return nil
    }

    func abbrechen() { reader.cancelReading() }
}

/// (L+R+…)/n aus interleaved Samples.
func downmix(_ s: [Float], frames: Int, channels: Int) -> [Float] {
    if channels == 1 { return s }
    var mono = [Float](repeating: 0, count: frames)
    s.withUnsafeBufferPointer { p in
        for c in 0..<channels {
            vDSP_vadd(mono, 1, p.baseAddress! + c, vDSP_Stride(channels), &mono, 1, vDSP_Length(frames))
        }
    }
    var k = 1 / Float(channels)
    vDSP_vsmul(mono, 1, &k, &mono, 1, vDSP_Length(frames))
    return mono
}

/// Streamender Umtaster mono Float → 16 kHz mono Float (AVAudioConverter, Qualität max).
final class Umtaster {
    private let srcF: AVAudioFormat
    private let dstF: AVAudioFormat
    private let conv: AVAudioConverter
    private var vorrat: [Float] = []
    private var eof = false
    let block = 65536

    init(rate: Double, ziel: Double = 16000) throws {
        srcF = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: rate, channels: 1, interleaved: false)!
        dstF = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: ziel, channels: 1, interleaved: false)!
        guard let c = AVAudioConverter(from: srcF, to: dstF) else { throw RTFehler("AVAudioConverter \(rate)→\(ziel) nicht anlegbar") }
        c.sampleRateConverterQuality = AVAudioQuality.max.rawValue
        conv = c
    }

    /// Samples anhängen; liefert fertige 16-kHz-Samples, sobald genug Vorrat da ist.
    func fuettere(_ mono: [Float], _ sink: (UnsafePointer<Float>, Int) throws -> Void) throws {
        vorrat.append(contentsOf: mono)
        if vorrat.count >= 2 * block { try laufe(sink) }
    }

    func schliesse(_ sink: (UnsafePointer<Float>, Int) throws -> Void) throws {
        eof = true
        try laufe(sink)
    }

    private func laufe(_ sink: (UnsafePointer<Float>, Int) throws -> Void) throws {
        var pos = 0
        var fertig = false
        while !fertig {
            let outBuf = AVAudioPCMBuffer(pcmFormat: dstF, frameCapacity: 32768)!
            var err: NSError?
            let st = conv.convert(to: outBuf, error: &err) { [self] _, status in
                let rest = vorrat.count - pos
                if rest <= 0 || (!eof && rest < block) {
                    status.pointee = eof ? .endOfStream : .noDataNow
                    return nil
                }
                let n = min(block, rest)
                let inBuf = AVAudioPCMBuffer(pcmFormat: srcF, frameCapacity: AVAudioFrameCount(n))!
                inBuf.frameLength = AVAudioFrameCount(n)
                vorrat.withUnsafeBufferPointer { inBuf.floatChannelData![0].update(from: $0.baseAddress! + pos, count: n) }
                pos += n
                status.pointee = .haveData
                return inBuf
            }
            if let e = err { throw e }
            if outBuf.frameLength > 0 { try sink(outBuf.floatChannelData![0], Int(outBuf.frameLength)) }
            switch st {
            case .haveData: continue
            case .inputRanDry: fertig = !eof || outBuf.frameLength == 0
            case .endOfStream, .error: fertig = true
            @unknown default: fertig = true
            }
        }
        vorrat.removeFirst(pos)
    }
}

/// Kern: Datei (Ausschnitt) → 16-kHz-mono-s16-WAV, streamend, mit Abbruch/Fortschritt.
func dekodiereWav16k(pfad: String, ziel: String, start: Double, dauer: Double,
                     abbruch: RTAbbruchCb?, fortschritt: RTFortschrittCb?, ctx: UnsafeMutableRawPointer?) throws -> [String: Any] {
    let t0 = jetzt()
    let url = URL(fileURLWithPath: pfad)
    let ausschnitt = dauer > 0
    // Ausschnitt: Reader mit Vorlauf (0,5 s) positionieren, dann sample-genau nach PTS trimmen.
    var tr: CMTimeRange? = nil
    if ausschnitt {
        let s = max(0, start - 0.5)
        tr = CMTimeRange(start: CMTime(seconds: s, preferredTimescale: 48000),
                         duration: CMTime(seconds: start + dauer - s + 0.5, preferredTimescale: 48000))
    }
    let leser = try NativLeser(url: url, timeRange: tr)
    let rate = leser.rate, ch = leser.channels
    guard rate > 0, ch > 0 else { throw RTFehler("Tonspur ohne Format (rate=\(rate) ch=\(ch))") }
    let fort = Fortschritt(fortschritt, ctx)
    let gesamtFrames = ausschnitt ? dauer * rate : leser.trackDauer * rate
    let ende = start + dauer
    let umtaster = try Umtaster(rate: rate)
    let wav = try WavSchreiber(pfad: ziel, rate: 16000)
    var gelesen = 0.0            // Frames, die in den Umtaster gingen (für Fortschritt)
    var seitPruefung = 0.0
    var erster = true
    do {
        try pruefeAbbruch(abbruch, ctx)
        fort.melde(0)
        while var b = try leser.naechster() {
            if ausschnitt {
                if erster {
                    erster = false
                    // Seeking zu spät gelandet (Ogg): von vorn lesen und per PTS trimmen.
                    if b.pts > start + 0.001 {
                        try leser.nochmalVonVorn()
                        guard let b0 = try leser.naechster() else { break }
                        b = b0
                    }
                }
                let bStart = b.pts, bEnde = b.pts + Double(b.frames) / rate
                if bEnde <= start { continue }
                if bStart >= ende { break }
                let von = max(0, Int(((start - bStart) * rate).rounded()))
                let bis = min(b.frames, Int(((ende - bStart) * rate).rounded()))
                if bis <= von { continue }
                if von > 0 || bis < b.frames {
                    b.samples = Array(b.samples[(von * ch)..<(bis * ch)])
                    b.frames = bis - von
                }
            }
            let mono = downmix(b.samples, frames: b.frames, channels: ch)
            try umtaster.fuettere(mono) { p, n in try wav.schreibe(p, n) }
            gelesen += Double(b.frames); seitPruefung += Double(b.frames)
            if gesamtFrames > 0 { fort.melde(min(0.999, gelesen / gesamtFrames)) }
            if seitPruefung >= 0.5 * rate {
                seitPruefung = 0
                try pruefeAbbruch(abbruch, ctx)
            }
        }
        try pruefeAbbruch(abbruch, ctx)
        try umtaster.schliesse { p, n in try wav.schreibe(p, n) }
        try wav.schliesse()
    } catch {
        leser.abbrechen()
        wav.verwerfe()
        throw error
    }
    fort.melde(1)
    return ["samples": wav.frames, "dauer_s": Double(wav.frames) / 16000, "ms": (jetzt() - t0) * 1000,
            "quelle_rate": rate, "quelle_kanaele": ch]
}

@_cdecl("rt_dekodiere_wav16k")
public func rt_dekodiere_wav16k(_ pfad: UnsafePointer<CChar>?, _ ziel: UnsafePointer<CChar>?,
                                _ start: Double, _ dauer: Double,
                                _ abbruch: RTAbbruchCb?, _ fortschritt: RTFortschrittCb?,
                                _ ctx: UnsafeMutableRawPointer?) -> UnsafeMutablePointer<CChar>? {
    guard let pfad, let ziel else { return jsonString(["error": "pfad/ziel_wav ist NULL"]) }
    do {
        return jsonString(try dekodiereWav16k(pfad: String(cString: pfad), ziel: String(cString: ziel),
                                              start: start, dauer: dauer, abbruch: abbruch, fortschritt: fortschritt, ctx: ctx))
    } catch { return jsonFehler(error) }
}
