//! Spike F3: SpeakerKit im Prozess über die C-Hülle rt_diarize.
//!
//!   rt-diarize-spike --wav ton.wav --model-dir models/speakerkit
//!       [--num-speakers N] [--threshold 0.62] [--exclusive]
//!       [--repeat K] [--rttm-out aus.rttm] [--file-id ton]
//!
//! Gibt RTTM auf stdout (oder in --rttm-out) und Messwerte auf stderr.

use std::ffi::{c_char, c_int, CStr, CString};
use std::io::Write;
use std::sync::Mutex;
use std::time::Instant;

type ProgressCb = extern "C" fn(c_int);

extern "C" {
    fn rt_diarize(
        samples: *const f32,
        count: usize,
        num_speakers: i32,
        cluster_distance_threshold: f32,
        exclusive: bool,
        model_dir: *const c_char,
        progress: Option<ProgressCb>,
    ) -> *mut c_char;
    fn rt_free(p: *mut c_char);
    #[allow(dead_code)]
    fn rt_unload(model_dir: *const c_char);
}

#[derive(serde::Deserialize, Debug)]
struct Segment {
    start: f32,
    end: f32,
    speaker: String,
}

#[derive(serde::Deserialize, Debug)]
struct ShimResult {
    segments: Vec<Segment>,
    speaker_count: usize,
    model_load_ms: f64,
    diarize_ms: f64,
}

#[derive(serde::Deserialize, Debug)]
struct ShimError {
    error: String,
}

static PROGRESS: Mutex<Vec<i32>> = Mutex::new(Vec::new());

extern "C" fn on_progress(p: c_int) {
    PROGRESS.lock().unwrap().push(p);
}

fn read_wav(path: &str) -> (Vec<f32>, u32) {
    let mut reader = hound::WavReader::open(path).expect("WAV öffnen");
    let spec = reader.spec();
    assert_eq!(spec.channels, 1, "WAV muss mono sein");
    let samples: Vec<f32> = match spec.sample_format {
        hound::SampleFormat::Float => reader.samples::<f32>().map(|s| s.unwrap()).collect(),
        hound::SampleFormat::Int => {
            let max = (1i64 << (spec.bits_per_sample - 1)) as f32;
            reader.samples::<i32>().map(|s| s.unwrap() as f32 / max).collect()
        }
    };
    (samples, spec.sample_rate)
}

fn arg(args: &[String], name: &str) -> Option<String> {
    args.iter().position(|a| a == name).and_then(|i| args.get(i + 1).cloned())
}

/// Gegenprobe F3: argmax-cli als Kindprozess starten (Sandbox-Vererbung).
fn spawn_cli(cli: &str, wav: &str, model_dir: &str, num_speakers: i32, threshold: f32, rttm_out: &str) {
    let mut cmd = std::process::Command::new(cli);
    cmd.args(["diarize", "--audio-path", wav, "--model-path", model_dir, "--rttm-path", rttm_out,
              "--cluster-distance-threshold", &threshold.to_string(), "--use-exclusive-reconciliation"]);
    if num_speakers > 0 { cmd.args(["--num-speakers", &num_speakers.to_string()]); }
    let t0 = Instant::now();
    let out = cmd.output().expect("Kind starten");
    eprintln!("kind: status={} wall={:.0}ms stderr={}", out.status, t0.elapsed().as_secs_f64() * 1000.0,
              String::from_utf8_lossy(&out.stderr).trim());
    std::process::exit(if out.status.success() { 0 } else { 3 });
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if let Some(cli) = arg(&args, "--cli") {
        spawn_cli(&cli, &arg(&args, "--wav").unwrap(), &arg(&args, "--model-dir").unwrap(),
                  arg(&args, "--num-speakers").map(|s| s.parse().unwrap()).unwrap_or(0),
                  arg(&args, "--threshold").map(|s| s.parse().unwrap()).unwrap_or(0.6),
                  &arg(&args, "--rttm-out").unwrap());
    }
    let wav = arg(&args, "--wav").expect("--wav fehlt");
    let model_dir = arg(&args, "--model-dir").expect("--model-dir fehlt");
    let num_speakers: i32 = arg(&args, "--num-speakers").map(|s| s.parse().unwrap()).unwrap_or(0);
    let threshold: f32 = arg(&args, "--threshold").map(|s| s.parse().unwrap()).unwrap_or(0.6);
    let exclusive = args.iter().any(|a| a == "--exclusive");
    let repeat: usize = arg(&args, "--repeat").map(|s| s.parse().unwrap()).unwrap_or(1);
    let rttm_out = arg(&args, "--rttm-out");
    let file_id = arg(&args, "--file-id").unwrap_or_else(|| "ton".into());

    let (samples, rate) = read_wav(&wav);
    assert_eq!(rate, 16000, "WAV muss 16 kHz haben");
    eprintln!("samples={} ({:.1} s)", samples.len(), samples.len() as f64 / 16000.0);

    let c_dir = CString::new(model_dir).unwrap();
    let mut last: Option<ShimResult> = None;
    for i in 0..repeat {
        PROGRESS.lock().unwrap().clear();
        let t0 = Instant::now();
        let ptr = unsafe {
            rt_diarize(samples.as_ptr(), samples.len(), num_speakers, threshold,
                       exclusive, c_dir.as_ptr(), Some(on_progress))
        };
        let wall = t0.elapsed();
        assert!(!ptr.is_null(), "rt_diarize gab NULL zurück");
        let json = unsafe { CStr::from_ptr(ptr) }.to_string_lossy().into_owned();
        unsafe { rt_free(ptr) };
        if let Ok(e) = serde_json::from_str::<ShimError>(&json) {
            eprintln!("FEHLER: {}", e.error);
            std::process::exit(2);
        }
        let r: ShimResult = serde_json::from_str(&json).expect("JSON parsen");
        let prog = PROGRESS.lock().unwrap().clone();
        let monoton = prog.windows(2).all(|w| w[0] <= w[1]);
        eprintln!(
            "lauf={} wall={:.0}ms model_load={:.0}ms diarize={:.0}ms segmente={} sprecher={} \
             progress: n={} erst={:?} letzt={:?} monoton={}",
            i + 1, wall.as_secs_f64() * 1000.0, r.model_load_ms, r.diarize_ms,
            r.segments.len(), r.speaker_count, prog.len(), prog.first(), prog.last(), monoton
        );
        if i == 0 {
            eprintln!("progress-folge: {:?}", prog);
        }
        last = Some(r);
    }
    let r = last.unwrap();
    let mut out = String::new();
    for s in &r.segments {
        out.push_str(&format!(
            "SPEAKER {} 1 {:.3} {:.3} <NA> <NA> {} <NA> <NA>\n",
            file_id, s.start, s.end - s.start, s.speaker
        ));
    }
    match rttm_out {
        Some(p) => std::fs::write(p, out).unwrap(),
        None => std::io::stdout().write_all(out.as_bytes()).unwrap(),
    }
}
