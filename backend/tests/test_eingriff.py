"""Eingriffsmass: Wortabstand und Sprecher-Verwechslung (BACKLOG 16)."""
import json
import time

from researchtranscript import bibliothek, eingriff


def seg(start, end, wer, text, sid=None):
    return {"id": sid or f"s{start}", "start": start, "end": end, "sprecher": wer, "text": text}


def test_wortabstand_ist_minimal():
    a = ["das", "ist", "ein", "kleiner", "test", "mit", "worten"]
    b = ["das", "ist", "ein", "grosser", "test", "worten", "heute"]
    r = eingriff.wortabstand(a, b)
    # minimal sind 3 Schritte — ob als 1S+1D+1I oder 3S, ist gleichwertig
    assert r["geaendert"] == 3 and r["woerter_heute"] == 7
    assert abs(r["rate"] - 3 / 7) < 1e-9


def test_wortabstand_trennt_s_d_i():
    r = eingriff.wortabstand(["a", "b", "c", "d"], ["a", "x", "c"])
    assert (r["ersetzt"], r["geloescht"], r["eingefuegt"]) == (1, 1, 0)
    r = eingriff.wortabstand(["a", "c"], ["a", "b", "c"])
    assert (r["ersetzt"], r["geloescht"], r["eingefuegt"]) == (0, 0, 1)


def test_normiert_ueberliest_satzzeichen_und_grossschreibung():
    a = [seg(0, 2, "A", "hallo welt wie gehts")]
    b = [seg(0, 2, "A", "Hallo, Welt! Wie geht’s?")]
    r = eingriff.text(a, b)
    assert r["normiert"]["geaendert"] == 0
    assert r["roh"]["geaendert"] == 4


def test_unveraendert_ist_null_und_leer_ist_none():
    a = [seg(0, 2, "A", "eins zwei drei")]
    assert eingriff.text(a, a)["roh"]["rate"] == 0
    assert eingriff.text([], [])["roh"]["rate"] is None


def test_grosses_transkript_bleibt_schnell():
    import random
    rng = random.Random(7)
    basis = [seg(k * 3, k * 3 + 3, "S1", " ".join(f"w{int(rng.paretovariate(1.1)) % 4000}"
                                                   for _ in range(10)), f"id{k}")
             for k in range(3000)]                                    # 30 000 Wörter
    heute = [dict(s) for s in basis]
    for k in range(0, 3000, 5):                                       # 600 Segmente, je 1 Wort
        w = heute[k]["text"].split()
        w[3] = "KORRIGIERT"
        heute[k]["text"] = " ".join(w)
    t0 = time.monotonic()
    r = eingriff.text(basis, heute)["roh"]
    assert time.monotonic() - t0 < 3
    assert (r["ersetzt"], r["geloescht"], r["eingefuegt"]) == (600, 0, 0)
    assert abs(r["rate"] - 600 / 30000) < 1e-9


def test_teilen_verbinden_und_zwischenruf_ueber_neue_ids():
    basis = [seg(0, 4, "A", "eins zwei drei vier", "a"), seg(4, 6, "B", "fuenf sechs", "b"),
             seg(6, 8, "A", "sieben", "c"), seg(8, 9, "A", "acht", "d")]
    heute = [seg(0, 2, "A", "eins zwei", "x1"), seg(2, 4, "B", "drei vier", "x2"),   # a geteilt
             seg(4, 6, "B", "fuenf sechs", "b"),
             seg(5, 5.5, "A", "mhm", "neu"),                                         # Zwischenruf
             seg(6, 9, "A", "sieben acht", "x3")]                                    # c+d verbunden
    r = eingriff.text(basis, heute)["roh"]
    assert (r["ersetzt"], r["geloescht"], r["eingefuegt"]) == (0, 0, 1)


def test_sprecher_umhaengen_zaehlt_zeitgewichtet():
    a = [seg(0, 10, "S1", "a"), seg(10, 20, "S2", "b"), seg(20, 30, "S1", "c"), seg(30, 40, "S2", "d")]
    b = [seg(0, 10, "S1", "a"), seg(10, 20, "S2", "b"), seg(20, 30, "S2", "c"), seg(30, 40, "S2", "d")]
    r = eingriff.sprecher(a, b)
    assert abs(r["mehrheit"] - 0.25) < 1e-9
    assert abs(r["eins_zu_eins"] - 0.25) < 1e-9


def test_zusammenfuehren_ist_kein_fehler_je_stelle_aber_in_der_eins_zu_eins_lesart():
    a = [seg(0, 10, "S1", "a"), seg(10, 20, "S2", "b"), seg(20, 30, "S3", "c")]
    b = [seg(0, 10, "A", "a"), seg(10, 20, "B", "b"), seg(20, 30, "A", "c")]   # S3 → A
    r = eingriff.sprecher(a, b)
    assert r["mehrheit"] == 0
    assert abs(r["eins_zu_eins"] - 1 / 3) < 1e-9
    assert (r["sprecher_ausgang"], r["sprecher_heute"]) == (3, 2)


def test_geteilte_segmente_und_ohne_maschinensprecher():
    a = [seg(0, 10, "S1", "eins zwei")]
    b = [seg(0, 4, "S1", "eins", "x"), seg(4, 10, "S2", "zwei", "y")]
    assert abs(eingriff.sprecher(a, b)["mehrheit"] - 0.4) < 1e-9
    ohne = eingriff.sprecher([seg(0, 10, None, "a")], [seg(0, 10, "A", "a")])
    assert ohne["maschine_ohne_sprecher"] and ohne["mehrheit"] is None


def test_ausgangsstand_wird_gesichert_und_bleibt(client):
    d = bibliothek.anlegen("Probe", [seg(0, 2, "p1", "hallo welt"), seg(2, 4, "p2", "ja")],
                           [{"id": "p1", "name": "Sprecher 1"}, {"id": "p2", "name": "Sprecher 2"}],
                           {"datei": "probe.mp3", "erzeugt": "transcription", "model": "large-v3-turbo"})
    eid = d["id"]
    basis, woher = bibliothek.ausgangsstand(eid)
    assert woher == "ausgang" and basis["segmente"][0]["text"] == "hallo welt"
    d["segmente"][0]["text"] = "Hallo Welt, genau"
    d["segmente"][1]["sprecher"] = "p1"
    bibliothek.schreibe(eid, d)
    basis2, _ = bibliothek.ausgangsstand(eid)
    assert basis2["segmente"][0]["text"] == "hallo welt"          # unberührt vom Editor
    r = eingriff.vergleiche(basis2, bibliothek.lese(eid))
    assert r["text"]["normiert"]["eingefuegt"] == 1 and r["sprecher"]["eins_zu_eins"] > 0


def test_alter_eintrag_ohne_ausgang_wird_beim_ersten_eingriff_nachgeholt(client):
    d = bibliothek.anlegen("Alt", [seg(0, 2, "p1", "roh text")], [{"id": "p1", "name": "Sprecher 1"}],
                           {"datei": "a.mp3", "erzeugt": "transcription"})
    eid = d["id"]
    (bibliothek.eintrag_pfad(eid) / bibliothek.AUSGANG).unlink()   # wie vor 0.6.0
    assert bibliothek.ausgangsstand(eid)[1] == "ausgang"           # noch unberührt: heutiger Stand
    d["segmente"][0]["text"] = "korrigierter text"
    bibliothek.schreibe(eid, d)
    basis, woher = bibliothek.ausgangsstand(eid)
    assert woher == "ausgang" and basis["segmente"][0]["text"] == "roh text"
    assert json.loads((bibliothek.eintrag_pfad(eid) / bibliothek.AUSGANG).read_text())["schema"] == 1
