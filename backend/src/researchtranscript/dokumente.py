"""Begleitdokumente für Forschende, aus den echten Werten erzeugt (BACKLOG 16).

Zuschnitt nach Recherche (docs/begleitdokumente.md):

  protokoll     je Transkript — Transkriptionsprotokoll (Provenienz,
                Objektebene der Datendokumentation)
  methoden      Auswahl von 1…n Transkripten — Methodenbaustein: ein
                Methodenteil beschreibt das KORPUS (n, Dauer, Mittel und
                Spanne), nicht das einzelne Interview
  verfahren     je Projekt — Baustein fürs Verzeichnis der
                Bearbeitungstätigkeiten / DSFA / Ethikantrag: nur die
                Fakten der App; alles, was nur die Stelle weiss, bleibt
                ein markiertes Feld
  repositorium  Auswahl — Datenblatt für die Ablage in einem
                DOI-Repositorium (Zenodo/DataCite, Facharchive), vorausgefüllt
                aus Zotero und Transkript, offen, wo die Forscherin entscheidet

Grundsätze: Die App behauptet nichts, was sie nicht weiss (Rechtsgrundlage,
Speicherort, Backups, wer korrigiert hat). Eingriffsmasse heissen
«Korrekturrate», nie «Fehlerrate» oder «Genauigkeit». Befragte aus Zotero
erscheinen nie als Urheber. Offene Felder sind `[ … ]`.

Texte viersprachig in `dokumente_texte/<sprache>.py` (de = Quelle); hier
steht nur, WAS in welcher Reihenfolge erscheint.
"""
from __future__ import annotations

import hashlib
import importlib
import statistics
from datetime import UTC, datetime
from pathlib import Path

from . import bibliothek, eingriff
from .ausgabe import format_hms
from .config import APP_VERSION, get_available_models

ARTEN = ("protokoll", "methoden", "verfahren", "repositorium")
SPRACHEN = ("de", "en", "fr", "it")

#: Mitgelieferte Bestandteile — dieselben Stände wie scripts/gen-licenses.py
WHISPER_CPP = "1.8.2"
SILERO = "v5.1.2"
SPEAKERKIT = "argmax-oss-swift ea872ff"

#: Zotero-Rollen der befragten Seite: nie als Urheber vorschlagen
BEFRAGTE = {"interviewee", "guest", "castMember", "author"}

NACHWEISE = [
    ("Radford, A., Kim, J. W., Xu, T., Brockman, G., McLeavey, C., & Sutskever, I. (2022). "
    "Robust Speech Recognition via Large-Scale Weak Supervision. arXiv:2212.04356. <https://arxiv.org/abs/2212.04356>"),
    f"whisper.cpp {WHISPER_CPP} (ggml-org, MIT). <https://github.com/ggml-org/whisper.cpp>",
    "OpenAI. whisper-large-v3-turbo (MIT). <https://huggingface.co/openai/whisper-large-v3-turbo>",
    ("Plaquet, A., & Bredin, H. (2023). Powerset multi-class cross entropy loss for neural speaker "
    "diarization. Proc. Interspeech 2023, 3222–3226. <https://doi.org/10.21437/Interspeech.2023-205>"),
    ("Bredin, H. (2023). pyannote.audio 2.1 speaker diarization pipeline: principle, benchmark, and "
    "recipe. Proc. Interspeech 2023, 1983–1987. <https://doi.org/10.21437/Interspeech.2023-105>"),
    ("pyannote. speaker-diarization-community-1 (CC BY 4.0). "
    "<https://huggingface.co/pyannote/speaker-diarization-community-1>"),
    (f"Argmax, Inc. Argmax OSS: WhisperKit, SpeakerKit ({SPEAKERKIT}, MIT). "
    "<https://github.com/argmaxinc/argmax-oss-swift>"),
    f"Silero Team. Silero VAD {SILERO} (MIT). <https://github.com/snakers4/silero-vad>",
    ("Snover, M., Dorr, B., Schwartz, R., Micciulla, L., & Makhoul, J. (2006). A Study of Translation "
    "Edit Rate with Targeted Human Annotation. Proc. AMTA 2006. <https://aclanthology.org/2006.amta-papers.25/>"),
    ("Wollin-Giering, S., Hoffmann, M., Höfting, J., & Ventzke, C. (2024). Automatic Transcription of "
    "English and German Qualitative Interviews. Forum Qualitative Sozialforschung 25(1). "
    "<https://doi.org/10.17169/fqs-25.1.4129>"),
    "American Psychological Association. JARS–Qual, Table 1. <https://apastyle.apa.org/jars/qual-table-1.pdf>",
]


def _texte(sprache: str) -> dict[str, str]:
    basis = dict(importlib.import_module(".dokumente_texte.de", __package__).T)
    if sprache in SPRACHEN and sprache != "de":
        basis.update(importlib.import_module(f".dokumente_texte.{sprache}", __package__).T)
    return basis


# ---------- Fakten eines Transkripts ----------

def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for stueck in iter(lambda: f.read(1 << 20), b""):
            h.update(stueck)
    return h.hexdigest()


def _dateien(eid: str, daten: dict) -> list[dict]:
    ordner = bibliothek.eintrag_pfad(eid)
    namen = ["transkript.json", bibliothek.AUSGANG, daten.get("audio"), daten.get("video")]
    aus = []
    for n in namen:
        p = ordner / n if n else None
        if p is not None and p.is_file():
            aus.append({"name": n, "bytes": p.stat().st_size, "sha256": _sha256(p)})
    return aus


def fakten(eid: str, *, mit_dateien: bool = True) -> dict:
    daten = bibliothek.lese(eid)
    seg = daten.get("segmente", [])
    q = daten.get("quelle", {}) or {}
    journal = daten.get("journal", [])
    maschine = next((r for r in journal if r.get("origin") == "machine"), None)
    hand = [r for r in journal if r.get("origin") == "human"
            and any(k != "zotero" for k in (r.get("changed") or {}))]
    arten: dict[str, int] = {}
    for r in hand:
        for art in (r.get("changed") or {}).values():
            arten[art] = arten.get(art, 0) + 1
    ausgang, woher = bibliothek.ausgangsstand(eid)
    mass = eingriff.vergleiche(ausgang, daten) if ausgang is not None else None
    hand_seg = sum(1 for s in seg if s.get("origin") == "human")
    return {
        "id": daten["id"], "name": daten.get("name", ""), "datei": q.get("datei"),
        "transkribiert": q.get("erzeugt") == "transcription",
        "dauer": max((s.get("end", 0) for s in seg), default=0.0),
        "sprache": q.get("language"), "modell": q.get("model"),
        "modell_quelle": q.get("modell_quelle") or _modell_quelle_heute(q.get("model")),
        "modell_quelle_aufgezeichnet": bool(q.get("modell_quelle")),
        "diarize": q.get("diarize"), "sprecherzahl": q.get("sprecherzahl"),
        "trennung": q.get("trennung"), "vad": q.get("vad"),
        "app": q.get("app") or ((maschine or {}).get("who", {}).get("app") or "").rpartition("/")[2] or None,
        "lauf_datum": (maschine or {}).get("finished") or daten.get("created"),
        "segmente": len(seg), "sprecher": len(daten.get("sprecher", [])),
        "memos": sum(1 for s in seg if s.get("memo")),
        "sitzungen": len(hand),
        "hand_von": min((r.get("started") for r in hand if r.get("started")), default=None),
        "hand_bis": max((r.get("finished") for r in hand if r.get("finished")), default=None),
        "aenderungen": arten, "hand_segmente": hand_seg,
        "ausgang": woher, "mass": mass, "zotero": daten.get("zotero"),
        "dateien": _dateien(eid, daten) if mit_dateien else [],
    }


def _modell_quelle_heute(modell: str | None) -> str | None:
    return next((m["quelle"] for m in get_available_models() if m["name"] == modell), None)


# ---------- Formatierung ----------

def _prozent(x: float | None, sprache: str) -> str:
    if x is None:
        return "–"
    s = f"{x * 100:.1f}"
    return (s if sprache == "en" else s.replace(".", ",")) + " %"


def _tag(iso: str | None) -> str:
    return (iso or "")[:10] or "–"


def _groesse(n: int, sprache: str) -> str:
    for einheit, teiler in (("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
        if n >= teiler:
            s = f"{n / teiler:.1f}"
            return f"{s if sprache == 'en' else s.replace('.', ',')} {einheit}"
    return f"{n} B"


def _tabelle(kopf: list[str], zeilen: list[list[str]]) -> list[str]:
    sauber = lambda z: str(z).replace("|", "\\|").replace("\n", " ")
    return (["| " + " | ".join(kopf) + " |", "|" + "---|" * len(kopf)]
            + ["| " + " | ".join(sauber(z) for z in zeile) + " |" for zeile in zeilen] + [""])


def _spanne(werte: list[float], fmt) -> str:
    return "–" if not werte else (fmt(werte[0]) if len(werte) == 1
                                  else f"{fmt(min(werte))} – {fmt(max(werte))}")


def _modell_text(f: dict, t: dict) -> str:
    if not f["modell"]:
        return "–"
    herkunft = {"bundled": t["modell.mitgeliefert"], "eigen": t["modell.eigen"]}.get(
        f["modell_quelle"], t["modell.unbekannt"])
    zusatz = "" if f["modell_quelle_aufgezeichnet"] or not f["modell_quelle"] else f" {t['modell.heute']}"
    return f"`{f['modell']}` ({herkunft}{zusatz})"


def _sprecher_text(f: dict, t: dict) -> str:
    if not f["diarize"]:
        return t["diar.aus"]
    zahl = (f["sprecherzahl"] or "auto")
    zahl = t["diar.auto"] if zahl == "auto" else zahl.split("-")[0]
    trenn = "" if f["trennung"] is None else f"; {t['diar.trennung']} {str(f['trennung']).replace('.', t['dezimal'])}"
    return f"{t['diar.an']} ({t['diar.zahl']} {zahl}{trenn})"


def _kopf(t: dict, titel: str, einleitung: str, sprache: str) -> list[str]:
    heute = datetime.now(UTC).strftime("%Y-%m-%d")
    return [f"# {titel}", "", einleitung, "",
            t["kopf.erzeugt"].format(v=APP_VERSION, datum=heute), ""]


def _mass_zeilen(f: dict, t: dict, sprache: str) -> list[list[str]]:
    m = f["mass"]
    n, r, sp = m["text"]["normiert"], m["text"]["roh"], m["sprecher"]
    zeilen = [
        [t["mass.norm"], _prozent(n["rate"], sprache),
         t["mass.sdi"].format(s=n["ersetzt"], d=n["geloescht"], i=n["eingefuegt"], n=n["woerter_heute"])],
        [t["mass.orth"], _prozent(r["rate"], sprache),
         t["mass.sdi"].format(s=r["ersetzt"], d=r["geloescht"], i=r["eingefuegt"], n=r["woerter_heute"])],
    ]
    if sp["maschine_ohne_sprecher"]:
        zeilen.append([t["mass.sprechzeit"], "–", t["mass.ohne_maschine"]])
    else:
        zeilen.append([t["mass.sprechzeit"], _prozent(sp["eins_zu_eins"], sprache),
                       t["mass.sprechzeit.basis"].format(zeit=format_hms(sp["verglichen_s"]),
                                                         a=sp["sprecher_ausgang"], b=sp["sprecher_heute"])])
        zeilen.append([t["mass.sprechzeit.mehrheit"], _prozent(sp["mehrheit"], sprache),
                       t["mass.sprechzeit.mehrheit.text"]])
    return zeilen


def _nachweise(t: dict) -> list[str]:
    return [f"## {t['nachweise']}", ""] + [f"- {n}" for n in NACHWEISE] + [""]


# ---------- 1. Transkriptionsprotokoll ----------

def protokoll(eid: str, sprache: str) -> str:
    t, f = _texte(sprache), fakten(eid)
    z = _kopf(t, f"{t['p.titel']} — {f['name']}", t["p.einleitung"], sprache)
    z += [f"## {t['p.aufnahme']}", ""]
    zeilen = [[t["f.kennung"], f"`{f['id']}`"], [t["f.name"], f["name"]],
              [t["f.quelldatei"], f["datei"] or "–"], [t["f.dauer"], format_hms(f["dauer"])],
              [t["f.sprache"], f["sprache"] or "–"], [t["f.segmente"], str(f["segmente"])],
              [t["f.sprecher"], str(f["sprecher"])], [t["f.memos"], str(f["memos"])]]
    if f["zotero"] and f["zotero"].get("citekey"):
        zeilen.append(["Zotero", f"`{f['zotero']['citekey']}`"])
    z += _tabelle([t["feld"], t["wert"]], zeilen)

    z += [f"## {t['p.maschine']}", ""]
    if f["transkribiert"]:
        vad = {True: f"Silero VAD {SILERO}", False: t["vad.aus"], None: t["nicht_aufgezeichnet"]}[f["vad"]]
        z += _tabelle([t["feld"], t["wert"]], [
            [t["f.datum"], _tag(f["lauf_datum"])],
            [t["f.app"], f"ResearchTranscript {f['app'] or t['nicht_aufgezeichnet']}"],
            [t["f.erkennung"], f"whisper.cpp {WHISPER_CPP}, {t['f.modell.satz']} {_modell_text(f, t)}"],
            [t["f.vad"], vad],
            [t["f.trennung"], _sprecher_text(f, t)],
            [t["f.ort"], t["ort.lokal"]]])
    else:
        z += [t["p.importiert"].format(datei=f["datei"] or "?"), ""]

    z += [f"## {t['p.hand']}", ""]
    a = f["aenderungen"]
    z += _tabelle([t["feld"], t["wert"]], [
        [t["f.sitzungen"], str(f["sitzungen"])],
        [t["f.zeitraum"], "–" if not f["sitzungen"] else f"{_tag(f['hand_von'])} – {_tag(f['hand_bis'])}"],
        [t["f.journal"], t["journal.arten"].format(
            text=a.get("text", 0), sprecher=a.get("speaker", 0), zeit=a.get("time", 0),
            neu=a.get("new", 0), weg=a.get("removed", 0), name=a.get("name", 0))],
        [t["f.wer"], t["offen.wer"]], [t["f.abgehoert"], t["offen.abgehoert"]],
        [t["f.regeln"], t["offen.regeln"]], [t["f.pseudonym"], t["offen.pseudonym"]]])

    z += [f"## {t['p.mass']}", ""]
    if f["mass"] is None:
        anteil = f["hand_segmente"] / f["segmente"] if f["segmente"] else None
        z += [t["mass.fehlt"].format(anteil=_prozent(anteil, sprache), n=f["hand_segmente"],
                                     gesamt=f["segmente"]), ""]
    else:
        z += _tabelle([t["mass.kopf.mass"], t["wert"], t["mass.kopf.basis"]], _mass_zeilen(f, t, sprache))
        if f["ausgang"] == "verlauf":
            z += [t["mass.aus_verlauf"], ""]
        z += [t["mass.definition"], "", f"> {t['mass.vorbehalt']}", ""]

    z += [f"## {t['p.dateien']}", "", t["dateien.hinweis"], ""]
    z += _tabelle([t["datei"], t["groesse"], "SHA-256"],
                  [[f"`{d['name']}`", _groesse(d["bytes"], sprache), f"`{d['sha256']}`"] for d in f["dateien"]])
    return "\n".join(z + _nachweise(t))


# ---------- 2. Methodenbaustein (Korpus) ----------

def _median_spanne(werte: list[float], sprache: str) -> str:
    if not werte:
        return "–"
    return f"{_prozent(statistics.median(werte), sprache)} ({_spanne(werte, lambda x: _prozent(x, sprache))})"


def methoden(ids: list[str], sprache: str) -> str:
    t = _texte(sprache)
    fs = [fakten(e, mit_dateien=False) for e in ids]
    if not fs:
        raise ValueError("Keine Transkripte gewählt")
    dauern = [f["dauer"] for f in fs]
    mit = [f for f in fs if f["mass"] is not None]
    norm = [f["mass"]["text"]["normiert"]["rate"] for f in mit if f["mass"]["text"]["normiert"]["rate"] is not None]
    orth = [f["mass"]["text"]["roh"]["rate"] for f in mit if f["mass"]["text"]["roh"]["rate"] is not None]
    spz = [f["mass"]["sprecher"]["eins_zu_eins"] for f in mit if f["mass"]["sprecher"]["eins_zu_eins"] is not None]
    modelle = sorted({f["modell"] for f in fs if f["modell"]})
    versionen = sorted({f["app"] for f in fs if f["app"]})
    sprachen = sorted({f["sprache"] for f in fs if f["sprache"]})
    laeufe = sorted(_tag(f["lauf_datum"]) for f in fs if f["transkribiert"])
    importiert = sum(1 for f in fs if not f["transkribiert"])
    eigen = any(f["modell_quelle"] == "eigen" for f in fs)
    mittel = format_hms(statistics.mean(dauern))

    eines = len(fs) == 1            # der Regelfall: das Paket gilt EINEM Transkript
    ms = _median_spanne if not eines else (lambda w, sp: _prozent(w[0], sp) if w else "–")
    z = _kopf(t, t["m.titel"], t["m.einleitung.eins" if eines else "m.einleitung"], sprache)
    z += [f"## {t['m.korpus.eins' if eines else 'm.korpus']}", ""]
    z += _tabelle([t["feld"], t["wert"]], ([
        [t["f.name"], fs[0]["name"]], [t["f.dauer"], format_hms(dauern[0])]] if eines else [
        [t["m.n"], str(len(fs)) + (f" ({t['m.importiert'].format(n=importiert)})" if importiert else "")],
        [t["m.gesamt"], format_hms(sum(dauern))],
        [t["m.mittel"], f"{mittel} ({_spanne(dauern, format_hms)})"]]) + [
        [t["f.sprache"], ", ".join(sprachen) or "–"],
        [t["f.app"], ", ".join(f"ResearchTranscript {v}" for v in versionen) or t["nicht_aufgezeichnet"]],
        [t["f.erkennung"], f"whisper.cpp {WHISPER_CPP}, {t['f.modell.satz']} " + (", ".join(f"`{m}`" for m in modelle) or "–")
         + (f" — {t['m.eigen']}" if eigen else "")],
        [t["f.trennung"], t["m.diar"].format(n=sum(1 for f in fs if f["diarize"]), gesamt=len(fs))],
        [t["m.zeitraum"], _spanne(laeufe, str) if laeufe else "–"]])

    z += [f"## {t['p.mass' if eines else 'm.mass']}", ""]
    if not eines:
        z += [t["m.mass.text"].format(n=len(mit), gesamt=len(fs)), ""]
    elif not mit:
        z += [t["m.mass.fehlt"], ""]
    z += _tabelle([t["mass.kopf.mass"], t["wert" if eines else "m.median"]], [
        [t["mass.norm"], ms(norm, sprache)], [t["mass.orth"], ms(orth, sprache)],
        [t["mass.sprechzeit"], ms(spz, sprache)]])
    z += [t["mass.definition"], "", f"> {t['mass.vorbehalt']}", ""]

    z += [f"## {t['m.absatz']}", "", t["m.absatz.hinweis"], ""]
    absatz = t["m.absatz.text.eins" if eines else "m.absatz.text"].format(
        n=len(fs), gesamt=format_hms(sum(dauern)), mittel=mittel, spanne=_spanne(dauern, format_hms),
        version=", ".join(versionen) or "[ … ]", whisper=WHISPER_CPP,
        modell=", ".join(modelle) or "[ … ]", norm=ms(norm, sprache),
        diar=t["m.absatz.diar.eins" if eines else "m.absatz.diar"].format(sprechzeit=ms(spz, sprache))
        if any(f["diarize"] for f in fs) else "")
    z += [f"> {' '.join(absatz.split())}", ""]

    z += [f"## {t['m.offen']}", ""] + [f"- {t[k]}" for k in ("m.offen.wer", "m.offen.regeln",
                                                             "m.offen.pseudonym", "m.offen.einwilligung")] + [""]
    if eines:
        return "\n".join(z + _nachweise(t))
    z += [f"## {t['m.je']}", ""]
    z += _tabelle([t["f.name"], t["f.dauer"], t["f.modell"], t["mass.norm"], t["mass.orth"], t["mass.sprechzeit"]], [
        [f["name"], format_hms(f["dauer"]), f["modell"] or "–",
         _prozent(f["mass"]["text"]["normiert"]["rate"], sprache) if f["mass"] else "–",
         _prozent(f["mass"]["text"]["roh"]["rate"], sprache) if f["mass"] else "–",
         _prozent(f["mass"]["sprecher"]["eins_zu_eins"], sprache) if f["mass"] else "–"] for f in fs])
    return "\n".join(z + _nachweise(t))


# ---------- 3. Verfahrensbaustein (Projekt) ----------

def verfahren(sprache: str) -> str:
    t = _texte(sprache)
    modelle = get_available_models()
    z = _kopf(t, t["v.titel"], t["v.einleitung"], sprache)
    z += [f"## {t['v.schritte']}", ""]
    z += _tabelle([t["v.schritt"], t["v.werkzeug"], t["v.wo"]],
                  [[t[f"v.s{k}.a"], t[f"v.s{k}.b"].format(whisper=WHISPER_CPP, silero=SILERO), t[f"v.s{k}.c"]]
                   for k in range(1, 7)])
    z += [t["v.modelle"], ""]
    z += _tabelle([t["f.modell"], t["groesse"], t["v.herkunft"]],
                  [[f"`{m['name']}`", _groesse(int(m["size_mb"] * 1e6), sprache),
                    t["modell.mitgeliefert"] if m["quelle"] == "bundled" else t["modell.eigen"]] for m in modelle])
    for k in ("nicht", "ablage", "export"):
        z += [f"## {t[f'v.{k}']}", ""] + [f"- {p}" for p in t[f"v.{k}.punkte"].split("\n")] + [""]
    z += [f"## {t['v.offen']}", "", t["v.offen.text"], ""]
    z += _tabelle([t["feld"], t["v.eintrag"], t["v.hinweis"]],
                  [[a, "[ … ]", b] for a, b in (p.split(" :: ", 1) for p in t["v.offen.felder"].split("\n"))])
    z += [f"## {t['v.warnung']}", ""] + [f"- {p}" for p in t["v.warnung.punkte"].split("\n")] + [""]
    return "\n".join(z)


# ---------- 4. Repositoriums-Datenblatt ----------

def _urheber(fs: list[dict]) -> list[str]:
    """Vorschlag für Creators: nur Zotero-Personen, die NICHT zur befragten
    Seite gehören (Interviewer:in, Mitwirkende …)."""
    aus: list[str] = []
    for f in fs:
        for c in (f["zotero"] or {}).get("creators") or []:
            if c.get("role") in BEFRAGTE:
                continue
            name = ", ".join(filter(None, [c.get("last"), c.get("first")]))
            eintrag = f"{name} ({c.get('role')})"
            if name and eintrag not in aus:
                aus.append(eintrag)
    return aus


def repositorium(ids: list[str], sprache: str) -> str:
    t = _texte(sprache)
    fs = [fakten(e) for e in ids]
    if not fs:
        raise ValueError("Keine Transkripte gewählt")
    offen = "[ … ]"
    sprachen = sorted({f["sprache"] for f in fs if f["sprache"] and f["sprache"] != "auto"})
    jahre = sorted({str((f["zotero"] or {}).get("year") or (f["zotero"] or {}).get("date") or "")[:4]
                    for f in fs} - {""})
    titel = (fs[0]["zotero"] or {}).get("title") if len(fs) == 1 else None
    abstract = (fs[0]["zotero"] or {}).get("abstract") if len(fs) == 1 else None
    urheber = _urheber(fs)
    befragte = any(c.get("role") in BEFRAGTE for f in fs for c in (f["zotero"] or {}).get("creators") or [])
    dois = sorted({(f["zotero"] or {}).get("doi") for f in fs} - {None, ""})
    modelle = sorted({f["modell"] for f in fs if f["modell"]})
    technik = t["r.technik.wert"].format(
        version=", ".join(sorted({f["app"] for f in fs if f["app"]})) or APP_VERSION,
        whisper=WHISPER_CPP, modell=", ".join(modelle) or "–")
    vorschlag = lambda w: f"{w} — {t['r.vorschlag']}" if w else offen

    z = _kopf(t, t["r.dok"], t["r.einleitung"].format(n=len(fs)), sprache)
    z += [f"## {t['r.warnung']}", ""] + [f"- {p}" for p in t["r.warnung.punkte"].split("\n")] + [""]

    def gruppe(name: str, zeilen: list[tuple[str, str, str]]) -> None:
        z.extend([f"## {t[name]}", ""])
        z.extend(_tabelle([t["feld"], t["r.status"], t["wert"], t["r.erlaeuterung"]],
                          [[t[f"r.{k}"], t[f"r.st.{st}"], wert, t[f"r.{k}.e"]] for k, st, wert in zeilen]))

    gruppe("r.g.beschreibung", [
        ("titel", "pflicht", vorschlag(titel)), ("typ", "pflicht", "Dataset"),
        ("pubdatum", "pflicht", offen), ("abstract", "empfohlen", vorschlag(abstract)),
        ("schlagworte", "empfohlen", offen), ("sprache", "optional", ", ".join(sprachen) or offen),
        ("erhebung", "empfohlen", vorschlag(_spanne(jahre, str) if jahre else "")),
        ("ort", "optional", offen), ("version", "optional", "1.0"), ("publisher", "pflicht", offen),
        ("verwandt", "empfohlen", ", ".join(dois) or offen), ("foerderung", "optional", offen)])
    gruppe("r.g.personen", [
        ("creators", "pflicht", vorschlag("; ".join(urheber)) + (f" {t['r.befragte_weg']}" if befragte else "")),
        ("contributors", "empfohlen", offen), ("kontakt", "empfohlen", offen), ("rechteinhaber", "optional", offen)])
    gruppe("r.g.rechte", [
        ("lizenz", "pflicht", offen), ("zugang", "pflicht", offen),
        ("embargo", "optional", offen), ("bedingungen", "optional", offen)])
    gruppe("r.g.methode", [
        ("methode", "empfohlen", offen), ("sampling", "archiv", offen),
        ("umfang", "optional", t["r.umfang.wert"].format(n=len(fs), dauer=format_hms(sum(f["dauer"] for f in fs)))),
        ("technik", "empfohlen", technik), ("konventionen", "archiv", t["r.konventionen.wert"]),
        ("anonymisierung", "archiv", offen), ("begleit", "archiv", offen)])

    z += [f"## {t['r.g.dateien']}", "", t["r.dateien.text"], ""]
    z += _tabelle([t["f.name"], t["datei"], t["groesse"], "SHA-256"],
                  [[f["name"], f"`{d['name']}`", _groesse(d["bytes"], sprache), f"`{d['sha256']}`"]
                   for f in fs for d in f["dateien"]])
    z += [t["r.formate"], ""] + [f"- {p}" for p in t["r.formate.punkte"].split("\n")] + [""]

    z += [f"## {t['r.g.ethik']}", "", t["r.ethik.text"], ""]
    z += _tabelle([t["r.pruefpunkt"], t["r.erledigt"], t["r.erlaeuterung"]],
                  [[a, "[ ]", b] for a, b in (p.split(" :: ", 1) for p in t["r.ethik.punkte"].split("\n"))])

    z += [f"## {t['r.wohin']}", ""]
    z += _tabelle([t["r.repo"], t["r.repo.fuer"], "URL"],
                  [p.split(" :: ") for p in t["r.repos"].split("\n")])
    z += [f"## {t['r.quellen']}", ""] + [f"- {p}" for p in t["r.quellen.punkte"].split("\n")] + [""]
    return "\n".join(z)


# ---------- Zitierdatei ----------

APP_JAHR = "2026"
REPO = "https://github.com/bias-city/ResearchTranscript"
SEITE = "https://bias.city/researchtranscript/"


def zitate_bib() -> str:
    """BibLaTeX für Zotero (Datei › Importieren): die App als Eintragsart
    «Software» — Titel, Programmierer, Version, Datum, System, Firma, Ort,
    Lizenz, URL — und dazu alles, was ein Methodenteil zitiert. `@software`
    liest Zotero als Software; ältere BibTeX-Stile behandeln es wie @misc."""
    heute = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"""% ResearchTranscript — Zitierdatei (BibLaTeX). In Zotero: Datei > Importieren.
% Erzeugt von ResearchTranscript {APP_VERSION} am {heute}.

@software{{researchtranscript,
  title        = {{ResearchTranscript}},
  author       = {{Pohl, Ben}},
  version      = {{{APP_VERSION}}},
  date         = {{{APP_JAHR}}},
  organization = {{B/IAS – Basel Institut für angewandte Stadtforschung}},
  location     = {{Basel}},
  license      = {{AGPL-3.0-or-later}},
  url          = {{{SEITE}}},
  urldate      = {{{heute}}},
  note         = {{macOS (Apple Silicon). Quellcode: {REPO}}},
  abstract     = {{Lokale Transkription von Interviews mit Sprechertrennung (whisper.cpp, SpeakerKit/pyannote) und Editor; keine Übertragung von Aufnahmen oder Texten.}}
}}

@online{{radford2022whisper,
  title      = {{Robust Speech Recognition via Large-Scale Weak Supervision}},
  author     = {{Radford, Alec and Kim, Jong Wook and Xu, Tao and Brockman, Greg and McLeavey, Christine and Sutskever, Ilya}},
  date       = {{2022}},
  eprint     = {{2212.04356}},
  eprinttype = {{arXiv}},
  url        = {{https://arxiv.org/abs/2212.04356}}
}}

@software{{whispercpp,
  title   = {{whisper.cpp}},
  author  = {{Gerganov, Georgi and {{ggml-org contributors}}}},
  version = {{{WHISPER_CPP}}},
  license = {{MIT}},
  url     = {{https://github.com/ggml-org/whisper.cpp}}
}}

@online{{whisperlargev3turbo,
  title  = {{whisper-large-v3-turbo}},
  author = {{{{OpenAI}}}},
  date   = {{2024}},
  note   = {{Modellkarte, MIT}},
  url    = {{https://huggingface.co/openai/whisper-large-v3-turbo}}
}}

@inproceedings{{plaquet2023powerset,
  title     = {{Powerset multi-class cross entropy loss for neural speaker diarization}},
  author    = {{Plaquet, Alexis and Bredin, Hervé}},
  booktitle = {{Proc. Interspeech 2023}},
  pages     = {{3222--3226}},
  date      = {{2023}},
  doi       = {{10.21437/Interspeech.2023-205}}
}}

@inproceedings{{bredin2023pyannote,
  title     = {{pyannote.audio 2.1 speaker diarization pipeline: principle, benchmark, and recipe}},
  author    = {{Bredin, Hervé}},
  booktitle = {{Proc. Interspeech 2023}},
  pages     = {{1983--1987}},
  date      = {{2023}},
  doi       = {{10.21437/Interspeech.2023-105}}
}}

@online{{pyannotecommunity1,
  title  = {{speaker-diarization-community-1}},
  author = {{{{pyannote}}}},
  date   = {{2025}},
  note   = {{Modellkarte, CC BY 4.0}},
  url    = {{https://huggingface.co/pyannote/speaker-diarization-community-1}}
}}

@software{{argmaxoss,
  title   = {{Argmax OSS: WhisperKit, SpeakerKit}},
  author  = {{{{Argmax, Inc.}}}},
  version = {{{SPEAKERKIT.split()[-1]}}},
  license = {{MIT}},
  url     = {{https://github.com/argmaxinc/argmax-oss-swift}}
}}

@software{{silerovad,
  title   = {{Silero VAD}},
  author  = {{{{Silero Team}}}},
  version = {{{SILERO}}},
  license = {{MIT}},
  url     = {{https://github.com/snakers4/silero-vad}}
}}

@inproceedings{{snover2006ter,
  title     = {{A Study of Translation Edit Rate with Targeted Human Annotation}},
  author    = {{Snover, Matthew and Dorr, Bonnie and Schwartz, Richard and Micciulla, Linnea and Makhoul, John}},
  booktitle = {{Proceedings of AMTA 2006}},
  date      = {{2006}},
  url       = {{https://aclanthology.org/2006.amta-papers.25/}}
}}

@article{{wollingiering2024,
  title        = {{Automatic Transcription of English and German Qualitative Interviews}},
  author       = {{Wollin-Giering, Susanne and Hoffmann, Markus and Höfting, Jonas and Ventzke, Carla}},
  journaltitle = {{Forum Qualitative Sozialforschung / Forum: Qualitative Social Research}},
  volume       = {{25}},
  number       = {{1}},
  date         = {{2024}},
  doi          = {{10.17169/fqs-25.1.4129}}
}}
"""


def paket(ids: list[str], sprache: str) -> bytes:
    """Dokumentationspaket (User 2026-09-18): alle Begleitdokumente zur
    Auswahl in EINEM Zip — je als .md und .docx, dazu die Zitierdatei."""
    import io
    import zipfile

    from . import docx
    if not ids:
        raise ValueError("Keine Transkripte gewählt")
    t = _texte(sprache)
    teile: list[tuple[str, str]] = [
        (t["datei.methoden"], methoden(ids, sprache)),
        (t["datei.repositorium"], repositorium(ids, sprache)),
        (t["datei.verfahren"], verfahren(sprache))]
    gesehen: set[str] = set()
    for eid in ids:
        stamm = bibliothek._slug(bibliothek.lese(eid)["name"]) or eid
        while stamm in gesehen:
            stamm += "_"
        gesehen.add(stamm)
        teile.append((f"{t['paket.protokolle']}/{stamm}-{t['datei.protokoll']}", protokoll(eid, sprache)))
    inhalt = [f"# {t['paket.titel']}", "", t["paket.text"], ""]
    inhalt += [f"- `{name}.md` / `.docx`" for name, _ in teile] + ["- `researchtranscript.bib` — " + t["paket.bib"], ""]
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as zf:
        wurzel = t["paket.ordner"]
        zf.writestr(f"{wurzel}/{t['paket.liesmich']}.md", "\n".join(inhalt))
        zf.writestr(f"{wurzel}/researchtranscript.bib", zitate_bib())
        for name, md in teile:
            zf.writestr(f"{wurzel}/{name}.md", md)
            zf.writestr(f"{wurzel}/{name}.docx", docx.aus_markdown(md, titel=md.splitlines()[0].lstrip("# ")))
    return puffer.getvalue()


# ---------- Ausgabe ----------

def erzeuge(art: str, ids: list[str], sprache: str, format: str) -> tuple[bytes, str]:
    """(Inhalt, Dateiname). `format`: md | docx; «paket» ist immer ein Zip,
    «zitate» immer eine .bib."""
    sprache_ok = sprache if sprache in SPRACHEN else "de"
    if art == "paket":
        return paket(ids, sprache_ok), f"{_texte(sprache_ok)['paket.ordner']}.zip"
    if art == "zitate":
        return zitate_bib().encode("utf-8"), "researchtranscript.bib"
    if art not in ARTEN or format not in ("md", "docx"):
        raise ValueError(f"Unbekanntes Dokument: {art}.{format}")
    sprache = sprache if sprache in SPRACHEN else "de"
    if art == "protokoll":
        if len(ids) != 1:
            raise ValueError("Das Transkriptionsprotokoll gilt für genau ein Transkript")
        md = protokoll(ids[0], sprache)
    elif art == "methoden":
        md = methoden(ids, sprache)
    elif art == "repositorium":
        md = repositorium(ids, sprache)
    else:
        md = verfahren(sprache)
    t = _texte(sprache)
    name = t[f"datei.{art}"]
    if format == "md":
        return md.encode("utf-8"), f"{name}.md"
    from . import docx
    return docx.aus_markdown(md, titel=md.splitlines()[0].lstrip("# ")), f"{name}.docx"
