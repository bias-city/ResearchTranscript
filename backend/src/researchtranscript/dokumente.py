"""Dokumentationspaket für Forschende — je Transkript EIN Zip (BACKLOG 16).

Zuschnitt (User 2026-09-18, docs/begleitdokumente.md): Aussagen gelten für
das einzelne Dokument; im Zip nur Word-Dateien, kurz, in Unterordnern:

  LIESMICH.docx                      Wegweiser; Warnhinweise EINMAL
  1-methoden/transkriptionsprotokoll Lauf, Bearbeitung, Eingriff, Dateien
  1-methoden/methodenabsatz          kurz + ausführlich, offene Felder, Zitat
  2-datenschutz/app-tatsachen        was die App tut/nicht tut, wo Daten liegen
  2-datenschutz/angaben-der-stelle   Formular für die verantwortliche Stelle
  3-datenablage/datenblatt-datensatz Felder wie im Zenodo-Formular
  3-datenablage/datenblatt-interview was zu DIESEM Interview gehört
  3-datenablage/ethik-checkliste     Prüfpunkte, mit «trifft nicht zu»
  3-datenablage/repositorien-und-vorgaben
  zitieren/researchtranscript.bib    Software + Modelle für Zotero

Grundsätze: Die App behauptet nichts, was sie nicht weiss. Für Läufe von
vor 0.6.0 (LocalTranscript, TurnScript) stehen nur aufgezeichnete Angaben.
Das Eingriffsmass heisst «Korrekturrate», nie «Fehlerrate»/«Genauigkeit».
Aus Zotero kommt nie ein Titel- oder Beschreibungsvorschlag (Interview-
Titel sind oft Namen) und nie eine Person der befragten Seite. Quellen in
den Dokumenten: nur Technik (Repos, Modellkarten) und die Vorgaben der
Repositorien; die Fachliteratur steht in der .bib.

Texte viersprachig in `dokumente_texte/<sprache>.py` (de = Quelle).
"""
from __future__ import annotations

import hashlib
import importlib
import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from . import bibliothek, docx, eingriff
from .ausgabe import format_hms
from .config import APP_VERSION

SPRACHEN = ("de", "en", "fr", "it")

#: Mitgelieferte Bestandteile — dieselben Stände wie scripts/gen-licenses.py.
#: jobs._lauf_fakten zeichnet sie je Lauf auf; für ältere Läufe gelten sie nicht.
WHISPER_CPP = "1.8.2"
SILERO = "v5.1.2"
SPEAKERKIT = "argmax-oss-swift ea872ff"
APP_JAHR = "2026"
REPO = "https://github.com/bias-city/ResearchTranscript"
SEITE = "https://bias.city/researchtranscript/"

#: Zotero-Rollen der befragten Seite: nie als Urheber vorschlagen
BEFRAGTE = {"interviewee", "guest", "castMember", "author"}
APP_NAMEN = {"researchtranscript": "ResearchTranscript", "localtranscript": "LocalTranscript",
             "turnscript": "TurnScript"}
OFFEN = "[ … ]"


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
    aus = []
    for n in ("transkript.json", bibliothek.AUSGANG, daten.get("audio"), daten.get("video")):
        p = ordner / n if n else None
        if p is not None and p.is_file():
            aus.append({"name": n, "bytes": p.stat().st_size, "sha256": _sha256(p)})
    return aus


def _journal_mass(hand: list[dict], heute: int) -> dict:
    """Eingriff laut Journal (User 2026-09-18: «der Grad der Eingriffe kann
    doch aus den Protokollen entnommen werden»): verschiedene Segmente je
    Art der Änderung. Innerhalb einer Sitzung überschreibt die letzte Art
    die frühere (bibliothek.journal_eintrag) — darum Mindestwerte."""
    nach_art: dict[str, set[str]] = {}
    for r in hand:
        for rid, art in (r.get("changed") or {}).items():
            nach_art.setdefault(art, set()).add(rid)
    seg = {a: nach_art.get(a, set()) for a in ("text", "speaker", "time")}
    alle = seg["text"] | seg["speaker"] | seg["time"]
    anteil = lambda n: (n / heute) if heute else None
    return {"segmente": heute,
            "text": len(seg["text"]), "sprecher": len(seg["speaker"]), "zeit": len(seg["time"]),
            "summe": len(alle), "text_anteil": anteil(len(seg["text"])),
            "sprecher_anteil": anteil(len(seg["speaker"])), "summe_anteil": anteil(len(alle)),
            "neu": len(nach_art.get("new", ())), "weg": len(nach_art.get("removed", ())),
            "name": len(nach_art.get("name", ()))}


def fakten(eid: str) -> dict:
    daten = bibliothek.lese(eid)
    seg = daten.get("segmente", [])
    q = daten.get("quelle", {}) or {}
    journal = daten.get("journal", [])
    maschine = next((r for r in journal if r.get("origin") == "machine"), None)
    hand = [r for r in journal if r.get("origin") == "human"
            and any(k != "zotero" for k in (r.get("changed") or {}))]
    app_roh = (maschine or {}).get("who", {}).get("app") or ""
    kurz, _, version = app_roh.partition("/")
    wer: dict[str, int] = {}
    for r in hand:
        w = r.get("who", {})
        schluessel = w.get("user") or f"#{w.get('install') or '?'}"
        wer[schluessel] = wer.get(schluessel, 0) + 1
    ausgang, woher = bibliothek.ausgangsstand(eid)
    return {
        "id": daten["id"], "name": daten.get("name", ""), "datei": q.get("datei"),
        "transkribiert": q.get("erzeugt") == "transcription",
        "dauer": max((s.get("end", 0) for s in seg), default=0.0),
        "sprache": q.get("language"), "modell": q.get("model"),
        # «aufgezeichnet»: der Lauf hat seine Fakten selbst festgehalten (ab 0.6.0)
        "aufgezeichnet": bool(q.get("app")), "modell_quelle": q.get("modell_quelle"),
        "whisper_cpp": q.get("whisper_cpp"), "vad": q.get("vad"), "motor": q.get("motor"),
        "diarize": q.get("diarize"), "sprecherzahl": q.get("sprecherzahl"), "trennung": q.get("trennung"),
        "app_name": APP_NAMEN.get(kurz.lower(), kurz or "ResearchTranscript"),
        "app_version": q.get("app") or version or None,
        "lauf_datum": (maschine or {}).get("finished") or daten.get("created"),
        "segmente": len(seg), "sprecher": len(daten.get("sprecher", [])),
        "memos": sum(1 for s in seg if s.get("memo")),
        "sitzungen": len(hand), "wer": wer,
        "hand_von": min((r.get("started") for r in hand if r.get("started")), default=None),
        "hand_bis": max((r.get("finished") for r in hand if r.get("finished")), default=None),
        "journal": _journal_mass(hand, len(seg)),
        "ausgang": woher, "mass": eingriff.vergleiche(ausgang, daten) if ausgang is not None else None,
        "zotero": daten.get("zotero"), "dateien": _dateien(eid, daten),
    }


# ---------- Formatierung ----------

def _prozent(x: float | None, t: dict) -> str:
    return "–" if x is None else f"{x * 100:.1f}".replace(".", t["dezimal"]) + " %"


def _tag(iso: str | None) -> str:
    return (iso or "")[:10] or "–"


def _groesse(n: int, t: dict) -> str:
    for einheit, teiler in (("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
        if n >= teiler:
            return f"{n / teiler:.1f}".replace(".", t["dezimal"]) + f" {einheit}"
    return f"{n} B"


def _tabelle(kopf: list[str], zeilen: list[list[str]]) -> list[str]:
    sauber = lambda z: str(z).replace("|", "\\|").replace("\n", " ")
    return (["| " + " | ".join(kopf) + " |", "|" + "---|" * len(kopf)]
            + ["| " + " | ".join(sauber(z) for z in zeile) + " |" for zeile in zeilen] + [""])


def _punkte(text: str) -> list[str]:
    return [f"- {p}" for p in text.split("\n")] + [""]


def _spalten(text: str) -> list[list[str]]:
    return [p.split(" :: ") for p in text.split("\n")]


def _app(f: dict, t: dict, *, kurz: bool = False) -> str:
    """Wie die App beim Lauf hiess. «ResearchTranscript 2.5.0» gab es nie."""
    version = f["app_version"] or t["nicht_aufgezeichnet"]
    if f["app_name"] == "ResearchTranscript":
        return t["a.app.neu"].format(version=version)
    return (t["a.app.alt"] if kurz else t["app.vorgaenger"]).format(name=f["app_name"], version=version)


def _fuss(f: dict | None, t: dict) -> list[str]:
    heute = datetime.now(UTC).strftime("%Y-%m-%d")
    return ["---", "", t["fuss"].format(v=APP_VERSION, datum=heute, name=(f or {}).get("name", "–")), ""]


# ---------- 1a Transkriptionsprotokoll ----------

def protokoll(f: dict, t: dict) -> str:
    z = [f"# {t['p.titel']}", "", t["p.einleitung"], "", f"## {t['p.transkript']}", ""]
    z += _tabelle([t["feld"], t["wert"]], [
        [t["f.name"], f["name"]], [t["f.quelldatei"], f["datei"] or "–"],
        [t["f.dauer"], format_hms(f["dauer"])], [t["f.sprache"], f["sprache"] or "–"],
        [t["f.segmente"], str(f["segmente"])], [t["f.sprecher"], str(f["sprecher"])],
        [t["f.memos"], str(f["memos"])],
        [t["f.zotero"], t["zotero.ja" if f["zotero"] else "zotero.nein"]]])

    z += [f"## {t['p.maschine']}", ""]
    if f["transkribiert"]:
        neu = f["aufgezeichnet"]
        herkunft = {"bundled": t["modell.mitgeliefert"], "eigen": t["modell.eigen"]}.get(
            f["modell_quelle"], t["modell.unbekannt"])
        erkennung = (t["erkennung.wert"].format(whisper=f["whisper_cpp"] or WHISPER_CPP,
                                                modell=f["modell"], herkunft=herkunft)
                     if neu else t["erkennung.alt"].format(modell=f["modell"]))
        if not f["diarize"]:
            trennung = t["diar.aus"]
        else:
            zahl = f["sprecherzahl"] or "auto"
            trennung = t["diar.an"].format(zahl=t["diar.auto"] if zahl == "auto" else zahl.split("-")[0])
            if f["trennung"] is not None:
                trennung += "; " + t["diar.schwelle"].format(
                    wert=str(f["trennung"]).replace(".", t["dezimal"]))
        zeilen = [[t["f.datum"], _tag(f["lauf_datum"])], [t["f.app"], _app(f, t)],
                  [t["f.erkennung"], erkennung], [t["f.trennung"], trennung]]
        if neu:
            vad = (t["vad.diar"] if f["diarize"] else
                   t["vad.an"].format(silero=SILERO) if f["vad"] else t["vad.aus"])
            zeilen.insert(3, [t["f.vad"], vad])
        zeilen.append([t["f.ort"], t["ort.neu" if neu else "ort.alt"]])
        z += _tabelle([t["feld"], t["wert"]], zeilen)
    else:
        z += [t["p.importiert"].format(datei=f["datei"] or "?"), ""]

    z += [f"## {t['p.hand']}", ""]
    wer = "; ".join(t["wer.eintrag"].format(
        wer=(t["wer.install"].format(kennung=k[1:]) if k.startswith("#") else k), n=n)
        for k, n in sorted(f["wer"].items())) or "–"
    z += _tabelle([t["feld"], t["wert"]], [
        [t["f.sitzungen"], t["sitzungen.text"].format(n=f["sitzungen"])],
        [t["f.zeitraum"], "–" if not f["sitzungen"] else f"{_tag(f['hand_von'])} – {_tag(f['hand_bis'])}"],
        [t["f.wer"], wer], [t["f.rolle"], t["offen.rolle"]], [t["f.abgehoert"], t["offen.abgehoert"]],
        [t["f.regeln"], t["offen.regeln"]], [t["f.pseudonym"], t["offen.pseudonym"]]])

    z += [f"## {t['p.eingriff']}", "", f"### {t['e.journal']}", ""]
    j = f["journal"]
    von = lambda n, a: t["von"].format(n=n, gesamt=j["segmente"], anteil=_prozent(a, t))
    z += _tabelle([t["mass.kopf"], t["wert"]], [
        [t["e.j.text"], von(j["text"], j["text_anteil"])],
        [t["e.j.sprecher"], von(j["sprecher"], j["sprecher_anteil"])],
        [t["e.j.summe"], von(j["summe"], j["summe_anteil"])]])
    z += [t["e.journal.text"] + " " + t["e.j.weitere"].format(neu=j["neu"], weg=j["weg"], name=j["name"]), ""]
    z += [f"### {t['e.wort']}", ""]
    if f["mass"] is None:
        z += [t["e.wort.fehlt"], ""]
    else:
        n, r, sp = f["mass"]["text"]["normiert"], f["mass"]["text"]["roh"], f["mass"]["sprecher"]
        sdi = lambda m: t["mass.sdi"].format(s=m["ersetzt"], d=m["geloescht"], i=m["eingefuegt"],
                                             n=m["woerter_heute"])
        zeilen = [[t["mass.norm"], _prozent(n["rate"], t), sdi(n)], [t["mass.orth"], _prozent(r["rate"], t), sdi(r)]]
        if sp["maschine_ohne_sprecher"]:
            zeilen.append([t["mass.sprechzeit"], "–", t["mass.ohne_maschine"]])
        elif sp["eins_zu_eins"] is not None:
            zeilen.append([t["mass.sprechzeit"], _prozent(sp["eins_zu_eins"], t),
                           t["mass.sprechzeit.basis"].format(zeit=format_hms(sp["verglichen_s"]),
                                                             a=sp["sprecher_ausgang"], b=sp["sprecher_heute"])])
            zeilen.append([t["mass.mehrheit"], _prozent(sp["mehrheit"], t), t["mass.mehrheit.text"]])
        z += _tabelle([t["mass.kopf"], t["wert"], t["mass.basis"]], zeilen)
        if f["ausgang"] == "verlauf":
            z += [t["e.wort.verlauf"], ""]
        z += [t["mass.definition"], ""]
    z += [f"> {t['mass.vorbehalt']}", ""]

    z += [f"## {t['p.dateien']}", "", t["dateien.text"]
          + (" " + t["dateien.ausgang"] if any(d["name"] == bibliothek.AUSGANG for d in f["dateien"]) else ""), ""]
    z += _tabelle([t["datei"], t["groesse"], "SHA-256"],
                  [[f"`{d['name']}`", _groesse(d["bytes"], t), f"`{d['sha256']}`"] for d in f["dateien"]])
    z += [f"## {t['p.software']}", ""] + _punkte(t["software.punkte"])
    return "\n".join(z + _fuss(f, t))


# ---------- 1b Methodenabsatz ----------

def _eingriff_satz(f: dict, t: dict) -> str:
    m, j = f["mass"], f["journal"]
    if m is not None and m["text"]["normiert"]["rate"] is not None:
        sp = m["sprecher"]["eins_zu_eins"]
        zusatz = t["a.s5.sprechzeit"].format(wert=_prozent(sp, t)) if sp is not None else ""
        return t["a.s5.wort"].format(norm=_prozent(m["text"]["normiert"]["rate"], t), sprechzeit=zusatz)
    if f["sitzungen"]:
        return t["a.s5.journal"].format(text=_prozent(j["text_anteil"], t),
                                        sprecher=_prozent(j["sprecher_anteil"], t))
    return ""


def absatz(f: dict, t: dict) -> str:
    app, modell = _app(f, t, kurz=True), f["modell"] or OFFEN
    eingriff_satz = _eingriff_satz(f, t)
    lang = [t["a.s1"].format(dauer=format_hms(f["dauer"]), app=app), t["a.s2"].format(modell=modell)]
    if f["diarize"]:
        lang.append(t["a.s3"])
    lang.append(t["a.s4"])
    if eingriff_satz:
        lang += [eingriff_satz, t["a.s6"]]
    kurz = [t["a.k1"].format(app=app, modell=modell)] + ([eingriff_satz] if eingriff_satz else [])
    z = [f"# {t['a.titel']}", "", t["a.einleitung"], "",
         f"## {t['a.kurz']}", "", "> " + " ".join(kurz), "",
         f"## {t['a.lang']}", "", "> " + " ".join(lang), "",
         f"## {t['a.offen']}", ""] + _punkte(t["a.offen.punkte"])
    z += [f"## {t['a.zitieren']}", "",
          t["a.zitieren.text"].format(jahr=APP_JAHR, v=APP_VERSION, zitieren=t["ordner.zitieren"]), ""]
    return "\n".join(z + _fuss(f, t))


# ---------- 2 Datenschutz ----------

def tatsachen(f: dict | None, t: dict) -> str:
    z = [f"# {t['t.titel']}", "", t["t.einleitung"].format(v=APP_VERSION), "", f"## {t['t.schritte']}", ""]
    z += _tabelle([t["t.schritt"], t["t.werkzeug"], t["t.wo"]],
                  _spalten(t["t.schritte.zeilen"].format(whisper=WHISPER_CPP, silero=SILERO)))
    for k in ("schutz", "nicht", "ablage", "person", "export"):
        z += [f"## {t[f't.{k}']}", ""] + _punkte(t[f"t.{k}.punkte"])
    return "\n".join(z + _fuss(f, t))


def stelle(f: dict | None, t: dict) -> str:
    z = [f"# {t['s.titel']}", "", t["s.einleitung"], ""]
    z += _tabelle([t["feld"], t["eintrag"], t["hinweis"]], [[a, OFFEN, b] for a, b in _spalten(t["s.felder"])])
    z += [f"## {t['s.achten']}", ""] + _punkte(t["s.achten.punkte"])
    z += [f"## {t['s.entfernen']}", "", t["s.entfernen.text"], ""] + _punkte(t["s.entfernen.punkte"])
    return "\n".join(z + _fuss(f, t))


# ---------- 3 Datenablage ----------

def _urheber(f: dict) -> list[str]:
    aus: list[str] = []
    for c in (f["zotero"] or {}).get("creators") or []:
        name = ", ".join(filter(None, [c.get("last"), c.get("first")]))
        if c.get("role") not in BEFRAGTE and name:
            aus.append(f"{name} ({c.get('role')})")
    return aus


def datensatz(f: dict, t: dict) -> str:
    zot = f["zotero"] or {}
    urheber = _urheber(f)
    werte = {"creators": f"{'; '.join(urheber)} — {t['r.vorschlag']}" if urheber else OFFEN,
             "sprachen": f["sprache"] if f["sprache"] and f["sprache"] != "auto" else OFFEN,
             "dois": f"{zot['doi']} — {t['r.vorschlag']}" if zot.get("doi") else OFFEN}
    z = [f"# {t['d.titel']}", "", t["d.einleitung"], ""]
    z += _tabelle([t["feld"], t["r.status"], t["eintrag"], t["hinweis"]],
                  [[a, t[f"r.st.{st}"], wert.format(**werte), b] for a, st, wert, b in _spalten(t["d.zeilen"])])
    if any(c.get("role") in BEFRAGTE for c in zot.get("creators") or []):
        z += [t["d.befragte"], ""]
    z += [f"## {t['d.archiv']}", ""] + _punkte(t["d.archiv.punkte"])
    return "\n".join(z + _fuss(f, t))


def interview(f: dict, t: dict) -> str:
    jahr = str((f["zotero"] or {}).get("year") or (f["zotero"] or {}).get("date") or "")[:4]
    z = [f"# {t['i.titel']}", "", t["i.einleitung"], ""]
    z += _tabelle([t["feld"], t["eintrag"]], [
        [t["i.umfang"], t["i.umfang.wert"].format(dauer=format_hms(f["dauer"]), segmente=f["segmente"],
                                                  sprecher=f["sprecher"])],
        [t["i.sprache"], f["sprache"] or OFFEN],
        [t["i.jahr"], f"{jahr} — {t['r.vorschlag']}" if jahr else OFFEN],
        [t["i.verfahren"], t["i.verfahren.wert"].format(app=_app(f, t, kurz=True), modell=f["modell"] or OFFEN)],
        [t["i.konventionen"], t["i.konventionen.wert"]], [t["i.pseudonym"], t["i.pseudonym.wert"]]])
    z += [f"## {t['i.formate']}", ""] + _punkte(t["i.formate.punkte"])
    return "\n".join(z + _fuss(f, t))


def ethik(f: dict | None, t: dict) -> str:
    z = [f"# {t['e.titel']}", "", t["e.einleitung"], ""]
    z += _tabelle([t["e.punkt"], t["e.ja"], t["e.nz"], t["hinweis"]],
                  [[a, "[ ]", "[ ]", b] for a, b in _spalten(t["e.punkte"])])
    return "\n".join(z + _fuss(f, t))


def repos(f: dict | None, t: dict) -> str:
    z = [f"# {t['o.titel']}", "", t["o.einleitung"], "", f"## {t['o.zenodo']}", ""] + _punkte(t["o.zenodo.punkte"])
    z += [f"## {t['o.repos']}", ""] + _tabelle([t["o.repo"], t["o.fuer"], "URL"], _spalten(t["o.repos.zeilen"]))
    z += [f"## {t['o.vorgaben']}", ""] + _punkte(t["o.vorgaben.punkte"])
    return "\n".join(z + _fuss(f, t))


def liesmich(f: dict, t: dict) -> str:
    namen = {k: t[f"ordner.{k}"] for k in ("methoden", "datenschutz", "ablage", "zitieren")}
    namen.update({k: t[f"datei.{k}"] + ".docx" for k in ("protokoll", "absatz", "tatsachen", "stelle",
                                                        "datensatz", "interview", "ethik", "repos")})
    z = [f"# {t['l.titel']}", "", t["l.text"], ""]
    z += _tabelle([t["datei"], t["l.wofuer"]], [[f"`{a}`", b] for a, b in _spalten(t["l.zeilen"].format(**namen))])
    z += [f"## {t['l.vorher']}", ""] + _punkte(t["l.vorher.punkte"])
    return "\n".join(z + _fuss(f, t))


#: (Ordner-Schlüssel | None, Datei-Schlüssel, Erzeuger)
PLAN = ((None, "liesmich", liesmich), ("methoden", "protokoll", protokoll), ("methoden", "absatz", absatz),
        ("datenschutz", "tatsachen", tatsachen), ("datenschutz", "stelle", stelle),
        ("ablage", "datensatz", datensatz), ("ablage", "interview", interview),
        ("ablage", "ethik", ethik), ("ablage", "repos", repos))


def dokumente(eid: str, sprache: str) -> list[tuple[str, str]]:
    """[(Pfad im Paket ohne Endung, Markdown)] — die Quelle der Word-Dateien."""
    t, f = _texte(sprache), fakten(eid)
    return [("/".join(filter(None, [t[f"ordner.{ordner}"] if ordner else None, t[f"datei.{datei}"]])),
             bau(f, t)) for ordner, datei, bau in PLAN]


# ---------- Zitierdatei ----------

def zitate_bib() -> str:
    """BibLaTeX für Zotero (Datei › Importieren): die App als Eintragsart
    «Software», dazu Programme, Modelle und die Arbeiten, die deren
    Modellkarten zu zitieren bitten."""
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

@online{{radford2022whisper,
  title      = {{Robust Speech Recognition via Large-Scale Weak Supervision}},
  author     = {{Radford, Alec and Kim, Jong Wook and Xu, Tao and Brockman, Greg and McLeavey, Christine and Sutskever, Ilya}},
  date       = {{2022}},
  eprint     = {{2212.04356}},
  eprinttype = {{arXiv}},
  url        = {{https://arxiv.org/abs/2212.04356}}
}}

@software{{argmaxoss,
  title   = {{Argmax OSS: WhisperKit, SpeakerKit}},
  author  = {{{{Argmax, Inc.}}}},
  version = {{{SPEAKERKIT.split()[-1]}}},
  license = {{MIT}},
  url     = {{https://github.com/argmaxinc/argmax-oss-swift}}
}}

@online{{pyannotecommunity1,
  title  = {{speaker-diarization-community-1}},
  author = {{{{pyannote}}}},
  date   = {{2025}},
  note   = {{Modellkarte, CC BY 4.0; von Argmax nach Core ML umgewandelt}},
  url    = {{https://huggingface.co/pyannote/speaker-diarization-community-1}}
}}

@inproceedings{{plaquet2023powerset,
  title     = {{Powerset multi-class cross entropy loss for neural speaker diarization}},
  author    = {{Plaquet, Alexis and Bredin, Hervé}},
  booktitle = {{Proc. Interspeech 2023}},
  pages     = {{3222--3226}},
  date      = {{2023}},
  doi       = {{10.21437/Interspeech.2023-205}}
}}

@software{{silerovad,
  title   = {{Silero VAD}},
  author  = {{{{Silero Team}}}},
  version = {{{SILERO}}},
  license = {{MIT}},
  url     = {{https://github.com/snakers4/silero-vad}}
}}
"""


# ---------- Ausgabe ----------

def paket(eid: str, sprache: str) -> tuple[bytes, str]:
    """Das Zip (nur .docx und die .bib) und sein Dateiname."""
    sprache = sprache if sprache in SPRACHEN else "de"
    t = _texte(sprache)
    stamm = bibliothek._slug(bibliothek.lese(eid)["name"]) or eid
    wurzel = f"{stamm}-{t['paket.ordner']}"
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for pfad, md in dokumente(eid, sprache):
            zf.writestr(f"{wurzel}/{pfad}.docx", docx.aus_markdown(md, titel=md.splitlines()[0].lstrip("# ")))
        zf.writestr(f"{wurzel}/{t['ordner.zitieren']}/researchtranscript.bib", zitate_bib())
    return puffer.getvalue(), f"{wurzel}.zip"


def erzeuge(art: str, ids: list[str], sprache: str, format: str = "zip") -> tuple[bytes, str]:
    """API-Eingang: «paket» (genau ein Transkript) oder «zitate»."""
    if art == "zitate":
        return zitate_bib().encode("utf-8"), "researchtranscript.bib"
    if art != "paket":
        raise ValueError(f"Unbekanntes Dokument: {art}")
    if len(ids) != 1:
        raise ValueError("Das Dokumentationspaket gilt für genau ein Transkript")
    return paket(ids[0], sprache)
