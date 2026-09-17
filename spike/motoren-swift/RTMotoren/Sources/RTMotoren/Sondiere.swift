//  Sondiere.swift — Ersatz für video.sondiere: Codec-Tags, Masse, Dauer,
//  Bitrate, playable aus den Track-Formatbeschreibungen (kein stderr-Regex).

import AVFoundation
import Foundation

/// Ton-FourCC → ffprobe-codec_name.
func audioCodecName(_ sub: FourCharCode) -> String {
    switch sub {
    case kAudioFormatMPEGLayer3: return "mp3"
    case kAudioFormatMPEGLayer2: return "mp2"
    case kAudioFormatMPEGLayer1: return "mp1"
    case kAudioFormatMPEG4AAC, kAudioFormatMPEG4AAC_HE, kAudioFormatMPEG4AAC_HE_V2, kAudioFormatMPEG4AAC_LD,
         kAudioFormatMPEG4AAC_ELD, kAudioFormatMPEG4AAC_ELD_SBR, kAudioFormatMPEG4AAC_ELD_V2, kAudioFormatMPEG4AAC_Spatial:
        return "aac"
    case kAudioFormatLinearPCM: return "pcm"
    case kAudioFormatAppleLossless: return "alac"
    case kAudioFormatFLAC: return "flac"
    case kAudioFormatOpus: return "opus"
    case kAudioFormatAC3, kAudioFormatEnhancedAC3: return "ac3"
    case kAudioFormatAMR: return "amr_nb"
    case kAudioFormatAMR_WB: return "amr_wb"
    case kAudioFormatULaw: return "pcm_mulaw"
    case kAudioFormatALaw: return "pcm_alaw"
    default:
        let f = fourcc(sub).trimmingCharacters(in: .whitespaces)
        return f == "vorb" ? "vorbis" : f
    }
}

func sondiere(_ pfad: String) -> [String: Any] {
    let asset = AVURLAsset(url: URL(fileURLWithPath: pfad))
    var out: [String: Any] = [
        "video_codec": NSNull(), "audio_codec": NSNull(), "breite": 0, "hoehe": 0,
        "dauer_s": CMTimeGetSeconds(asset.duration).isFinite ? CMTimeGetSeconds(asset.duration) : 0,
        "bitrate": 0, "playable": asset.isPlayable, "abtastrate": 0, "kanaele": 0,
    ]
    var bitrate = 0.0
    var videoGesehen = false, audioGesehen = false
    for t in asset.tracks {
        bitrate += Double(t.estimatedDataRate)
        for fd in t.formatDescriptions as! [CMFormatDescription] {
            let sub = CMFormatDescriptionGetMediaSubType(fd)
            if t.mediaType == .video, !videoGesehen {
                videoGesehen = true
                out["video_codec"] = fourcc(sub).trimmingCharacters(in: .whitespaces)
                let dim = CMVideoFormatDescriptionGetDimensions(fd)
                out["breite"] = Int(dim.width); out["hoehe"] = Int(dim.height)
            } else if t.mediaType == .audio, !audioGesehen {
                audioGesehen = true
                out["audio_codec"] = audioCodecName(sub)
                if let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(fd) {
                    out["abtastrate"] = Int(asbd.pointee.mSampleRate)
                    out["kanaele"] = Int(asbd.pointee.mChannelsPerFrame)
                }
            }
        }
    }
    out["bitrate"] = Int(bitrate.rounded())
    return out
}

@_cdecl("rt_sondiere")
public func rt_sondiere(_ pfad: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>? {
    guard let pfad else { return jsonString(["error": "pfad ist NULL"]) }
    let p = String(cString: pfad)
    guard FileManager.default.fileExists(atPath: p) else { return jsonString(["error": "Datei fehlt: \(p)"]) }
    return jsonString(sondiere(p))
}
