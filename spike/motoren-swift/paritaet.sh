#!/bin/zsh
# Paritätsmessung RTMotoren gegen ffmpeg / argmax-cli (BEFUND.md).
# Aufruf aus dem Repo-Wurzelverzeichnis: spike/motoren-swift/paritaet.sh <out-ordner>
# Voraussetzungen: rt-motoren-probe gebaut, vergleich-wav gebaut, im out-Ordner
# liegen interview_stereo.m4a, long.mp3, feld5.mp3 (siehe BEFUND «Fixtures»).
set -u
R=$(cd "$(dirname "$0")/../.." && pwd)
O=${1:?out-Ordner}
P=$R/spike/motoren-swift/rt-motoren-probe/target/release/rt-motoren-probe
V=$R/spike/motoren-swift/vergleich-wav
FF=$R/frontend/src-tauri/resources/bin/ffmpeg
CLI=$R/frontend/src-tauri/resources/bin/argmax-cli
M=$R/frontend/src-tauri/resources/models/speakerkit
F=$R/spike/avfoundation/fixtures
VP=$R/spike/speakerkit-shim/vergleich.py
t() { python3 -c 'import time;print(time.time())'; }
dauer() { python3 -c "print(f'{$2-$1:.3f} s')"; }

echo "################ (a) wav16k gegen ffmpeg -ar 16000 -ac 1"
for f in $F/interview.mp3 $O/interview_stereo.m4a $F/video_h264.mp4 $F/video_hevc.mov $F/interview.ogg $F/interview_opus.ogg $F/interview_apple.flac $O/long.mp3; do
  n=$(basename $f | tr . _)
  t0=$(t); $FF -y -v error -i $f -vn -ar 16000 -ac 1 -c:a pcm_s16le $O/ref_$n.wav; t1=$(t)
  echo "== $n  ffmpeg: $(dauer $t0 $t1)"
  $P wav16k $f $O/rt_$n.wav
  [[ $n == long_mp3 ]] || $V $O/rt_$n.wav $O/ref_$n.wav
done

echo "################ (b) Ausschnitt gegen ffmpeg -ss -t (und gegen das eigene Volldekodat)"
clip() { # datei ref-voll rt-voll start dauer
  n=$(basename $1 | tr . _)_${4}_${5}
  $FF -y -v error -ss $4 -t $5 -i $1 -vn -ar 16000 -ac 1 -c:a pcm_s16le $O/refclip_$n.wav
  echo "== clip $n"
  $P wav16k $1 $O/rtclip_$n.wav $4 $5
  $V $O/rtclip_$n.wav $O/refclip_$n.wav | sed 's/^/   vs ffmpeg -ss -t: /'
  # Lage im Volldekodat (ffmpeg bzw. RTMotoren) per Kreuzkorrelation der ersten Sekunde; Slice-Identität mit dem eigenen Volldekodat
  python3 - $O/rtclip_$n.wav $2 $3 $4 <<'PYLAGE'
import sys, numpy as np, wave
def lese(p):
    w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
c, start = lese(sys.argv[1]), float(sys.argv[4])
for name, p in (("ffmpeg", sys.argv[2]), ("RTMotoren", sys.argv[3])):
    f = lese(p); i0 = int(round(start * 16000)); m = min(len(c), 16000); best, bestv = 0, -1
    for lag in range(-16000, 16001):
        a = f[i0 + lag: i0 + lag + m]
        if len(a) < m: continue
        v = np.dot(a, c[:m]) / (np.linalg.norm(a) * np.linalg.norm(c[:m]) + 1e-9)
        if v > bestv: bestv, best = v, lag
    s = f[i0+best:i0+best+len(c)]; d = c - s if len(s) == len(c) else c; e = np.sum(d**2); snr = 10*np.log10(np.sum(s**2)/e) if e > 0 and len(s) == len(c) else 999
    print(f"   Lage im {name}-Volldekodat: {start + best/16000:.4f} s (Abweichung {best/16000*1000:+.1f} ms, r={bestv:.4f}); SNR gegen dessen Slice {snr:.1f} dB, identisch={len(s)==len(c) and np.array_equal(s, c)}")
PYLAGE
}
clip $F/interview.mp3 $O/ref_interview_mp3.wav $O/rt_interview_mp3.wav 30 8          # Hörprobe aus dem Bibliotheks-mp3
clip $F/interview.mp3 $O/ref_interview_mp3.wav $O/rt_interview_mp3.wav 0 5
clip $F/interview.mp3 $O/ref_interview_mp3.wav $O/rt_interview_mp3.wav 120 10        # über das Ende hinaus
clip $O/feld5.mp3 $O/ref_feld5.wav $O/rt_feld5.wav 200 8                              # Bibliotheks-mp3 (stereo 48 k)
clip $O/long.mp3 $O/ref_long_mp3.wav $O/rt_long_mp3.wav 3000 8                        # 1 h VBR, Seek tief in der Datei
clip $O/long.mp3 $O/ref_long_mp3.wav $O/rt_long_mp3.wav 600 1
clip $O/interview_stereo.m4a $O/ref_interview_stereo_m4a.wav $O/rt_interview_stereo_m4a.wav 10 1
clip $O/interview_stereo.m4a $O/ref_interview_stereo_m4a.wav $O/rt_interview_stereo_m4a.wav 60 8
clip $F/video_hevc.mov $O/ref_video_hevc_mov.wav $O/rt_video_hevc_mov.wav 30 1
clip $F/video_h264.mp4 $O/ref_video_h264_mp4.wav $O/rt_video_h264_mp4.wav 20 8
clip $F/interview.ogg $O/ref_interview_ogg.wav $O/rt_interview_ogg.wav 30 1          # Ogg: von vorn
clip $F/interview_opus.ogg $O/ref_interview_opus_ogg.wav $O/rt_interview_opus_ogg.wav 60 2
clip $F/interview_apple.flac $O/ref_interview_apple_flac.wav $O/rt_interview_apple_flac.wav 30 1
clip $O/ref_interview_mp3.wav $O/ref_interview_mp3.wav $O/ref_interview_mp3.wav 12.345 3.21   # jobs._clip: Ausschnitt aus dem 16-kHz-WAV

echo "################ (c) mp3 gegen ffmpeg -c:a libmp3lame -q:a 2"
for f in $F/interview.mp3 $O/interview_stereo.m4a $F/video_hevc.mov $O/long.mp3; do
  n=$(basename $f | tr . _)
  t0=$(t); $FF -y -v error -i $f -vn -c:a libmp3lame -q:a 2 $O/ffm_$n.mp3; t1=$(t)
  echo "== $n  ffmpeg: $(dauer $t0 $t1)"
  $P mp3 $f $O/rt_$n.mp3
  for x in ffm rt; do
    echo "   $x: $(ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,duration,bit_rate -of compact=nk=1:p=0 $O/${x}_$n.mp3) bytes=$(stat -f %z $O/${x}_$n.mp3)"
  done
done

echo "################ (d) diarize_wav gegen argmax-cli diarize"
for w in feld5 demo; do
  for n in 0 2; do
    extra=(); [[ $n != 0 ]] && extra=(--num-speakers $n)
    t0=$(t); $CLI diarize --audio-path $O/ref_$w.wav --model-path $M --rttm-path $O/cli_${w}_$n.rttm --cluster-distance-threshold 0.62 --use-exclusive-reconciliation $extra >/dev/null 2>&1; t1=$(t)
    echo "== $w n=$n  argmax-cli: $(dauer $t0 $t1)"
    $P diarize $O/ref_$w.wav $M $n $O/rt_${w}_$n.rttm
    python3 $VP $O/cli_${w}_$n.rttm $O/rt_${w}_$n.rttm | tail -3
    echo "   diff (Bytes): $(diff <(cat $O/cli_${w}_$n.rttm; echo) $O/rt_${w}_$n.rttm | wc -l | tr -d ' ') Zeilen"
  done
done
echo "== feld5 aus dem RTMotoren-Dekodat (rt_feld5.wav) statt ffmpeg-WAV, n=0"
$P wav16k $O/feld5.mp3 $O/rt_feld5.wav >/dev/null; $V $O/rt_feld5.wav $O/ref_feld5.wav
$P diarize $O/rt_feld5.wav $M 0 $O/rt_feld5dec_0.rttm; python3 $VP $O/cli_feld5_0.rttm $O/rt_feld5dec_0.rttm | tail -2
echo "== warm: 3 Aufrufe im selben Prozess"; RT_WIEDERHOLE=3 $P diarize $O/ref_feld5.wav $M 0 $O/warm.rttm; cmp $O/warm.rttm $O/rt_feld5_0.rttm && echo "   warm identisch"
echo "== RTTM byte-identisch (File-ID angeglichen, CLI ohne Newline am Ende)"; for w in feld5_0 feld5_2 demo_0 demo_2; do id=ref_${w%_*}; cmp <(sed "s/^SPEAKER $id /SPEAKER ton /" $O/cli_$w.rttm; echo) $O/rt_$w.rttm && echo "   $w: identisch"; done

echo "################ (e) Abbruch"
rm -f $O/abbruch_long.wav $O/abbruch_long.mp3 $O/abbruch.rttm
echo "== wav16k long.mp3, Abbruch nach 2 s"; RT_ABBRUCH_NACH_S=2 $P wav16k $O/long.mp3 $O/abbruch_long.wav; ls -la $O/abbruch_long.wav 2>&1 | sed 's/^/   /'
echo "== mp3 long.mp3, Abbruch nach 1 s"; RT_ABBRUCH_NACH_S=1 $P mp3 $O/long.mp3 $O/abbruch_long.mp3; ls -la $O/abbruch_long.mp3 2>&1 | sed 's/^/   /'
echo "== diarize feld5, Abbruch nach 0.5 s"; RT_ABBRUCH_NACH_S=0.5 $P diarize $O/ref_feld5.wav $M 0 $O/abbruch.rttm; ls -la $O/abbruch.rttm 2>&1 | sed 's/^/   /'
echo "== diarize 1-h-WAV voll"; $P diarize $O/rt_long_mp3.wav $M 0 $O/long.rttm
echo "== diarize 1-h-WAV, Abbruch nach 3 s"; RT_ABBRUCH_NACH_S=3 $P diarize $O/rt_long_mp3.wav $M 0 $O/long_abbruch.rttm

echo "################ (4) Parallel: Thread 0 diarize feld5, Threads 1–3 wav16k long/mp3/mov"
$P parallel $O/ref_feld5.wav $M $O/long.mp3 $O/par_long.wav $F/interview.mp3 $O/par_mp3.wav $F/video_hevc.mov $O/par_mov.wav > $O/par.rttm
for x in long_mp3:par_long interview_mp3:par_mp3 video_hevc_mov:par_mov; do
  echo "   cmp rt_${x%%:*}.wav ${x##*:}.wav: $(cmp $O/rt_${x%%:*}.wav $O/${x##*:}.wav && echo identisch)"
done
echo "   RTTM parallel vs. sequenziell: $(cmp $O/par.rttm $O/rt_feld5_0.rttm && echo identisch)"
echo "== parallel-diarize k=3 (feld5)"
$P parallel-diarize $O/ref_feld5.wav $M 3 > $O/par3.rttm
echo "   RTTM k=3 vs. sequenziell: $(cmp $O/par3.rttm $O/rt_feld5_0.rttm && echo identisch)"
echo "== parallel-diarize k=4 (feld5)"
$P parallel-diarize $O/ref_feld5.wav $M 4 > /dev/null
echo "== vier wav16k gleichzeitig (long ×2, feld5, mov)"
$P parallel $O/ref_demo.wav $M $O/long.mp3 $O/par4_1.wav $O/long.mp3 $O/par4_2.wav $O/feld5.mp3 $O/par4_3.wav $F/video_hevc.mov $O/par4_4.wav > /dev/null
echo "   cmp: $(cmp $O/par4_1.wav $O/rt_long_mp3.wav && cmp $O/par4_2.wav $O/rt_long_mp3.wav && cmp $O/par4_3.wav $O/rt_feld5.wav && echo alle identisch)"
