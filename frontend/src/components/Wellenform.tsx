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
const MIN_SICHT_S = 2;          // engster Zoom: 2 s über die Breite

type Peaks = { t0: number; t1: number; daten: number[] };

/** Radix-Farbtoken (z. B. «indigo») → CSS-Farbe, einmal je Name. */
const farbCache = new Map<string, string>();
function cssFarbe(name: string, stufe: number): string {
  const k = `${name}-${stufe}`;
  const c = farbCache.get(k);
  if (c) return c;
  const v = getComputedStyle(document.documentElement)
    .getPropertyValue(`--${name}-${stufe}`).trim();
  const aus = v || (stufe >= 9 ? "#6e6e6e" : "rgba(128,128,128,0.2)");
  farbCache.set(k, aus);
  return aus;
}

export default function Wellenform({ eid, segmente, sprecher, zeit, spielt,
                                     onSeek }: {
  eid: string; segmente: Segment[]; sprecher: Sprecher[];
  /** Playhead in Sekunden (sekundengenau vom Player) */
  zeit: number; spielt: boolean;
  onSeek: (t: number) => void;
}) {
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

  // Breite beobachten (responsiv)
  useEffect(() => {
    const el = canvas.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setBreite(el.clientWidth));
    ro.observe(el);
    setBreite(el.clientWidth);
    return () => ro.disconnect();
  }, []);

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
    const belegt = new Uint8Array(breite);
    for (const seg of segmente) {
      if (seg.end < s.t0 || seg.start > t1) continue;
      const farbe = sprecherFarbe(sprecher, seg.sprecher);
      const a = Math.max(0, x(seg.start)), b = Math.min(breite, x(seg.end));
      if (b <= a) continue;
      // Pastell wie die Badges (Stufe 3–4), aber nicht ganz so blass:
      // Stufe 7 der Radix-Skala (User 2026-09-17)
      ctx.globalAlpha = farbe === "gray" ? 0.5 : 1;
      ctx.fillStyle = cssFarbe(farbe === "gray" ? "gray" : farbe, 7);
      ctx.fillRect(Math.floor(a), 0, Math.max(1, Math.ceil(b) - Math.floor(a)), HOEHE);
      belegt.fill(1, Math.floor(a), Math.ceil(b));
    }
    ctx.globalAlpha = 1;
    // Welle (drawWave-Muster aus PrepareMedia: ein Balken je Pixel)
    const pk = peaks.current;
    if (pk && pk.daten.length && pk.t1 > pk.t0) {
      const mid = HOEHE / 2, n = pk.daten.length;
      const frei = cssFarbe("gray", 9);
      for (let px = 0; px < breite; px += 1) {
        const t = s.t0 + (px + 0.5) * s.spp;
        const i = Math.floor(((t - pk.t0) / (pk.t1 - pk.t0)) * n);
        if (i < 0 || i >= n) continue;
        const amp = (pk.daten[i] / 255) * (HOEHE / 2 - 3);
        if (amp <= 0.3) continue;
        ctx.fillStyle = belegt[px] ? "rgba(255,255,255,0.85)" : frei;
        ctx.fillRect(px, mid - amp, 1, amp * 2);
      }
    }
    // Playhead
    const px = x(zeit);
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

  const zeitBei = (clientX: number) => {
    const el = canvas.current;
    const s = sicht.current;
    if (!el || !s.spp) return null;
    const px = clientX - el.getBoundingClientRect().left;
    return Math.max(0, Math.min(dauer, s.t0 + px * s.spp));
  };

  return (
    <canvas ref={canvas}
            style={{ width: "100%", height: HOEHE, display: "block",
                     cursor: "crosshair", borderTop: "1px solid var(--gray-a4)",
                     background: "var(--color-panel-solid)" }}
            onPointerDown={(e) => {
              const t = zeitBei(e.clientX);
              if (t === null) return;
              zieht.current = true;
              e.currentTarget.setPointerCapture(e.pointerId);
              onSeek(t);
            }}
            onPointerMove={(e) => {
              if (!zieht.current) return;
              const t = zeitBei(e.clientX);
              if (t !== null) onSeek(t);
            }}
            onPointerUp={() => { zieht.current = false; }}
            onDoubleClick={() => {
              if (!breite || !dauer) return;
              sicht.current = { t0: 0, spp: dauer / breite };
              ladePeaks(); tick();
            }} />
  );
}
