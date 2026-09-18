"""Begleitdokumente: Protokoll, Methodenbaustein, Verfahrensbaustein,
Repositoriums-Datenblatt, Zitierdatei, Paket (BACKLOG 16)."""
import io
import re
import zipfile

import pytest

from researchtranscript import bibliothek, dokumente


def _eintrag(name="Interview_01", zotero=None):
    seg = [{"id": "a", "start": 0, "end": 5, "sprecher": "p1", "text": "guten tag herr meier wie gehts"},
           {"id": "b", "start": 5, "end": 9, "sprecher": "p2", "text": "danke gut"},
           {"id": "c", "start": 9, "end": 15, "sprecher": "p1", "text": "das freut mich sehr"}]
    d = bibliothek.anlegen(name, seg, [{"id": "p1", "name": "Sprecher 1"}, {"id": "p2", "name": "Sprecher 2"}],
                           {"datei": "aufnahme.m4a", "erzeugt": "transcription", "model": "large-v3-turbo",
                            "language": "de", "diarize": True, "sprecherzahl": "2-2", "app": "0.6.0",
                            "modell_quelle": "bundled", "vad": True, "trennung": 0.5},
                           by={"tool": "whisper.cpp"}, zotero=zotero)
    d["segmente"][0]["text"] = "Guten Tag, Herr B3, wie geht es?"
    d["segmente"][2]["sprecher"] = "p2"
    d["sprecher"][0]["name"] = "I"
    bibliothek.schreibe(d["id"], d)
    return d["id"]


@pytest.mark.parametrize("sprache", ["de", "en", "fr", "it"])
def test_alle_dokumente_in_allen_sprachen(client, sprache):
    eid = _eintrag()
    for art, ids in (("protokoll", [eid]), ("methoden", [eid]), ("verfahren", []), ("repositorium", [eid])):
        md = dokumente.erzeuge(art, ids, sprache, "md")[0].decode()
        assert md.startswith("# ")
        assert not re.search(r"\{[a-z_]+\}", md), f"{art}/{sprache}: Platzhalter nicht gefüllt"
        assert "[ … ]" in md or art == "protokoll"
        dokumente.erzeuge(art, ids, sprache, "docx")


def test_protokoll_nennt_mass_und_keine_sprechernamen(client):
    eid = _eintrag()
    md = dokumente.protokoll(eid, "de")
    assert "Korrekturrate Wortebene, normalisiert" in md and "large-v3-turbo" in md
    assert "Eingriffsmass, kein Genauigkeitsmass" in md
    assert "Fehlerrate" not in md.replace("Wortfehlerrate", "") and "Genauigkeit " not in md
    assert re.search(r"`ausgang\.json` \| .* \| `[0-9a-f]{64}`", md)
    assert "Herr B3" not in md                    # kein Wortlaut im Protokoll


def test_methodenbaustein_aggregiert(client):
    ids = [_eintrag("Interview_01"), _eintrag("Interview_02")]
    md = dokumente.methoden(ids, "de")
    assert "| Transkripte | 2 |" in md and "00:00:30" in md        # Gesamtdauer 2 × 15 s
    assert "Median" in md and "Radford et al., 2022" in md and "[ wem ]" in md


def test_datenblatt_schlaegt_nie_befragte_vor(client):
    zot = {"item_key": "K", "title": "Gespräch über Wohnen", "date": "2026-05-02", "year": "2026",
           "citekey": "meier2026", "abstract": "Interview zu Genossenschaften.",
           "creators": [{"first": "Hans", "last": "Meier", "role": "interviewee"},
                        {"first": "Nora", "last": "Keller", "role": "interviewer"}]}
    md = dokumente.repositorium([_eintrag(zotero=zot)], "de")
    assert "Keller, Nora (interviewer)" in md and "Meier" not in md
    assert "bewusst nicht aufgeführt" in md and "Gespräch über Wohnen — Vorschlag, prüfen" in md


def test_zitierdatei_und_paket(client):
    bib = dokumente.zitate_bib()
    assert "@software{researchtranscript," in bib and "Pohl, Ben" in bib and "AGPL-3.0-or-later" in bib
    assert bib.count("{") == bib.count("}")
    eid = _eintrag()
    inhalt, name = dokumente.erzeuge("paket", [eid], "de", "zip")
    assert name.endswith(".zip")
    with zipfile.ZipFile(io.BytesIO(inhalt)) as z:
        namen = z.namelist()
    assert any(n.endswith("researchtranscript.bib") for n in namen)
    assert sum(n.endswith(".docx") for n in namen) == sum(n.endswith(".md") for n in namen) - 1 == 4


def test_api_schreibt_nur_passende_endung(client, tmp_path):
    eid = _eintrag()
    r = client.post("/api/dokument", json={"art": "methoden", "format": "md", "ids": [eid],
                                           "path": str(tmp_path / "x.txt")})
    assert r.status_code == 409
    r = client.post("/api/dokument", json={"art": "paket", "ids": [eid], "path": str(tmp_path / "p.zip")})
    assert r.status_code == 200 and (tmp_path / "p.zip").stat().st_size > 1000
    r = client.get(f"/api/transcripts/{eid}/export/protokoll-md")
    assert r.status_code == 200 and r.content.decode().startswith("# Transkriptionsprotokoll")


def test_methodenbaustein_fuer_ein_transkript_ohne_median(client):
    md = dokumente.methoden([_eintrag()], "de")
    assert "Median" not in md and "Die Aufnahme (Dauer 00:00:15)" in md
    assert "Je Transkript" not in md and "| Korrekturrate Wortebene, normalisiert | 23,1 % |" in md
