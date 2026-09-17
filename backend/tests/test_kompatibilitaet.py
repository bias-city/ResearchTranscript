"""Was nach zwei Umbenennungen gleich bleiben MUSS.

LocalTranscript (bis 2.5.0) → TurnScript (3.0.0) → ResearchTranscript
(ab 0.4.0). Einstellungen werden bewusst nicht übernommen; Daten aus
früheren Fassungen bleiben aber lesbar, und Kennungen bleiben stabil.
"""
from __future__ import annotations

import uuid

from researchtranscript import config, qdpx
from researchtranscript.format2 import EIGENE_TOOLS, TOOL, _ist_unser_run


def test_dossiers_der_vorgaenger_gelten_als_eigene():
    assert TOOL == "researchtranscript"
    assert {"turnscript", "localtranscript"} < EIGENE_TOOLS
    for alt in ("localtranscript", "turnscript"):
        assert _ist_unser_run({"who": {"app": alt}})
        assert _ist_unser_run({"who": {"app": f"{alt}/2.5.0"}})
        assert _ist_unser_run({"tool": alt})
    assert not _ist_unser_run({"who": {"app": "enrich"}})


def test_qdpx_kennungen_bleiben_stabil():
    """Aus ihnen entstehen die GUIDs der Quellen in ATLAS.ti: ändern sie
    sich, sieht ATLAS.ti einen erneuten Export als neue Quelle."""
    assert qdpx._NS_QUELLE == uuid.uuid5(uuid.NAMESPACE_URL,
                                         "localtranscript:refi-source")
    assert qdpx._NS_CODE == uuid.uuid5(uuid.NAMESPACE_URL,
                                       "localtranscript:refi-code")
    assert qdpx._NS_SEL == uuid.uuid5(uuid.NAMESPACE_URL,
                                      "localtranscript:refi-selection")
    assert qdpx._NS_USER == uuid.uuid5(uuid.NAMESPACE_URL,
                                       "localtranscript:refi-user")


def test_frischer_start_ohne_erbe(tmp_path, monkeypatch):
    """Kein Zugriff auf die Ordner der Vorgänger, kein Kopieren."""
    monkeypatch.delenv("LT_CONFIG_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    for name in ("LocalTranscript", "TurnScript"):
        alt = tmp_path / "Library" / "Application Support" / name
        alt.mkdir(parents=True)
        (alt / "config.json").write_text('{"library_root": "/x/Bib"}')
        (tmp_path / "Documents" / name).mkdir(parents=True)
    cfg = config.read_config()
    assert cfg["library_root"] == ""          # First-Run, nichts geerbt
    assert config.default_library_root().name == "ResearchTranscript"
    neu = tmp_path / "Library" / "Application Support" / "ResearchTranscript"
    assert sorted(p.name for p in neu.iterdir()) == ["config.json"]
    for name in ("LocalTranscript", "TurnScript"):
        alt = tmp_path / "Library" / "Application Support" / name / "config.json"
        assert alt.read_text() == '{"library_root": "/x/Bib"}'   # unberührt


def test_identitaet_nennt_den_neuen_namen():
    assert config.identitaet()["app"].startswith("researchtranscript/0.5.0")
