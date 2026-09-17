#!/usr/bin/env python3
"""RTTM-Paritätsvergleich: Segmentzahl, Sprecherzahl und Anteil der
Sekunden (10-ms-Raster) mit gleicher Zuordnung nach bester
Label-Permutation. Aufruf: vergleich.py A.rttm B.rttm [dauer_s]"""
import itertools, sys

def lies(p):
    seg = []
    for z in open(p):
        f = z.split()
        if len(f) < 10 or f[0] != "SPEAKER":
            continue
        s, d = float(f[-7]), float(f[-6])
        seg.append((s, s + d, f[-3]))
    return seg

def raster(seg, n, dt):
    r = [None] * n
    for s, e, sp in seg:
        for i in range(int(round(s / dt)), min(n, int(round(e / dt)))):
            r[i] = sp
    return r

def main():
    a, b = lies(sys.argv[1]), lies(sys.argv[2])
    dauer = float(sys.argv[3]) if len(sys.argv) > 3 else max(e for _, e, _ in a + b)
    dt = 0.01
    n = int(dauer / dt)
    ra, rb = raster(a, n, dt), raster(b, n, dt)
    la, lb = sorted({s for _, _, s in a}), sorted({s for _, _, s in b})
    best, bestmap = -1, None
    gross, klein = (la, lb) if len(la) >= len(lb) else (lb, la)
    for perm in itertools.permutations(gross, len(klein)):
        m = dict(zip(klein, perm))
        if len(la) >= len(lb):
            gleich = sum(1 for x, y in zip(ra, rb) if (x or y) and x == (m.get(y) if y else None))
        else:
            gleich = sum(1 for x, y in zip(ra, rb) if (x or y) and (m.get(x) if x else None) == y)
        if gleich > best:
            best, bestmap = gleich, m
    sprache = sum(1 for x, y in zip(ra, rb) if x or y)
    stille = n - sprache
    identisch = [(round(s, 3), round(e, 3), sp) for s, e, sp in a] == \
                [(round(s, 3), round(e, 3), sp) for s, e, sp in b]
    print(f"A: {len(a)} Segmente, {len(la)} Sprecher {la}")
    print(f"B: {len(b)} Segmente, {len(lb)} Sprecher {lb}")
    print(f"Zuordnung: {bestmap}")
    print(f"gleiche Zuordnung: {(best+stille)*dt:.2f} s von {n*dt:.2f} s gesamt = {100*(best+stille)/n:.2f} %"
          f"  (nur Sekunden mit Sprache in A oder B: {best*dt:.2f} s von {sprache*dt:.2f} s = {100*best/max(1,sprache):.2f} %)")
    print(f"RTTM zeilenweise identisch (3 Dezimalen): {identisch}")

main()
