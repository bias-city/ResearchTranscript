"""Dokumentationspaket je Transkript: neun kurze Word-Dokumente + .bib (BACKLOG 16)."""
import io
import json
import re
import zipfile
from xml.etree import ElementTree as ET

import pytest

from researchtranscript import bibliothek, dokumente


def _eintrag(name="Interview_01", zotero=None, **quelle):
    seg = [{"id": "a", "start": 0, "end": 5, "sprecher": "p1", "text": "guten tag herr meier wie gehts"},
           {"id": "b", "start": 5, "end": 9, "sprecher": "p2", "text": "danke gut"},
           {"id": "c", "start": 9, "end": 15, "sprecher": "p1", "text": "das freut mich sehr"}]
    q = {"datei": "aufnahme.m4a", "erzeugt": "transcription", "model": "large-v3-turbo",
         "language": "de", "diarize": True, "sprecherzahl": "2-2", "app": "0.6.0",
         "modell_quelle": "bundled", "whisper_cpp": "1.8.2", "vad": False, "trennung": 0.5}
    q.update(quelle)
    d = bibliothek.anlegen(name, seg, [{"id": "p1", "name": "Sprecher 1"}, {"id": "p2", "name": "Sprecher 2"}],
                           q, by={"tool": "whisper.cpp"}, zotero=zotero)
    d["segmente"][0]["text"] = "Guten Tag, Herr B3, wie geht es?"
    d["segmente"][2]["sprecher"] = "p2"
    d["sprecher"][0]["name"] = "I"
    bibliothek.schreibe(d["id"], d)
    return d["id"]


def _alt(eid):
    """Wie ein Eintrag aus LocalTranscript 2.5.0: kein Ausgangsstand, keine Lauf-Fakten."""
    ordner = bibliothek.eintrag_pfad(eid)
    (ordner / bibliothek.AUSGANG).unlink()
    for fp in (ordner / "history").glob("*.json"):
        fp.unlink()
    tj = ordner / "transkript.json"
    d = json.loads(tj.read_text())
    for k in ("app", "modell_quelle", "whisper_cpp", "vad", "trennung"):
        d["quelle"].pop(k, None)
    for r in d["journal"]:
        if r["origin"] == "machine":
            r["who"]["app"] = "localtranscript/2.5.0"
    tj.write_text(json.dumps(d))


@pytest.mark.parametrize("sprache", ["de", "en", "fr", "it"])
def test_alle_dokumente_in_allen_sprachen(client, sprache):
    eid = _eintrag()
    docs = dokumente.dokumente(eid, sprache)
    assert len(docs) == 9
    for pfad, md in docs:
        assert md.startswith("# "), pfad
        assert not re.search(r"\{[a-z_]+\}", md), f"{pfad}/{sprache}: Platzhalter nicht gefüllt"
        assert len(md.split()) < (660 if sprache == "de" else 760), f"{pfad}: zu lang ({len(md.split())} Wörter)"


def test_protokoll_neuer_lauf(client):
    md = dict(dokumente.dokumente(_eintrag(), "de"))["1-methoden/transkriptionsprotokoll"]
    assert "ResearchTranscript 0.6.0" in md and "whisper.cpp 1.8.2" in md
    assert "die Sprechertrennung schneidet die Blöcke" in md            # VAD nicht behauptet
    assert "Hilfsprogramm aus dem App-Paket" in md and "im Prozess" not in md
    assert "Korrekturrate, normalisiert | 23,1 %" in md and "Eingriffsmass, kein Genauigkeitsmass" in md
    assert "Wortlaut geändert | 1 von 3 (33,3 %)" in md and "Sprecher neu zugeordnet | 1 von 3" in md
    assert "Installation ins-" in md                                    # wer bearbeitet hat, laut Journal
    assert "Herr B3" not in md and "meier2026" not in md


def test_protokoll_alter_lauf_behauptet_nichts(client):
    eid = _eintrag()
    _alt(eid)
    docs = dict(dokumente.dokumente(eid, "de"))
    p, a = docs["1-methoden/transkriptionsprotokoll"], docs["1-methoden/methodenabsatz"]
    assert "LocalTranscript 2.5.0 (Vorgängername" in p and "ResearchTranscript 2.5.0" not in p
    assert "Programmversion beim Lauf nicht aufgezeichnet" in p and "1.8.2" not in p.split("## Software")[0]
    assert "Sprachaktivitätserkennung" not in p and "| Ort der Verarbeitung | lokal auf dem Mac |" in p
    assert "nicht berechenbar" in p and "`ausgang.json` ist" not in p
    # der Absatz bleibt nie leer: ohne Wortrate das Journal-Mass
    assert "LocalTranscript 2.5.0 (heute ResearchTranscript)" in a
    assert "Laut Journal wurde in mindestens 33,3 %" in a and " – " not in a.split("## Noch")[0]


def test_absatz_mit_wortrate_kurz_und_lang(client):
    a = dict(dokumente.dokumente(_eintrag(), "de"))["1-methoden/methodenabsatz"]
    assert "Die Korrekturrate auf Wortebene betrug 23,1 %" in a and "neu zugeordnet wurden" in a
    assert "[ wem ]" in a and "AGPL" not in a and "Pohl, B. (2026)" in a
    kurz = a.split("## Kurzfassung")[1].split("##")[0]
    assert len(kurz.split()) < 60


def test_datenblatt_nie_titel_oder_befragte_aus_zotero(client):
    zot = {"item_key": "K", "title": "Hanna", "date": "2026-05-02", "year": "2026",
           "citekey": "meier2026", "abstract": "Gespräch mit Hans Meier.",
           "creators": [{"first": "Hans", "last": "Meier", "role": "interviewee"},
                        {"first": "Nora", "last": "Keller", "role": "interviewer"}]}
    alles = "\n".join(md for _, md in dokumente.dokumente(_eintrag(zotero=zot), "de"))
    assert "Keller, Nora (interviewer) — Vorschlag aus Zotero, prüfen" in alles
    assert "Meier" not in alles and "Hanna" not in alles and "meier2026" not in alles
    assert "bewusst nicht aufgeführt" in alles and "Gilt bei Zenodo je Eintrag" in alles


def test_tatsachen_stimmen_mit_der_app(client):
    t = dict(dokumente.dokumente(_eintrag(), "de"))["2-datenschutz/app-tatsachen"]
    assert "Netzberechtigung von macOS ist gesetzt" in t and "generative" not in t
    assert "kann Wörter setzen, die nicht gesagt wurden" in t
    assert "enrich-Dossier (`.enrich`): Text, Tonaufnahme als MP3" in t and "Keine Memos." in t
    assert "ohne Sprechertrennung mit Silero VAD" in t


def test_paket_nur_docx_in_unterordnern(client):
    eid = _eintrag("Interview 01")
    inhalt, name = dokumente.erzeuge("paket", [eid], "de")
    assert name == "Interview-01-dokumentation.zip"
    with zipfile.ZipFile(io.BytesIO(inhalt)) as z:
        namen = z.namelist()
        for n in namen:
            if n.endswith(".docx"):
                ET.fromstring(z.read(n).__class__(zipfile.ZipFile(io.BytesIO(z.read(n))).read("word/document.xml")))
    assert not any(n.endswith(".md") for n in namen)
    assert sum(n.endswith(".docx") for n in namen) == 9
    ordner = {n.split("/")[1] for n in namen if n.count("/") == 2}
    assert ordner == {"1-methoden", "2-datenschutz", "3-datenablage", "zitieren"}
    bib = dokumente.zitate_bib()
    assert "@software{researchtranscript," in bib and bib.count("{") == bib.count("}")
    with pytest.raises(ValueError):
        dokumente.erzeuge("paket", [eid, eid], "de")


def test_api_schreibt_nur_passende_endung(client, tmp_path):
    eid = _eintrag()
    r = client.post("/api/dokument", json={"art": "paket", "ids": [eid], "path": str(tmp_path / "x.txt")})
    assert r.status_code == 409
    r = client.post("/api/dokument", json={"art": "methoden", "ids": [eid], "path": str(tmp_path / "x.md")})
    assert r.status_code == 409
    r = client.post("/api/dokument", json={"art": "paket", "ids": [eid], "path": str(tmp_path / "p.zip")})
    assert r.status_code == 200 and (tmp_path / "p.zip").stat().st_size > 1000
