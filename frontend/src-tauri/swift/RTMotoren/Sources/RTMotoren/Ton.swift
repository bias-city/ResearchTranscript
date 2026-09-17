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

protocol BlockQuelle: AnyObject {
    var rate: Double { get }
    var channels: Int { get }
    func naechster() throws -> NativBlock?
    func abbrechen()
}

/// AVAudioFile (CoreAudio) mit framePosition: sample-genaues Seeking auch in VBR-mp3
/// (CoreAudio baut die Pakettabelle; AVAssetReader.timeRange interpoliert nur den Xing-TOC
/// und liegt bis ±1 s daneben). PTS aus dem Frame-Zähler.
final class DateiLeser: BlockQuelle {
    let datei: AVAudioFile
    let rate: Double
    let channels: Int
    private var pos: AVAudioFramePosition
    private let ende: AVAudioFramePosition
    private var fertig = false

    /// Liest [start−vorlauf, start+dauer+vorlauf); der Aufrufer schneidet im 16-kHz-Raster.
    init(url: URL, start: Double, dauer: Double, vorlauf: Double) throws {
        datei = try AVAudioFile(forReading: url, commonFormat: .pcmFormatFloat32, interleaved: true)
        rate = datei.processingFormat.sampleRate
        channels = Int(datei.processingFormat.channelCount)
        guard rate > 0, channels > 0 else { throw RTFehler("AVAudioFile ohne Format") }
        pos = max(0, AVAudioFramePosition(((start - vorlauf) * rate).rounded()))
        ende = min(datei.length, AVAudioFramePosition(((start + dauer + vorlauf) * rate).rounded()))
        datei.framePosition = pos
    }

    func naechster() throws -> NativBlock? {
        guard !fertig, pos < ende else { return nil }
        let n = AVAudioFrameCount(min(65536, ende - pos))
        let buf = AVAudioPCMBuffer(pcmFormat: datei.processingFormat, frameCapacity: n)!
        try datei.read(into: buf, frameCount: n)
        let got = Int(buf.frameLength)
        if got == 0 { fertig = true; return nil }
        let s = Array(UnsafeBufferPointer(start: buf.floatChannelData![0], count: got * channels))
        let b = NativBlock(samples: s, frames: got, pts: Double(pos) / rate)
        pos += AVAudioFramePosition(got)
        return b
    }

    func abbrechen() { fertig = true }
}

/// AVAssetReader → Linear-PCM Float32 in nativer Rate/Kanalzahl, blockweise.
final class NativLeser: BlockQuelle {
    let asset: AVURLAsset
    let track: AVAssetTrack
    let rate: Double
    let channels: Int
    let trackDauer: Double
    private let reader: AVAssetReader
    private let output: AVAssetReaderTrackOutput

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
///
/// Dem Konverter wird NIE `.noDataNow` gemeldet: gerechnet wird nur, wenn ein voller Block
/// Reserve im Vorrat liegt, und die Ausgabegrösse ist so begrenzt, dass der Konverter nicht
/// mehr Eingabe zieht, als da ist. Sonst hängt die Länge des Ergebnisses (Flush der
/// Filterverzögerung, 192 Samples) davon ab, wie der Reader die Blöcke schneidet — das war
/// unter Parallellast messbar (59 032 555 vs. 59 032 747 Samples bei 1 h).
final class Umtaster {
    private let srcF: AVAudioFormat
    private let dstF: AVAudioFormat
    private let conv: AVAudioConverter
    private let ratio: Double
    private var vorrat: [Float] = []
    private var eof = false
    let block = 65536
    let outMax = 32768

    init(rate: Double, ziel: Double = 16000) throws {
        srcF = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: rate, channels: 1, interleaved: false)!
        dstF = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: ziel, channels: 1, interleaved: false)!
        guard let c = AVAudioConverter(from: srcF, to: dstF) else { throw RTFehler("AVAudioConverter \(rate)→\(ziel) nicht anlegbar") }
        c.sampleRateConverterQuality = AVAudioQuality.max.rawValue
        conv = c
        ratio = ziel / rate
    }

    /// Samples anhängen; liefert fertige 16-kHz-Samples, sobald genug Vorrat da ist.
    func fuettere(_ mono: [Float], _ sink: (UnsafePointer<Float>, Int) throws -> Void) throws {
        vorrat.append(contentsOf: mono)
        if vorrat.count >= 3 * block { try laufe(sink) }
    }

    func schliesse(_ sink: (UnsafePointer<Float>, Int) throws -> Void) throws {
        eof = true
        try laufe(sink)
    }

    private func laufe(_ sink: (UnsafePointer<Float>, Int) throws -> Void) throws {
        var pos = 0
        while true {
            let rest = vorrat.count - pos
            let outCap: Int
            if eof {
                outCap = outMax
            } else {
                // Ein Block bleibt als Reserve für den Vorgriff des Filters; Ausgabe nur so gross,
                // wie es die restliche Eingabe sicher hergibt.
                guard rest >= 2 * block else { break }
                outCap = min(outMax, Int(Double(rest - block) * ratio) - 64)
                guard outCap > 0 else { break }
            }
            let outBuf = AVAudioPCMBuffer(pcmFormat: dstF, frameCapacity: AVAudioFrameCount(outCap))!
            var err: NSError?
            let st = conv.convert(to: outBuf, error: &err) { [self] _, status in
                let r = vorrat.count - pos
                if r <= 0 {
                    status.pointee = eof ? .endOfStream : .noDataNow   // .noDataNow: nur theoretisch
                    return nil
                }
                let n = min(block, r)
                let inBuf = AVAudioPCMBuffer(pcmFormat: srcF, frameCapacity: AVAudioFrameCount(n))!
                inBuf.frameLength = AVAudioFrameCount(n)
                vorrat.withUnsafeBufferPointer { inBuf.floatChannelData![0].update(from: $0.baseAddress! + pos, count: n) }
                pos += n
                status.pointee = .haveData
                return inBuf
            }
            if let e = err { throw e }
            if outBuf.frameLength > 0 { try sink(outBuf.floatChannelData![0], Int(outBuf.frameLength)) }
            if st == .error { throw RTFehler("AVAudioConverter: error") }
            if eof {
                if st == .endOfStream || outBuf.frameLength == 0 { break }
            } else if st == .inputRanDry || st == .endOfStream {
                break
            }
        }
        vorrat.removeFirst(pos)
    }
}

/// Kern: Datei (Ausschnitt) → 16-kHz-mono-s16-WAV, streamend, mit Abbruch/Fortschritt.
///
/// Ausschnitt: Quelle mit 0,5 s Vor- und Nachlauf lesen, ALLES durch den Umtaster und erst
/// im 16-kHz-Raster auf [start, start+dauer) schneiden — so ist der Ausschnitt ein Stück des
/// Volldekodats (kein Einschwingen/Ausklingen des Umtasters an den Schnittkanten).
/// Leser je Container: mp3/wav/aiff/caf/flac → AVAudioFile (sample-genaues Seeking, auch
/// VBR-mp3; AVAssetReader.timeRange liegt dort bis ±1 s daneben); mp4/mov/m4a →
/// AVAssetReader.timeRange (Sample-Tabelle, exakt; AVAudioFile ignoriert bei .mov die
/// Edit-Liste → 23 ms früh); Ogg und Unbekanntes → AVAssetReader von vorn (Ogg-Seeking
/// landet ~37 % zu spät und meldet trotzdem die Soll-PTS).
func dekodiereWav16k(pfad: String, ziel: String, start: Double, dauer: Double,
                     abbruch: RTAbbruchCb?, fortschritt: RTFortschrittCb?, ctx: UnsafeMutableRawPointer?) throws -> [String: Any] {
    let t0 = jetzt()
    let url = URL(fileURLWithPath: pfad)
    let ausschnitt = dauer > 0
    let vorlauf = 0.5
    let leser: BlockQuelle
    var trackDauer = 0.0
    var quelle = "reader"
    let ext = url.pathExtension.lowercased()
    if ausschnitt && ["mp3", "wav", "wave", "aiff", "aif", "caf", "flac"].contains(ext) {
        leser = try DateiLeser(url: url, start: start, dauer: dauer, vorlauf: vorlauf); quelle = "audiofile"
    } else {
        var tr: CMTimeRange? = nil
        if ausschnitt && ["mp4", "m4v", "mov", "m4a", "3gp", "aac"].contains(ext) {
            let s = max(0, start - vorlauf)
            tr = CMTimeRange(start: CMTime(seconds: s, preferredTimescale: 48000),
                             duration: CMTime(seconds: start + dauer - s + vorlauf, preferredTimescale: 48000))
            quelle = "reader-timerange"
        } else if ausschnitt { quelle = "reader-von-vorn" }
        let n = try NativLeser(url: url, timeRange: tr)
        leser = n; trackDauer = n.trackDauer
    }
    let rate = leser.rate, ch = leser.channels
    guard rate > 0, ch > 0 else { throw RTFehler("Tonspur ohne Format (rate=\(rate) ch=\(ch))") }
    let fort = Fortschritt(fortschritt, ctx)
    let gesamtFrames = ausschnitt ? (dauer + 2 * vorlauf) * rate : trackDauer * rate
    let leseEnde = start + dauer + vorlauf          // native Zeit, bis zu der gelesen wird
    // mp3: der Reader liefert das LAME-Padding am Ende mal mit, mal nicht (162 708 480 oder
    // 162 709 009 Frames bei 1 h, auch sequenziell) → auf die nominelle Spurlänge kappen.
    let kappe = (!ausschnitt && ext == "mp3" && trackDauer > 0) ? Int((trackDauer * rate).rounded()) : Int.max
    let umtaster = try Umtaster(rate: rate)
    let wav = try WavSchreiber(pfad: ziel, rate: 16000)
    var gelesen = 0.0            // native Frames, die in den Umtaster gingen (für Fortschritt)
    var seitPruefung = 0.0
    // Schnitt im 16-kHz-Raster: [skip, skip+behalte) der Umtaster-Ausgabe.
    var skip = 0, behalte = Int.max, outPos = 0
    var erster = true
    var fertig = false
    let sink: (UnsafePointer<Float>, Int) throws -> Void = { p, n in
        let von = max(skip, outPos), bis = min(skip + behalte, outPos + n)
        if bis > von { try wav.schreibe(p + (von - outPos), bis - von) }
        outPos += n
        if outPos >= skip + behalte { fertig = true }
    }
    do {
        try pruefeAbbruch(abbruch, ctx)
        fort.melde(0)
        while !fertig, let b = try leser.naechster() {
            if ausschnitt {
                if erster {
                    erster = false
                    // Reader ohne timeRange liefert ab 0; mit timeRange/AVAudioFile ab dem Vorlauf.
                    let p0 = b.pts
                    skip = max(0, Int(((start - p0) * 16000).rounded()))
                    behalte = Int((dauer * 16000).rounded())
                }
                if b.pts >= leseEnde { break }
            }
            var b = b
            if Int(gelesen) + b.frames > kappe {
                let n = max(0, kappe - Int(gelesen))
                if n == 0 { break }
                b.samples = Array(b.samples[0..<(n * ch)]); b.frames = n
            }
            let mono = downmix(b.samples, frames: b.frames, channels: ch)
            try umtaster.fuettere(mono, sink)
            gelesen += Double(b.frames); seitPruefung += Double(b.frames)
            if gesamtFrames > 0 { fort.melde(min(0.999, gelesen / gesamtFrames)) }
            if seitPruefung >= 0.5 * rate {
                seitPruefung = 0
                try pruefeAbbruch(abbruch, ctx)
            }
        }
        try pruefeAbbruch(abbruch, ctx)
        if !fertig { try umtaster.schliesse(sink) }
        leser.abbrechen()
        try wav.schliesse()
    } catch {
        leser.abbrechen()
        wav.verwerfe()
        throw error
    }
    fort.melde(1)
    return ["samples": wav.frames, "dauer_s": Double(wav.frames) / 16000, "ms": (jetzt() - t0) * 1000,
            "quelle_rate": rate, "quelle_kanaele": ch, "quelle_frames": Int(gelesen), "leser": quelle]
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
