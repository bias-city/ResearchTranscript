/* rtmotoren.h — C-Schnittstelle der statischen Bibliothek RTMotoren.
 *
 * Alle Strings UTF-8. Alle Rückgaben sind JSON-C-Strings, die der
 * Aufrufer mit rt_free freigibt; Fehler kommen als {"error":"…"}.
 * Jede Funktion BLOCKIERT den rufenden Thread (nie vom Main-Thread
 * einer GUI-App rufen); keine Funktion braucht den Main-Thread.
 * Die Callbacks abbruch/fortschritt werden bei rt_dekodiere_wav16k und
 * rt_nach_mp3 auf dem rufenden Thread gerufen; bei rt_diarize_wav kommt
 * fortschritt aus einem SpeakerKit-Thread, abbruch wird auf dem rufenden
 * Thread alle 100 ms gepollt.
 */
#ifndef RTMOTOREN_H
#define RTMOTOREN_H
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef bool (*rt_abbruch_cb)(void *ctx);                    /* true = abbrechen */
typedef void (*rt_fortschritt_cb)(double anteil, void *ctx);  /* 0..1, monoton */

/* {"video_codec":"avc1"|null,"audio_codec":"aac"|null,"breite":..,"hoehe":..,
 *  "dauer_s":..,"bitrate":..,"playable":true,"abtastrate":..,"kanaele":..}
 * Codec-Tags wie ffprobe (avc1/hvc1/hev1, aac/mp3/vorbis/opus/flac/pcm/alac…),
 * null wenn keine Spur. breite/hoehe 0 ohne Video. */
char *rt_sondiere(const char *pfad);

/* Schreibt 16 kHz mono s16le WAV (Ausschnitt [start_s, start_s+dauer_s),
 * wenn dauer_s > 0). {"samples":n,"dauer_s":..,"ms":..}. Abbruch wird
 * alle ~0,5 s Audio geprüft; bei Abbruch wird die Zieldatei gelöscht und
 * {"error":"abgebrochen"} geliefert. abbruch/fortschritt dürfen NULL sein. */
char *rt_dekodiere_wav16k(const char *pfad, const char *ziel_wav,
                          double start_s, double dauer_s,
                          rt_abbruch_cb abbruch, rt_fortschritt_cb fortschritt,
                          void *ctx);

/* Wie `ffmpeg -vn -c:a libmp3lame -q:a <vbr_q>`: Quelle in nativer Rate
 * und Kanalzahl (mono/stereo) kodieren. lame_dylib = Pfad zu
 * libmp3lame.dylib (NULL → "libmp3lame.dylib" über den dyld-Suchpfad).
 * {"bytes":..,"dauer_s":..,"ms":..} */
char *rt_nach_mp3(const char *pfad, const char *ziel_mp3, int vbr_q,
                  const char *lame_dylib,
                  rt_abbruch_cb abbruch, rt_fortschritt_cb fortschritt,
                  void *ctx);

/* Liest 16-kHz-mono-WAV (s16 oder f32) und ruft SpeakerKit.
 * num_speakers 0 = automatisch. {"segments":[{"start":..,"end":..,
 * "speaker":"A"},…],"speaker_count":n,"model_load_ms":..,"diarize_ms":..} */
char *rt_diarize_wav(const char *wav_pfad, int32_t num_speakers,
                     float cluster_distance_threshold, bool exclusive,
                     const char *model_dir,
                     rt_abbruch_cb abbruch, rt_fortschritt_cb fortschritt,
                     void *ctx);

/* Geladene SpeakerKit-Modelle eines Ordners aus dem Speicher werfen. */
void rt_unload_models(const char *model_dir);

/* Von den rt_*-Funktionen gelieferten String freigeben. */
void rt_free(char *p);

#ifdef __cplusplus
}
#endif
#endif
