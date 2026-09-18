"""Wie stark hat der Mensch eingegriffen? — Rechenkern (BACKLOG 16).

Verglichen wird der AUSGANGSSTAND eines Transkripts (`ausgang.json`, von
`bibliothek.anlegen` einmal geschrieben: das Whisper-Ergebnis bzw. die
importierte Datei, wie sie kam) mit dem heutigen Stand.

Text: Wort-Editierabstand. Ersetzungen (S), Löschungen (D) und
Einfügungen (I) des Menschen auf dem Weg vom Ausgangsstand zur heutigen
Fassung — in zwei Lesarten:
  - `roh`:       Wörter wie geschrieben (Gross/Klein und Satzzeichen zählen)
  - `normiert`:  klein geschrieben, ohne Satz- und Sonderzeichen — die
                 Lesart, in der Wortfehlerraten (WER) üblich berichtet werden
Die Rate bezieht sich auf die Wortzahl der KORRIGIERTEN Fassung (Referenz,
wie bei der WER) und zusätzlich auf die des Ausgangsstands.

Exakte Levenshtein-Zählung über zehntausende Wörter wäre in reinem Python
quadratisch — und unnötig: die Segmente tragen IDs. Eine Diff-Karte über
die IDs (`_strecken_paare`) sagt, WO etwas geschah; exakt gerechnet wird
nur dort. Über die Segmentgrenzen der Anker hinweg wird nicht ausgerichtet
(ein Wort, das von einem Segment ins nächste wanderte, zählt als gelöscht
und eingefügt).

Sprecher: Zeitgewichtet. Für jedes Stück Redezeit, das beide Stände
belegen, wird verglichen, welchem Sprecher die Maschine es gab und wem es
heute gehört. Maschinen-Sprecher werden dafür den heutigen zugeordnet
  - `mehrheit`: jeder Maschinen-Sprecher → der heutige mit der meisten
                gemeinsamen Zeit (mehrere dürfen auf denselben zeigen: ein
                Zusammenführen zweier Stimmen zählt NICHT als Fehler je Stelle)
  - `eins_zu_eins`: beste umkehrbar eindeutige Zuordnung — so rechnet die
                Diarization Error Rate ihren Verwechslungsanteil
Der Anteil der Zeit, die danach nicht passt, ist der Wert.
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from itertools import permutations

#: Lücken bis zu dieser Zellenzahl werden exakt gerechnet, grössere geschätzt
_DP_MAX = 1_000_000


def _normiere(wort: str) -> str:
    w = unicodedata.normalize("NFKC", wort).casefold()
    return "".join(z for z in w if unicodedata.category(z)[0] not in "PS")


def woerter(segmente: list[dict], normiert: bool) -> list[str]:
    aus: list[str] = []
    for s in sorted(segmente, key=lambda s: (s.get("start", 0), s.get("end", 0))):
        for w in re.split(r"\s+", s.get("text") or ""):
            if not w:
                continue
            if normiert:
                w = _normiere(w)
                if not w:
                    continue
            aus.append(w)
    return aus


def _levenshtein_sdi(a: list[str], b: list[str]) -> tuple[int, int, int]:
    """(S, D, I) einer minimalen Ausrichtung a → b; D = aus a gelöscht,
    I = in b eingefügt."""
    n, m = len(a), len(b)
    if n == 0:
        return 0, 0, m
    if m == 0:
        return 0, n, 0
    if n * m > _DP_MAX:                    # Notbremse: obere Schranke
        s = min(n, m)
        return s, n - s, m - s
    # Zeilenweise Kosten, dazu je Zelle die (S, D, I) des besten Wegs
    vor = [(j, 0, 0, j) for j in range(m + 1)]            # (kosten, S, D, I)
    for i in range(1, n + 1):
        akt = [(i, 0, i, 0)]
        ai = a[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                akt.append(vor[j - 1])
                continue
            k_s, k_d, k_i = vor[j - 1], vor[j], akt[j - 1]
            if k_s[0] <= k_d[0] and k_s[0] <= k_i[0]:
                akt.append((k_s[0] + 1, k_s[1] + 1, k_s[2], k_s[3]))
            elif k_d[0] <= k_i[0]:
                akt.append((k_d[0] + 1, k_d[1], k_d[2] + 1, k_d[3]))
            else:
                akt.append((k_i[0] + 1, k_i[1], k_i[2], k_i[3] + 1))
        vor = akt
    _, s, d, i = vor[m]
    return s, d, i


def _sdi(a: list[str], b: list[str]) -> tuple[int, int, int]:
    """Kleine Strecken exakt; sehr grosse (ein ganzes Transkript ersetzt)
    über difflib-Anker mit Standard-Heuristik, exakt nur in den Lücken."""
    if len(a) * len(b) <= _DP_MAX:
        return _levenshtein_sdi(a, b)
    s = d = i = 0
    for art, a0, a1, b0, b1 in SequenceMatcher(None, a, b).get_opcodes():
        if art != "equal":
            ds, dd, di = _levenshtein_sdi(a[a0:a1], b[b0:b1])
            s, d, i = s + ds, d + dd, i + di
    return s, d, i


def _woerter_text(text: str, normiert: bool) -> list[str]:
    return woerter([{"text": text}], normiert)


def _strecken_paare(ausgang: list[dict], heute: list[dict]):
    """Diff-Karte über die Segment-IDs (User 2026-09-18): Segmente, die in
    beiden Ständen vorkommen, sind Anker und werden direkt verglichen; was
    dazwischen liegt (geteilt, verbunden, eingefügt, gelöscht — der Editor
    vergibt dabei neue IDs), bildet je Lücke EIN Paar. So wird nur dort
    gerechnet, wo etwas geschah. Liefert (Text Ausgang, Text heute)."""
    nach_zeit = lambda s: (s.get("start", 0), s.get("end", 0))
    a = sorted(ausgang, key=nach_zeit)
    b = sorted(heute, key=nach_zeit)
    ort = {s["id"]: k for k, s in enumerate(a) if "id" in s}
    ia = 0
    luecke: list[dict] = []
    for s in b:
        k = ort.get(s.get("id"))
        if k is None or k < ia:            # neu — oder ein Anker, der die Reihenfolge bricht
            luecke.append(s)
            continue
        yield (" ".join(x.get("text") or "" for x in a[ia:k]),
               " ".join(x.get("text") or "" for x in luecke))
        luecke = []
        if (a[k].get("text") or "") != (s.get("text") or ""):
            yield a[k].get("text") or "", s.get("text") or ""
        ia = k + 1
    yield (" ".join(x.get("text") or "" for x in a[ia:]),
           " ".join(x.get("text") or "" for x in luecke))


def text(ausgang: list[dict], heute: list[dict]) -> dict:
    aus = {}
    for name, normiert in (("roh", False), ("normiert", True)):
        s = d = i = 0
        for ta, tb in _strecken_paare(ausgang, heute):
            if ta == tb:
                continue
            ds, dd, di = _sdi(_woerter_text(ta, normiert), _woerter_text(tb, normiert))
            s, d, i = s + ds, d + dd, i + di
        na, nb = len(woerter(ausgang, normiert)), len(woerter(heute, normiert))
        summe = s + d + i
        aus[name] = {"ersetzt": s, "geloescht": d, "eingefuegt": i, "geaendert": summe,
                     "woerter_ausgang": na, "woerter_heute": nb,
                     # Referenz = korrigierte Fassung (Konvention der WER)
                     "rate": summe / nb if nb else None,
                     "rate_ausgang": summe / na if na else None}
    return aus


def wortabstand(a: list[str], b: list[str]) -> dict:
    """Zwei Wortfolgen direkt (ohne Segment-IDs)."""
    s, d, i = _sdi(a, b)
    summe = s + d + i
    return {"ersetzt": s, "geloescht": d, "eingefuegt": i, "geaendert": summe,
            "woerter_ausgang": len(a), "woerter_heute": len(b),
            "rate": summe / len(b) if b else None,
            "rate_ausgang": summe / len(a) if a else None}


# ---------- Sprecher ----------

def _strecken(segmente: list[dict]) -> list[tuple[float, float, str]]:
    aus = []
    for s in segmente:
        if not (s.get("text") or "").strip():
            continue
        t0, t1 = float(s.get("start") or 0), float(s.get("end") or 0)
        if t1 > t0:
            aus.append((t0, t1, s.get("sprecher") or ""))
    return sorted(aus)


def _gemeinsame_zeit(a: list[tuple[float, float, str]],
                     b: list[tuple[float, float, str]]) -> dict[tuple[str, str], float]:
    """Zeit je Paar (Sprecher im Ausgang, Sprecher heute) — Zwei-Zeiger-Lauf.
    Überlappende Segmente desselben Stands zählen je für sich."""
    zeit: dict[tuple[str, str], float] = {}
    j0 = 0
    for a0, a1, wa in a:
        while j0 < len(b) and b[j0][1] <= a0:
            j0 += 1
        j = j0
        while j < len(b) and b[j][0] < a1:
            gemeinsam = min(a1, b[j][1]) - max(a0, b[j][0])
            if gemeinsam > 0:
                zeit[(wa, b[j][2])] = zeit.get((wa, b[j][2]), 0.0) + gemeinsam
            j += 1
    return zeit


def _beste_eins_zu_eins(zeit: dict[tuple[str, str], float],
                        links: list[str], rechts: list[str]) -> float:
    """Grösste Zeit, die eine umkehrbar eindeutige Zuordnung trifft."""
    if not links or not rechts:
        return 0.0
    if len(links) > len(rechts):           # immer die kürzere Seite permutieren
        zeit = {(r, li): t for (li, r), t in zeit.items()}
        links, rechts = rechts, links
    if len(rechts) <= 8:
        return max(sum(zeit.get((li, r), 0.0) for li, r in zip(links, wahl, strict=False))
                   for wahl in permutations(rechts, len(links)))
    # viele Sprecher: gierig (Näherung, praktisch nur bei Grossgruppen)
    paare = sorted(zeit.items(), key=lambda kv: -kv[1])
    belegt_l: set[str] = set()
    belegt_r: set[str] = set()
    summe = 0.0
    for (li, r), t in paare:
        if li in belegt_l or r in belegt_r or li not in links or r not in rechts:
            continue
        belegt_l.add(li)
        belegt_r.add(r)
        summe += t
    return summe


def sprecher(ausgang: list[dict], heute: list[dict]) -> dict:
    a, b = _strecken(ausgang), _strecken(heute)
    ids_a = sorted({w for _, _, w in a if w})
    ids_b = sorted({w for _, _, w in b if w})
    if not ids_a:                           # Maschine hat keine Sprecher vergeben
        return {"verglichen_s": 0.0, "maschine_ohne_sprecher": True,
                "sprecher_ausgang": 0, "sprecher_heute": len(ids_b),
                "mehrheit": None, "eins_zu_eins": None}
    zeit = _gemeinsame_zeit(a, b)
    gesamt = sum(zeit.values())
    if gesamt <= 0:
        return {"verglichen_s": 0.0, "maschine_ohne_sprecher": False,
                "sprecher_ausgang": len(ids_a), "sprecher_heute": len(ids_b),
                "mehrheit": None, "eins_zu_eins": None}
    links = sorted({li for li, _ in zeit})
    rechts = sorted({r for _, r in zeit})
    treffer_mehrheit = sum(max((zeit.get((li, r), 0.0) for r in rechts), default=0.0)
                           for li in links)
    treffer_11 = _beste_eins_zu_eins(zeit, links, rechts)
    return {"verglichen_s": gesamt, "maschine_ohne_sprecher": False,
            "sprecher_ausgang": len(ids_a), "sprecher_heute": len(ids_b),
            "mehrheit": 1 - treffer_mehrheit / gesamt,
            "eins_zu_eins": 1 - treffer_11 / gesamt}


def vergleiche(ausgang: dict, heute: dict) -> dict:
    """Beide in kanonischer Form ({segmente, sprecher})."""
    seg_a, seg_b = ausgang.get("segmente", []), heute.get("segmente", [])
    namen_a = {p["id"]: p.get("name", "") for p in ausgang.get("sprecher", [])}
    benannt = sum(1 for p in heute.get("sprecher", [])
                  if p.get("name", "") != namen_a.get(p["id"], p.get("name", ""))
                  or p["id"] not in namen_a)
    return {"text": text(seg_a, seg_b), "sprecher": sprecher(seg_a, seg_b),
            "segmente_ausgang": len(seg_a), "segmente_heute": len(seg_b),
            "sprecher_benannt": benannt}
