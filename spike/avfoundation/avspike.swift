// avspike — Phase-0-Nebenmessung M4: kann AVFoundation ffmpeg ersetzen?
// Bauen: swiftc -O avspike.swift -o avspike -framework AVFoundation \
//        -framework AudioToolbox -framework Accelerate
// Unterbefehle:
//   decode <datei> <ref.wav>         16 kHz mono f32 via AVAssetReader, Vergleich mit ffmpeg-Referenz
//   probe  <datei>                    Spuren: Codec-Tag, Masse, Dauer, Ton-Codec
//   clip   <datei> <start> <dauer> <out.wav>   Ausschnitt per timeRange
//   mp3writer <datei> <out.mp3>       AVAssetWriter + kAudioFormatMPEGLayer3 (Erwartung: NSException)
//   mp3converter                      AudioConverterNew / AudioFormat-Encoderliste
//   mp3lame <datei> <out.mp3> [dylib] libmp3lame per dlopen, VBR q2 wie ffmpeg -q:a 2
import AVFoundation
import AudioToolbox
import Accelerate
import Foundation

// ---------- Hilfen ----------

func jetzt() -> Double { CFAbsoluteTimeGetCurrent() }

func fehler(_ s: String) -> Never {
    FileHandle.standardError.write((s + "\n").data(using: .utf8)!)
    exit(1)
}

func fourcc(_ v: FourCharCode) -> String {
    let b = [UInt8(v >> 24 & 0xff), UInt8(v >> 16 & 0xff), UInt8(v >> 8 & 0xff), UInt8(v & 0xff)]
    return String(bytes: b, encoding: .macOSRoman) ?? "????"
}

/// Referenz-WAV (pcm_s16le, wie ffmpeg es schreibt) als Float.
func leseWav(_ pfad: String) -> (samples: [Float], rate: Int, channels: Int) {
    guard let d = FileManager.default.contents(atPath: pfad) else { fehler("WAV fehlt: \(pfad)") }
    return d.withUnsafeBytes { raw -> ([Float], Int, Int) in
        let p = raw.baseAddress!
        var off = 12
        var rate = 0, ch = 0, bits = 0
        var samples: [Float] = []
        while off + 8 <= d.count {
            let id = String(bytes: raw[off..<off+4], encoding: .ascii) ?? ""
            let size = Int(p.load(fromByteOffset: off + 4, as: UInt32.self))
            if id == "fmt " {
                ch = Int(p.load(fromByteOffset: off + 10, as: UInt16.self))
                rate = Int(p.load(fromByteOffset: off + 12, as: UInt32.self))
                bits = Int(p.load(fromByteOffset: off + 22, as: UInt16.self))
            } else if id == "data" {
                precondition(bits == 16, "nur s16 erwartet")
                let n = min(size, d.count - off - 8) / 2
                samples = [Float](repeating: 0, count: n)
                let src = p.advanced(by: off + 8).assumingMemoryBound(to: Int16.self)
                for i in 0..<n { samples[i] = Float(src[i]) / 32768 }
                break
            }
            off += 8 + size + (size & 1)
        }
        return (samples, rate, ch)
    }
}

func schreibeWav16(_ pfad: String, _ samples: [Float], rate: Int = 16000) {
    var d = Data()
    func u32(_ v: UInt32) { var x = v.littleEndian; d.append(Data(bytes: &x, count: 4)) }
    func u16(_ v: UInt16) { var x = v.littleEndian; d.append(Data(bytes: &x, count: 2)) }
    let bytes = samples.count * 2
    d.append("RIFF".data(using: .ascii)!); u32(UInt32(36 + bytes)); d.append("WAVE".data(using: .ascii)!)
    d.append("fmt ".data(using: .ascii)!); u32(16); u16(1); u16(1); u32(UInt32(rate)); u32(UInt32(rate * 2)); u16(2); u16(16)
    d.append("data".data(using: .ascii)!); u32(UInt32(bytes))
    var pcm = [Int16](repeating: 0, count: samples.count)
    for i in 0..<samples.count { pcm[i] = Int16(max(-32768, min(32767, (samples[i] * 32768).rounded()))) }
    pcm.withUnsafeBytes { d.append(contentsOf: $0) }
    try! d.write(to: URL(fileURLWithPath: pfad))
}

// ---------- Dekodieren ----------

struct Dekodiert {
    var samples: [Float]       // interleaved
    var rate: Double
    var channels: Int
    var sekunden: Double
    var quelle: String = ""
}

/// AVAssetReader → Linear-PCM Float32. rate/channels nil = nativ (TrackOutput),
/// sonst AudioMixOutput mit Umtastung/Downmix (16 kHz mono für Whisper).
func dekodiere(_ url: URL, rate: Double?, channels: Int?, timeRange: CMTimeRange? = nil) throws -> Dekodiert {
    let t0 = jetzt()
    let asset = AVURLAsset(url: url)
    let tracks = asset.tracks(withMediaType: .audio)
    guard !tracks.isEmpty else {
        throw NSError(domain: "avspike", code: 1, userInfo: [NSLocalizedDescriptionKey: "keine Tonspur (tracks(.audio) leer; asset.tracks=\(asset.tracks.count))"])
    }
    let reader = try AVAssetReader(asset: asset)
    var settings: [String: Any] = [
        AVFormatIDKey: kAudioFormatLinearPCM,
        AVLinearPCMBitDepthKey: 32,
        AVLinearPCMIsFloatKey: true,
        AVLinearPCMIsBigEndianKey: false,
        AVLinearPCMIsNonInterleaved: false,
    ]
    let output: AVAssetReaderOutput
    if let r = rate, let c = channels {
        settings[AVSampleRateKey] = r
        settings[AVNumberOfChannelsKey] = c
        if ProcessInfo.processInfo.environment["AVSPIKE_MODE"] == "track" {
            output = AVAssetReaderTrackOutput(track: tracks[0], outputSettings: settings)
        } else {
            output = AVAssetReaderAudioMixOutput(audioTracks: [tracks[0]], audioSettings: settings)
        }
    } else {
        output = AVAssetReaderTrackOutput(track: tracks[0], outputSettings: settings)
    }
    output.alwaysCopiesSampleData = false
    reader.add(output)
    if let tr = timeRange { reader.timeRange = tr }
    guard reader.startReading() else {
        throw reader.error ?? NSError(domain: "avspike", code: 2, userInfo: [NSLocalizedDescriptionKey: "startReading false"])
    }
    var out: [Float] = []
    var gotRate = 0.0, gotCh = 0
    while let sb = output.copyNextSampleBuffer() {
        if gotCh == 0, let fd = CMSampleBufferGetFormatDescription(sb),
           let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(fd) {
            gotRate = asbd.pointee.mSampleRate; gotCh = Int(asbd.pointee.mChannelsPerFrame)
        }
        guard let bb = CMSampleBufferGetDataBuffer(sb) else { continue }
        var len = 0
        var ptr: UnsafeMutablePointer<Int8>?
        CMBlockBufferGetDataPointer(bb, atOffset: 0, lengthAtOffsetOut: nil, totalLengthOut: &len, dataPointerOut: &ptr)
        if let p = ptr {
            let n = len / 4
            p.withMemoryRebound(to: Float.self, capacity: n) { out.append(contentsOf: UnsafeBufferPointer(start: $0, count: n)) }
        }
    }
    if reader.status == .failed { throw reader.error ?? NSError(domain: "avspike", code: 3) }
    return Dekodiert(samples: out, rate: gotRate, channels: gotCh, sekunden: jetzt() - t0)
}

/// Alternativer Weg: AVAudioFile (CoreAudio AudioFile, kennt FLAC) + AVAudioConverter → 16 kHz mono.
func dekodiereAudioFile(_ url: URL) throws -> Dekodiert {
    let t0 = jetzt()
    let f = try AVAudioFile(forReading: url)
    let src = f.processingFormat
    let dst = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: 16000, channels: 1, interleaved: false)!
    guard let conv = AVAudioConverter(from: src, to: dst) else { throw NSError(domain: "avspike", code: 4, userInfo: [NSLocalizedDescriptionKey: "AVAudioConverter nil"]) }
    conv.sampleRateConverterQuality = AVAudioQuality.max.rawValue
    let inBuf = AVAudioPCMBuffer(pcmFormat: src, frameCapacity: 65536)!
    var out: [Float] = []
    var eof = false
    while !eof {
        let outBuf = AVAudioPCMBuffer(pcmFormat: dst, frameCapacity: 32768)!
        var err: NSError?
        let st = conv.convert(to: outBuf, error: &err) { _, status in
            if eof { status.pointee = .endOfStream; return nil }
            inBuf.frameLength = 0
            do { try f.read(into: inBuf) } catch { FileHandle.standardError.write("AVAudioFile.read: \(error)\n".data(using: .utf8)!); status.pointee = .endOfStream; eof = true; return nil }
            if inBuf.frameLength == 0 { status.pointee = .endOfStream; eof = true; return nil }
            status.pointee = .haveData; return inBuf
        }
        if let e = err { throw e }
        out.append(contentsOf: UnsafeBufferPointer(start: outBuf.floatChannelData![0], count: Int(outBuf.frameLength)))
        if st == .endOfStream || st == .error { break }
        if st == .inputRanDry && eof && outBuf.frameLength == 0 { break }
    }
    return Dekodiert(samples: out, rate: 16000, channels: 1, sekunden: jetzt() - t0, quelle: String(format: "AVAudioFile %@ %.0f Hz ch=%d frames=%lld", fourcc(src.streamDescription.pointee.mFormatID), src.sampleRate, src.channelCount, f.length))
}

/// Empfohlener Weg: nativ dekodieren (kein SRC im Reader), (L+R)/n selbst mischen, AVAudioConverter (Qualität max) → 16 kHz.
func dekodiereNativ(_ url: URL) throws -> Dekodiert {
    let t0 = jetzt()
    let nat = try dekodiere(url, rate: nil, channels: nil)
    let ch = nat.channels, frames = nat.samples.count / ch
    var mono = [Float](repeating: 0, count: frames)
    if ch == 1 { mono = nat.samples } else {
        for c in 0..<ch { vDSP_vadd(mono, 1, Array(nat.samples[c...]).withUnsafeBufferPointer { $0.baseAddress! }, vDSP_Stride(ch), &mono, 1, vDSP_Length(frames)) }
        var k = 1 / Float(ch); vDSP_vsmul(mono, 1, &k, &mono, 1, vDSP_Length(frames))
    }
    let srcF = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: nat.rate, channels: 1, interleaved: false)!
    let dstF = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: 16000, channels: 1, interleaved: false)!
    let conv = AVAudioConverter(from: srcF, to: dstF)!
    conv.sampleRateConverterQuality = AVAudioQuality.max.rawValue
    var out: [Float] = []
    let block = 65536
    var pos = 0
    var eof = false
    while !eof {
        let outBuf = AVAudioPCMBuffer(pcmFormat: dstF, frameCapacity: 32768)!
        var err: NSError?
        let st = conv.convert(to: outBuf, error: &err) { _, status in
            if pos >= frames { status.pointee = .endOfStream; eof = true; return nil }
            let n = min(block, frames - pos)
            let inBuf = AVAudioPCMBuffer(pcmFormat: srcF, frameCapacity: AVAudioFrameCount(n))!
            inBuf.frameLength = AVAudioFrameCount(n)
            mono.withUnsafeBufferPointer { inBuf.floatChannelData![0].update(from: $0.baseAddress! + pos, count: n) }
            pos += n; status.pointee = .haveData; return inBuf
        }
        if let e = err { throw e }
        out.append(contentsOf: UnsafeBufferPointer(start: outBuf.floatChannelData![0], count: Int(outBuf.frameLength)))
        if st == .endOfStream || st == .error || (st == .inputRanDry && outBuf.frameLength == 0) { break }
    }
    return Dekodiert(samples: out, rate: 16000, channels: 1, sekunden: jetzt() - t0, quelle: String(format: "nativ %.0f Hz ch=%d (Reader %.3f s)", nat.rate, ch, nat.sekunden))
}

/// Kreuzkorrelation über die ersten `fenster` Sekunden, Lags ±maxLag Samples.
/// Ergebnis: lag mit  dec[i] ≈ ref[i + lag].
func versatz(_ dec: [Float], _ ref: [Float], rate: Int, fenster: Double = 10, maxLagWunsch: Int = 1600) -> (lag: Int, korr: Float) {
    let maxLag = min(maxLagWunsch, min(dec.count, ref.count) / 4)
    let m = min(Int(fenster * Double(rate)), dec.count - 2 * maxLag, ref.count - 2 * maxLag)
    guard m > rate / 4 else { return (0, 0) }
    let f = Array(dec[maxLag..<(maxLag + m)])                  // Filter: Fenster aus dec
    let a = Array(ref[0..<(m + 2 * maxLag)])                   // Signal: ref mit Rand
    var c = [Float](repeating: 0, count: 2 * maxLag + 1)
    vDSP_conv(a, 1, f, 1, &c, 1, vDSP_Length(c.count), vDSP_Length(m))
    var best = 0; var bestV: Float = -Float.greatestFiniteMagnitude
    for (i, v) in c.enumerated() where v > bestV { bestV = v; best = i }
    // Normierung
    var ef: Float = 0; vDSP_dotpr(f, 1, f, 1, &ef, vDSP_Length(m))
    let aa = Array(a[best..<(best + m)])
    var ea: Float = 0; vDSP_dotpr(aa, 1, aa, 1, &ea, vDSP_Length(m))
    return (best - maxLag, bestV / (sqrt(ef * ea) + 1e-12))
}

func vergleiche(_ dec: [Float], _ ref: [Float], rate: Int) -> String {
    let (lag, korr) = versatz(dec, ref, rate: rate)
    // Überlappung nach Ausrichtung: dec[i] ↔ ref[i+lag]
    let i0 = max(0, -lag), i1 = min(dec.count, ref.count - lag)
    var maxDiff: Float = 0, sumSq: Double = 0, sumRef: Double = 0, sumDec: Double = 0, dot: Double = 0
    if i1 > i0 {
        for i in i0..<i1 {
            let d = dec[i] - ref[i + lag]
            maxDiff = max(maxDiff, abs(d)); sumSq += Double(d * d)
            sumRef += Double(ref[i + lag] * ref[i + lag]); sumDec += Double(dec[i] * dec[i]); dot += Double(dec[i] * ref[i + lag])
        }
    }
    var peakDec: Float = 0, peakRef: Float = 0
    vDSP_maxmgv(dec, 1, &peakDec, vDSP_Length(dec.count)); vDSP_maxmgv(ref, 1, &peakRef, vDSP_Length(ref.count))
    let clipped = dec.filter { abs($0) >= 0.999 }.count
    let n = Double(max(1, i1 - i0))
    // Bandbegrenzt (Tiefpass ~3,4 kHz, 63-Tap-Sinc): was Whisper hauptsächlich sieht
    var snrTief = 0.0
    if i1 - i0 > 4000 {
        let taps = 63, fc: Float = 3400 / Float(rate)
        var h = (0..<taps).map { i -> Float in
            let k = Float(i - taps / 2)
            let sinc: Float = k == 0 ? 2 * fc : sin(2 * .pi * fc * k) / (.pi * k)
            return sinc * (0.54 - 0.46 * cos(2 * .pi * Float(i) / Float(taps - 1)))
        }
        let hs = h.reduce(0, +); h = h.map { $0 / hs }
        let a = Array(dec[i0..<i1]), b = Array(ref[(i0 + lag)..<(i1 + lag)])
        let nn = a.count - taps
        var fa = [Float](repeating: 0, count: nn), fb = [Float](repeating: 0, count: nn)
        vDSP_conv(a, 1, h, 1, &fa, 1, vDSP_Length(nn), vDSP_Length(taps))
        vDSP_conv(b, 1, h, 1, &fb, 1, vDSP_Length(nn), vDSP_Length(taps))
        var d = [Float](repeating: 0, count: nn); vDSP_vsub(fb, 1, fa, 1, &d, 1, vDSP_Length(nn))
        var ed: Float = 0, eb: Float = 0; vDSP_dotpr(d, 1, d, 1, &ed, vDSP_Length(nn)); vDSP_dotpr(fb, 1, fb, 1, &eb, vDSP_Length(nn))
        snrTief = ed > 0 ? 10 * log10(Double(eb / ed)) : 999
    }
    let rmsDiff = sqrt(sumSq / n), rmsRef = sqrt(sumRef / n)
    let gain = sumRef > 0 ? dot / sumRef : 0
    let snr = rmsDiff > 0 ? 20 * log10(rmsRef / rmsDiff) : 999
    return String(format: "samples dec=%d ref=%d (Δ=%+d = %+.1f ms) | Versatz lag=%+d Samples (%+.2f ms, r=%.4f) | nach Ausrichtung: maxAbw=%.5f (%.1f LSB16) rmsAbw=%.6f SNR=%.1f dB (<3,4 kHz: %.1f dB) Gain(dec/ref)=%.4f | Peak dec=%.3f ref=%.3f Clip≥0.999: %d",
                  dec.count, ref.count, dec.count - ref.count, Double(dec.count - ref.count) / Double(rate) * 1000,
                  lag, Double(lag) / Double(rate) * 1000, korr, maxDiff, maxDiff * 32768, rmsDiff, snr, snrTief, gain, peakDec, peakRef, clipped)
}

// ---------- Sondieren ----------

func sondiere(_ url: URL) {
    let asset = AVURLAsset(url: url)
    let d = asset.duration
    print("dauer_s=\(String(format: "%.3f", CMTimeGetSeconds(d))) (timescale \(d.timescale)) readable=\(asset.isReadable) playable=\(asset.isPlayable)")
    for t in asset.tracks {
        var zeile = "track \(t.trackID) \(t.mediaType.rawValue)"
        for fd in t.formatDescriptions as! [CMFormatDescription] {
            let sub = CMFormatDescriptionGetMediaSubType(fd)
            zeile += " codec=\(fourcc(sub))"
            if t.mediaType == .video {
                let dim = CMVideoFormatDescriptionGetDimensions(fd)
                zeile += " \(dim.width)x\(dim.height) natural=\(Int(t.naturalSize.width))x\(Int(t.naturalSize.height)) fps=\(String(format: "%.2f", t.nominalFrameRate))"
                if let ext = CMFormatDescriptionGetExtension(fd, extensionKey: kCMFormatDescriptionExtension_FormatName) { zeile += " name='\(ext)'" }
            } else if t.mediaType == .audio, let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(fd) {
                zeile += " \(Int(asbd.pointee.mSampleRate)) Hz ch=\(asbd.pointee.mChannelsPerFrame)"
            }
        }
        zeile += String(format: " dauer=%.3f bitrate=%.0f", CMTimeGetSeconds(t.timeRange.duration), t.estimatedDataRate)
        print(zeile)
    }
}

// ---------- MP3 via Apple ----------

func mp3Writer(_ inUrl: URL, _ outUrl: URL) {
    // Erwartung: AVAssetWriterInput wirft NSException «not a supported output format» — Swift kann sie
    // nicht fangen; der Aufrufer liest stderr des Kindprozesses.
    try? FileManager.default.removeItem(at: outUrl)
    let writer = try! AVAssetWriter(outputURL: outUrl, fileType: .mp3)
    let settings: [String: Any] = [AVFormatIDKey: kAudioFormatMPEGLayer3, AVSampleRateKey: 44100, AVNumberOfChannelsKey: 1, AVEncoderBitRateKey: 192000]
    print("AVAssetWriter(.mp3) angelegt; canApply=\(writer.canApply(outputSettings: settings, forMediaType: .audio))")
    let input = AVAssetWriterInput(mediaType: .audio, outputSettings: settings)
    writer.add(input)
    print("Input hinzugefügt (unerwartet) — startWriting=\(writer.startWriting()) error=\(String(describing: writer.error))")
}

func mp3Converter() {
    // 1. Welche Encoder kennt AudioToolbox?
    var size: UInt32 = 0
    var st = AudioFormatGetPropertyInfo(kAudioFormatProperty_EncodeFormatIDs, 0, nil, &size)
    print("EncodeFormatIDs: status=\(st) bytes=\(size)")
    if st == noErr {
        var ids = [AudioFormatID](repeating: 0, count: Int(size) / 4)
        st = AudioFormatGetProperty(kAudioFormatProperty_EncodeFormatIDs, 0, nil, &size, &ids)
        print("  Encoder-Format-IDs: " + ids.map { fourcc($0) }.joined(separator: " "))
        print("  enthält MPEGLayer3 ('.mp3')? \(ids.contains(kAudioFormatMPEGLayer3))")
    }
    var dsize: UInt32 = 0
    st = AudioFormatGetPropertyInfo(kAudioFormatProperty_DecodeFormatIDs, 0, nil, &dsize)
    if st == noErr {
        var ids = [AudioFormatID](repeating: 0, count: Int(dsize) / 4)
        AudioFormatGetProperty(kAudioFormatProperty_DecodeFormatIDs, 0, nil, &dsize, &ids)
        print("  Decoder-Format-IDs: " + ids.map { fourcc($0) }.joined(separator: " "))
    }
    // 2. AudioConverterNew PCM → MP3
    var src = AudioStreamBasicDescription(mSampleRate: 44100, mFormatID: kAudioFormatLinearPCM,
        mFormatFlags: kAudioFormatFlagIsFloat | kAudioFormatFlagIsPacked, mBytesPerPacket: 4, mFramesPerPacket: 1,
        mBytesPerFrame: 4, mChannelsPerFrame: 1, mBitsPerChannel: 32, mReserved: 0)
    var dst = AudioStreamBasicDescription(mSampleRate: 44100, mFormatID: kAudioFormatMPEGLayer3,
        mFormatFlags: 0, mBytesPerPacket: 0, mFramesPerPacket: 1152, mBytesPerFrame: 0, mChannelsPerFrame: 1, mBitsPerChannel: 0, mReserved: 0)
    var conv: AudioConverterRef?
    st = AudioConverterNew(&src, &dst, &conv)
    print("AudioConverterNew(PCM→MPEGLayer3): status=\(st) (\(fourcc(UInt32(bitPattern: st)))) \(st == kAudioConverterErr_FormatNotSupported ? "= kAudioConverterErr_FormatNotSupported" : "")")
    if let c = conv { AudioConverterDispose(c) }
    // Gegenprobe: PCM → AAC muss gehen
    var aac = dst; aac.mFormatID = kAudioFormatMPEG4AAC; aac.mFramesPerPacket = 1024
    st = AudioConverterNew(&src, &aac, &conv)
    print("AudioConverterNew(PCM→AAC) Gegenprobe: status=\(st)")
    if let c = conv { AudioConverterDispose(c) }
    // 3. ExtAudioFile mit MP3-Dateityp
    var ext: ExtAudioFileRef?
    let url = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("avspike-test.mp3")
    st = ExtAudioFileCreateWithURL(url as CFURL, kAudioFileMP3Type, &dst, nil, AudioFileFlags.eraseFile.rawValue, &ext)
    print("ExtAudioFileCreateWithURL(kAudioFileMP3Type, MPEGLayer3): status=\(st) (\(fourcc(UInt32(bitPattern: st))))")
    if let e = ext {
        st = ExtAudioFileSetProperty(e, kExtAudioFileProperty_ClientDataFormat, UInt32(MemoryLayout<AudioStreamBasicDescription>.size), &src)
        print("  ExtAudioFileSetProperty(ClientDataFormat=PCM): status=\(st) (\(fourcc(UInt32(bitPattern: st))))")
        var pcm = [Float](repeating: 0, count: 4096)
        var abl = AudioBufferList(mNumberBuffers: 1, mBuffers: AudioBuffer(mNumberChannels: 1, mDataByteSize: 4096 * 4, mData: &pcm))
        st = ExtAudioFileWrite(e, 4096, &abl)
        print("  ExtAudioFileWrite(4096 Frames): status=\(st) (\(fourcc(UInt32(bitPattern: st))))")
        ExtAudioFileDispose(e)
    }
    try? FileManager.default.removeItem(at: url)
}

// ---------- MP3 via LAME (dlopen) ----------

typealias LameT = OpaquePointer?
func mp3Lame(_ inUrl: URL, _ outPfad: String, dylib: String) throws {
    guard let h = dlopen(dylib, RTLD_NOW) else { fehler("dlopen fehlgeschlagen: \(String(cString: dlerror()))") }
    func sym<T>(_ n: String, _: T.Type) -> T {
        guard let p = dlsym(h, n) else { fehler("Symbol fehlt: \(n)") }
        return unsafeBitCast(p, to: T.self)
    }
    let get_lame_version = sym("get_lame_version", (@convention(c) () -> UnsafePointer<CChar>).self)
    let lame_init = sym("lame_init", (@convention(c) () -> LameT).self)
    let set_in_rate = sym("lame_set_in_samplerate", (@convention(c) (LameT, Int32) -> Int32).self)
    let set_ch = sym("lame_set_num_channels", (@convention(c) (LameT, Int32) -> Int32).self)
    let set_vbr = sym("lame_set_VBR", (@convention(c) (LameT, Int32) -> Int32).self)
    let set_vbr_q = sym("lame_set_VBR_quality", (@convention(c) (LameT, Float) -> Int32).self)
    let set_vbrtag = sym("lame_set_bWriteVbrTag", (@convention(c) (LameT, Int32) -> Int32).self)
    let set_id3auto = sym("lame_set_write_id3tag_automatic", (@convention(c) (LameT, Int32) -> Int32).self)
    let init_params = sym("lame_init_params", (@convention(c) (LameT) -> Int32).self)
    let enc_float = sym("lame_encode_buffer_ieee_float", (@convention(c) (LameT, UnsafePointer<Float>, UnsafePointer<Float>, Int32, UnsafeMutablePointer<UInt8>, Int32) -> Int32).self)
    let enc_il_float = sym("lame_encode_buffer_interleaved_ieee_float", (@convention(c) (LameT, UnsafePointer<Float>, Int32, UnsafeMutablePointer<UInt8>, Int32) -> Int32).self)
    let flush = sym("lame_encode_flush", (@convention(c) (LameT, UnsafeMutablePointer<UInt8>, Int32) -> Int32).self)
    let lametag = sym("lame_get_lametag_frame", (@convention(c) (LameT, UnsafeMutablePointer<UInt8>?, Int) -> Int).self)
    let close = sym("lame_close", (@convention(c) (LameT) -> Int32).self)
    let get_out_rate = sym("lame_get_out_samplerate", (@convention(c) (LameT) -> Int32).self)
    print("LAME \(String(cString: get_lame_version())) aus \(dylib)")

    // Wie ton_befehl/exporte: Quelle nativ dekodieren (ohne Umtastung), dann q2-VBR.
    let dec = try dekodiere(inUrl, rate: nil, channels: nil)
    print(String(format: "dekodiert nativ: %d Hz ch=%d frames=%d in %.3f s", Int(dec.rate), dec.channels, dec.samples.count / max(1, dec.channels), dec.sekunden))
    let t0 = jetzt()
    let gf = lame_init()
    _ = set_in_rate(gf, Int32(dec.rate)); _ = set_ch(gf, Int32(dec.channels))
    _ = set_vbr(gf, 4)           // vbr_mtrh = vbr_default, wie ffmpeg libmp3lame
    _ = set_vbr_q(gf, 2.0)       // ffmpeg -q:a 2 → lame_set_VBR_quality(2.0)
    _ = set_vbrtag(gf, 1); _ = set_id3auto(gf, 0)
    guard init_params(gf) >= 0 else { fehler("lame_init_params") }
    print("LAME out_samplerate=\(get_out_rate(gf))")
    let frames = dec.samples.count / dec.channels
    let chunk = 16384
    var buf = [UInt8](repeating: 0, count: Int(1.25 * Double(chunk)) + 7200)
    var mp3 = Data()
    // Platz für den Xing/LAME-Tag-Frame reservieren
    print("lametag-Grösse abfragen…")
    let tagSize = lametag(gf, nil, 0)
    print("tagSize=\(tagSize)")
    mp3.append(Data(count: tagSize))
    var pos = 0
    while pos < frames {
        let n = min(chunk, frames - pos)
        let w: Int32 = dec.samples.withUnsafeBufferPointer { p in
            let base = p.baseAddress! + pos * dec.channels
            return dec.channels == 2
                ? enc_il_float(gf, base, Int32(n), &buf, Int32(buf.count))
                : enc_float(gf, base, base, Int32(n), &buf, Int32(buf.count))
        }
        guard w >= 0 else { fehler("lame_encode_buffer: \(w)") }
        if pos == 0 { print("erster Block: \(w) Bytes") }
        mp3.append(buf, count: Int(w)); pos += n
    }
    let w = flush(gf, &buf, Int32(buf.count)); mp3.append(buf, count: Int(w))
    let need = lametag(gf, nil, 0)
    print("lametag nach flush: benötigt \(need) Bytes (reserviert \(tagSize))")
    if need > 0 {
        var tag = [UInt8](repeating: 0, count: need)
        let got = lametag(gf, &tag, need)
        // LAME schreibt im ersten Block bereits einen Platzhalter-Frame gleicher Grösse (bWriteVbrTag) — überschreiben.
        mp3.replaceSubrange(0..<got, with: tag[0..<got])
    }
    _ = close(gf)
    try mp3.write(to: URL(fileURLWithPath: outPfad))
    print(String(format: "MP3 geschrieben: %d Bytes, Kodierzeit %.3f s (ohne Dekodieren), %.1f× Echtzeit", mp3.count, jetzt() - t0, (Double(frames) / dec.rate) / (jetzt() - t0)))
}

// ---------- Kanal-Analyse (Downmix) ----------

/// Nativ dekodieren (Stereo), L / R / (L+R)/2 / 0,707(L+R) je einzeln per AVAudioConverter auf 16 kHz,
/// gegen die ffmpeg-Referenz und gegen den AudioMixOutput-Weg halten.
func kanalAnalyse(_ url: URL, refPfad: String) throws {
    let nat = try dekodiere(url, rate: nil, channels: nil)
    precondition(nat.channels == 2, "Stereo erwartet")
    let frames = nat.samples.count / 2
    var l = [Float](repeating: 0, count: frames), r = l
    for i in 0..<frames { l[i] = nat.samples[2 * i]; r[i] = nat.samples[2 * i + 1] }
    var lr: Float = 0; vDSP_dotpr(l, 1, r, 1, &lr, vDSP_Length(frames))
    var ll: Float = 0; vDSP_dotpr(l, 1, l, 1, &ll, vDSP_Length(frames))
    var rr: Float = 0; vDSP_dotpr(r, 1, r, 1, &rr, vDSP_Length(frames))
    print(String(format: "nativ %.0f Hz stereo, %d Frames; Korrelation L/R = %.3f, RMS L=%.4f R=%.4f", nat.rate, frames, lr / sqrt(ll * rr), sqrt(ll / Float(frames)), sqrt(rr / Float(frames))))
    func resample(_ x: [Float]) -> [Float] {
        let srcF = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: nat.rate, channels: 1, interleaved: false)!
        let dstF = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: 16000, channels: 1, interleaved: false)!
        let conv = AVAudioConverter(from: srcF, to: dstF)!
        conv.sampleRateConverterQuality = AVAudioQuality.max.rawValue
        let inBuf = AVAudioPCMBuffer(pcmFormat: srcF, frameCapacity: AVAudioFrameCount(x.count))!
        inBuf.frameLength = AVAudioFrameCount(x.count)
        x.withUnsafeBufferPointer { inBuf.floatChannelData![0].update(from: $0.baseAddress!, count: x.count) }
        let outBuf = AVAudioPCMBuffer(pcmFormat: dstF, frameCapacity: AVAudioFrameCount(Double(x.count) * 16000 / nat.rate) + 64)!
        var fed = false
        var err: NSError?
        _ = conv.convert(to: outBuf, error: &err) { _, status in
            if fed { status.pointee = .endOfStream; return nil }
            fed = true; status.pointee = .haveData; return inBuf
        }
        return Array(UnsafeBufferPointer(start: outBuf.floatChannelData![0], count: Int(outBuf.frameLength)))
    }
    let ref = leseWav(refPfad).samples
    let mix = try dekodiere(url, rate: 16000, channels: 1).samples
    var varianten: [(String, [Float])] = [("L", l), ("R", r)]
    var m05 = [Float](repeating: 0, count: frames), m07 = m05
    var k05: Float = 0.5, k07: Float = 0.70710678
    vDSP_vasm(l, 1, r, 1, &k05, &m05, 1, vDSP_Length(frames))
    vDSP_vasm(l, 1, r, 1, &k07, &m07, 1, vDSP_Length(frames))
    varianten += [("(L+R)/2", m05), ("0,707(L+R)", m07)]
    for (name, x) in varianten {
        let y = resample(x)
        print("  \(name) vs ffmpeg-Ref: " + vergleiche(y, ref, rate: 16000))
        print("  \(name) vs AudioMixOutput: " + vergleiche(y, mix, rate: 16000))
    }
}

// ---------- main ----------

setvbuf(stdout, nil, _IONBF, 0)
let args = CommandLine.arguments
guard args.count >= 2 else { fehler("Unterbefehl fehlt") }
do {
    switch args[1] {
    case "decode":
        let url = URL(fileURLWithPath: args[2])
        let mode = ProcessInfo.processInfo.environment["AVSPIKE_MODE"] ?? "mix"
        let dec = mode == "audiofile" ? try dekodiereAudioFile(url) : mode == "nativ" ? try dekodiereNativ(url) : try dekodiere(url, rate: 16000, channels: 1)
        if !dec.quelle.isEmpty { print(dec.quelle) }
        let ref = leseWav(args[3])
        precondition(ref.rate == 16000 && ref.channels == 1)
        print(String(format: "AVFoundation[\(mode)]: %.3f s (Datei→f32 16k mono, %d Samples, got %.0f Hz ch=%d)", dec.sekunden, dec.samples.count, dec.rate, dec.channels))
        print(vergleiche(dec.samples, ref.samples, rate: 16000))
        if args.count > 4 { schreibeWav16(args[4], dec.samples) }
    case "probe":
        sondiere(URL(fileURLWithPath: args[2]))
    case "clip":
        let start = Double(args[3])!, dauer = Double(args[4])!
        let tr = CMTimeRange(start: CMTime(seconds: start, preferredTimescale: 1000), duration: CMTime(seconds: dauer, preferredTimescale: 1000))
        let dec = try dekodiere(URL(fileURLWithPath: args[2]), rate: 16000, channels: 1, timeRange: tr)
        schreibeWav16(args[5], dec.samples)
        print(String(format: "Clip %.3f+%.3f s: %d Samples (= %.3f s) in %.3f s", start, dauer, dec.samples.count, Double(dec.samples.count) / 16000, dec.sekunden))
        if args.count > 6 {
            let ref = leseWav(args[6])
            print(vergleiche(dec.samples, ref.samples, rate: 16000))
        }
    case "chan":
        try kanalAnalyse(URL(fileURLWithPath: args[2]), refPfad: args[3])
    case "mp3writer":
        mp3Writer(URL(fileURLWithPath: args[2]), URL(fileURLWithPath: args[3]))
    case "mp3converter":
        mp3Converter()
    case "mp3lame":
        try mp3Lame(URL(fileURLWithPath: args[2]), args[3], dylib: args.count > 4 ? args[4] : "/opt/homebrew/opt/lame/lib/libmp3lame.dylib")
    default: fehler("unbekannt: \(args[1])")
    }
} catch {
    let e = error as NSError
    print("FEHLER: \(e.domain) \(e.code): \(e.localizedDescription) \(e.userInfo[NSLocalizedFailureReasonErrorKey] ?? "")")
    exit(2)
}
