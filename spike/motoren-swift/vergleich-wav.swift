// vergleich-wav — zwei 16-kHz-mono-s16-WAVs vergleichen (dec gegen ref).
// leseWav / versatz / vergleiche sind 1:1 aus spike/avfoundation/avspike.swift
// (dessen Vergleichsmetrik: Samplezahl, Kreuzkorrelation der ersten 10 s,
// maxAbw in LSB16, SNR breit und < 3,4 kHz, Gain).
// Bauen: swiftc -O vergleich-wav.swift -o vergleich-wav -framework Accelerate
// Aufruf: vergleich-wav <dec.wav> <ref.wav>
import Accelerate
import Foundation

func fehler(_ s: String) -> Never {
    FileHandle.standardError.write((s + "\n").data(using: .utf8)!)
    exit(1)
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

let args = CommandLine.arguments
guard args.count >= 3 else { fehler("Aufruf: vergleich-wav <dec.wav> <ref.wav>") }
let dec = leseWav(args[1]), ref = leseWav(args[2])
precondition(dec.rate == ref.rate && dec.channels == 1 && ref.channels == 1, "16 kHz mono erwartet")
print(vergleiche(dec.samples, ref.samples, rate: dec.rate))
