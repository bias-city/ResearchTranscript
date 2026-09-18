// Wellenform unter dem Transport (User 2026-09-17): zoombar (⌘/Ctrl +
// Rad oder Pinch), verschiebbar (horizontales Rad, Shift + Rad), Klick
// und Ziehen setzen die Abspielposition, Doppelklick zeigt wieder alles.
// Hintergrund in den Sprecherfarben je Turn, Playhead als Strich.
//
// Kein Audio im Browser dekodiert: die Peaks kommen als Pyramide aus dem
// Backend (wellenform.py, Muster PrepareMedia) — je Ansicht ein Bucket
// pro Gerätepixel, gebündelt nachgeladen, wenn sich die Ansicht ändert.
import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet, sprecherFarbe, type Segment, type Sprecher } from "../lib/api";

const HOEHE = 44;              // wie die Transportleiste (User 2026-09-17)
// Oberes Drittel: Spur für Memo-Marker; die Welle nimmt die unteren zwei
// Drittel (User 2026-09-18)
const SPUR = Math.round(HOEHE / 3);
const WELLE = HOEHE - SPUR;
const MARKER_R = 4;
const MIN_SICHT_S = 2;          // engster Zoom: 2 s über die Breite

type Peaks = { t0: number; t1: number; daten: number[] };

/** Radix-Farbtoken (z. B. «indigo») → CSS-Farbe, einmal je Name UND
    Modus: die Dunkelpalette hat andere Werte (User 2026-09-17: die
    Welle blieb nach dem Umschalten hell). */
const farbCache = new Map<string, string>();
function cssFarbe(name: string, stufe: number | string): string {
  const dunkel = document.documentElement.classList.contains("dark") ? "d" : "l";
  const k = `${dunkel}-${name}-${stufe}`;
  const c = farbCache.get(k);
  if (c) return c;
  const v = getComputedStyle(document.documentElement)
    .getPropertyValue(`--${name}-${stufe}`).trim();
  const aus = v || (String(stufe).includes("1") ? "#6e6e6e" : "rgba(128,128,128,0.2)");
  farbCache.set(k, aus);
  return aus;
}

export default function Wellenform({ eid, segmente, sprecher, zeit, spielt,
                                     onSeek, onMemo }: {
  eid: string; segmente: Segment[]; sprecher: Sprecher[];
  /** Playhead in Sekunden (sekundengenau vom Player) */
  zeit: number; spielt: boolean;
  onSeek: (t: number) => void;
  /** Klick auf einen Memo-Marker: Memo dieser Zeile öffnen */
  onMemo?: (segId: string) => void;
}) {
  // Memo unter dem Zeiger (Tooltip) — x in CSS-Pixeln
  const [schwebt, setSchwebt] = useState<{ x: number; text: string } | null>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const [dauer, setDauer] = useState(0);
  const [breite, setBreite] = useState(0);
  // Ansicht: Anfang in s und Sekunden je CSS-Pixel
  const sicht = useRef({ t0: 0, spp: 0 });
  const peaks = useRef<Peaks | null>(null);
  const [, neuZeichnen] = useState(0);
  const tick = useCallback(() => neuZeichnen((n) => n + 1), []);
  const ladeTimer = useRef<number | undefined>(undefined);
  const zieht = useRef(false);
  // Feine Abspielposition (Hundertstel) aus dem Ereignis «rt-zeit» —
  // die Eigenschaft `zeit` kommt nur sekundenweise
  const fein = useRef(zeit);
  useEffect(() => {
    const h = (e: Event) => { fein.current = (e as CustomEvent<number>).detail; tick(); };
    window.addEventListener("rt-zeit", h);
    return () => window.removeEventListener("rt-zeit", h);
  }, [tick]);

  // Breite beobachten (responsiv) und Hell/Dunkel (html.dark → neu zeichnen)
  useEffect(() => {
    const el = canvas.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setBreite(el.clientWidth));
    ro.observe(el);
    setBreite(el.clientWidth);
    const mo = new MutationObserver(() => tick());
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => { ro.disconnect(); mo.disconnect(); };
  }, [tick]);

  const klemme = useCallback(() => {
    const s = sicht.current;
    if (!dauer || !breite) return;
    const maxSpp = dauer / breite;
    s.spp = Math.min(maxSpp, Math.max(MIN_SICHT_S / breite, s.spp || maxSpp));
    s.t0 = Math.max(0, Math.min(dauer - s.spp * breite, s.t0));
  }, [dauer, breite]);

  const ladePeaks = useCallback(() => {
    window.clearTimeout(ladeTimer.current);
    ladeTimer.current = window.setTimeout(() => {
      const s = sicht.current;
      if (!breite) return;
      const t0 = s.t0, t1 = s.t0 + s.spp * breite;
      const buckets = Math.min(4000, Math.ceil(breite * (window.devicePixelRatio || 1)));
      const q = `t0=${t0.toFixed(3)}&t1=${t1.toFixed(3)}&buckets=${buckets}`;
      void apiGet<{ dauer_s: number; peaks: number[] }>(
        `/api/transcripts/${eid}/wellenform?${q}`).then((r) => {
          if (!dauer && r.dauer_s) setDauer(r.dauer_s);
          peaks.current = { t0, t1, daten: r.peaks };
          tick();
        }).catch(() => undefined);
    }, 60);
  }, [eid, breite, dauer, tick]);

  // Erster Abruf: Dauer und Gesamtansicht
  useEffect(() => {
    if (!breite) return;
    if (!dauer) {
      void apiGet<{ dauer_s: number; peaks: number[] }>(
        `/api/transcripts/${eid}/wellenform?t0=0&t1=0&buckets=1`)
        .then((r) => setDauer(r.dauer_s)).catch(() => undefined);
      return;
    }
    if (!sicht.current.spp) { sicht.current = { t0: 0, spp: dauer / breite }; }
    klemme(); ladePeaks();
  }, [eid, breite, dauer, klemme, ladePeaks]);

  // Beim Abspielen der Position folgen: verlässt der Playhead die
  // Ansicht, rückt sie nach (Playhead bei 20 %)
  useEffect(() => {
    const s = sicht.current;
    if (!spielt || !breite || !s.spp) return;
    const t1 = s.t0 + s.spp * breite;
    if (zeit < s.t0 || zeit > t1 - s.spp * 4) {
      s.t0 = zeit - s.spp * breite * 0.2; klemme(); ladePeaks();
    }
    tick();
  }, [zeit, spielt, breite, klemme, ladePeaks, tick]);

  // Zeichnen
  useEffect(() => {
    const el = canvas.current;
    if (!el || !breite) return;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(breite * dpr), h = Math.round(HOEHE * dpr);
    if (el.width !== w || el.height !== h) { el.width = w; el.height = h; }
    const ctx = el.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, breite, HOEHE);
    const s = sicht.current;
    if (!s.spp) return;
    const x = (t: number) => (t - s.t0) / s.spp;
    const t1 = s.t0 + s.spp * breite;
    // Sprecherstreifen: kräftige Farbe, volle Höhe, durchgehend — keine
    // Rundungen, keine Lücken (User 2026-09-17); die Welle weiss darüber,
    // ausserhalb der Turns grau. Je Pixel merken, ob ein Turn darunter liegt.
    // je Pixel die Sprecherfarbe des Turns darunter (für die Welle)
    const belegt: (string | null)[] = new Array(breite).fill(null);
    for (let k = 0; k < segmente.length; k += 1) {
      const seg = segmente[k];
      // Lücke bis zum nächsten Turn mit dem Vorgänger auffüllen (User
      // 2026-09-17); Zwischenrufe liegen als spätere Einträge darüber
      const bis = Math.max(seg.end, segmente[k + 1]?.start ?? seg.end);
      if (bis < s.t0 || seg.start > t1) continue;
      const farbe = sprecherFarbe(sprecher, seg.sprecher);
      const a = Math.max(0, x(seg.start)), b = Math.min(breite, x(bis));
      if (b <= a) continue;
      // Farbschema der Sprecher-Badges (Radix «soft»): Hintergrund
      // Stufe a3, Welle in der Schriftfarbe a11 (User 2026-09-17)
      ctx.fillStyle = cssFarbe(farbe, "a3");
      ctx.fillRect(Math.floor(a), SPUR, Math.max(1, Math.ceil(b) - Math.floor(a)), WELLE);
      belegt.fill(farbe, Math.floor(a), Math.ceil(b));
    }
    // Welle (drawWave-Muster aus PrepareMedia: ein Balken je Pixel)
    const pk = peaks.current;
    if (pk && pk.daten.length && pk.t1 > pk.t0) {
      const mid = SPUR + WELLE / 2, n = pk.daten.length;
      const frei = cssFarbe("gray", "a9");
      for (let px = 0; px < breite; px += 1) {
        const t = s.t0 + (px + 0.5) * s.spp;
        const i = Math.floor(((t - pk.t0) / (pk.t1 - pk.t0)) * n);
        if (i < 0 || i >= n) continue;
        const amp = (pk.daten[i] / 255) * (WELLE / 2 - 2);
        if (amp <= 0.3) continue;
        const f = belegt[px];
        ctx.fillStyle = f ? cssFarbe(f, "a11") : frei;
        ctx.fillRect(px, mid - amp, 1, amp * 2);
      }
    }
    // Memo-Marker in der oberen Spur: roter Punkt am Anfang der Zeile
    ctx.fillStyle = cssFarbe("gray", "a4");
    ctx.fillRect(0, SPUR - 0.5, breite, 0.5);
    ctx.fillStyle = cssFarbe("red", 9);
    for (const seg of segmente) {
      if (!seg.memo || seg.start < s.t0 || seg.start > t1) continue;
      ctx.beginPath();
      ctx.arc(Math.max(MARKER_R, Math.min(breite - MARKER_R, x(seg.start))), SPUR / 2, MARKER_R, 0, Math.PI * 2);
      ctx.fill();
    }
    // Playhead
    const px = x(Math.abs(fein.current - zeit) < 1.05 ? fein.current : zeit);
    if (px >= 0 && px <= breite) {
      ctx.fillStyle = cssFarbe("gray", 12);
      ctx.fillRect(Math.round(px) - 1, 0, 2, HOEHE);
    }
  });

  // Zoom (⌘/Ctrl + Rad, Pinch) und Verschieben (horizontales Rad, Shift + Rad)
  useEffect(() => {
    const el = canvas.current;
    if (!el) return;
    const rad = (e: WheelEvent) => {
      const s = sicht.current;
      if (!s.spp || !dauer) return;
      const px = e.clientX - el.getBoundingClientRect().left;
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const t = s.t0 + px * s.spp;
        s.spp *= Math.exp(e.deltaY * 0.01);
        klemme();
        s.t0 = t - px * s.spp;
        klemme(); ladePeaks(); tick();
      } else if (Math.abs(e.deltaX) > Math.abs(e.deltaY) || e.shiftKey) {
        e.preventDefault();
        s.t0 += (e.shiftKey && !e.deltaX ? e.deltaY : e.deltaX) * s.spp;
        klemme(); ladePeaks(); tick();
      }
    };
    el.addEventListener("wheel", rad, { passive: false });
    return () => el.removeEventListener("wheel", rad);
  }, [dauer, klemme, ladePeaks, tick]);

  /** Memo-Marker unter dem Zeiger (nur in der oberen Spur) */
  const markerBei = (clientX: number, clientY: number) => {
    const el = canvas.current;
    const s = sicht.current;
    if (!el || !s.spp) return null;
    const r = el.getBoundingClientRect();
    const px = clientX - r.left, py = clientY - r.top;
    if (py > SPUR + 2) return null;
    let best: { seg: Segment; x: number; d: number } | null = null;
    for (const seg of segmente) {
      if (!seg.memo) continue;
      const mx = (seg.start - s.t0) / s.spp;
      const d = Math.abs(mx - px);
      if (d <= MARKER_R + 3 && (!best || d < best.d)) best = { seg, x: mx, d };
    }
    return best;
  };

  const zeitBei = (clientX: number) => {
    const el = canvas.current;
    const s = sicht.current;
    if (!el || !s.spp) return null;
    const px = clientX - el.getBoundingClientRect().left;
    return Math.max(0, Math.min(dauer, s.t0 + px * s.spp));
  };

  return (
    <div style={{ position: "relative" }}>
    {schwebt && (
      <div style={{ position: "absolute", bottom: HOEHE + 4, zIndex: 50,
                    left: Math.max(8, Math.min(breite - 328, schwebt.x - 160)),
                    width: 320, maxHeight: 160, overflow: "hidden",
                    padding: "6px 10px", borderRadius: 8, fontSize: 12, lineHeight: 1.45,
                    whiteSpace: "pre-wrap", pointerEvents: "none",
                    background: "var(--gray-12)", color: "var(--gray-1)",
                    boxShadow: "var(--shadow-4)" }}>
        {schwebt.text}
      </div>
    )}
    <canvas ref={canvas}
            style={{ width: "100%", height: HOEHE, display: "block",
                     cursor: schwebt ? "pointer" : "crosshair",
                     borderTop: "1px solid var(--gray-a4)",
                     background: "var(--color-panel-solid)" }}
            onPointerLeave={() => setSchwebt(null)}
            onPointerDown={(e) => {
              const m = markerBei(e.clientX, e.clientY);
              if (m) {                       // Marker: hinspringen und Memo öffnen
                onSeek(m.seg.start);
                onMemo?.(m.seg.id);
                setSchwebt(null);
                return;
              }
              const t = zeitBei(e.clientX);
              if (t === null) return;
              zieht.current = true;
              e.currentTarget.setPointerCapture(e.pointerId);
              onSeek(t);
            }}
            onPointerMove={(e) => {
              if (!zieht.current) {
                const m = markerBei(e.clientX, e.clientY);
                setSchwebt((alt) => m
                  ? (alt && alt.text === m.seg.memo && Math.abs(alt.x - m.x) < 1 ? alt
                     : { x: m.x, text: m.seg.memo ?? "" })
                  : (alt ? null : alt));
                return;
              }
              const t = zeitBei(e.clientX);
              if (t !== null) onSeek(t);
            }}
            onPointerUp={() => { zieht.current = false; }}
            onDoubleClick={() => {
              if (!breite || !dauer) return;
              sicht.current = { t0: 0, spp: dauer / breite };
              ladePeaks(); tick();
            }} />
    </div>
  );
}
