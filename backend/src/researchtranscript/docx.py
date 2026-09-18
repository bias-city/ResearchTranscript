"""Markdown-Teilmenge → .docx, ohne Fremdbibliothek (BACKLOG 16).

Die App liefert Transkripte und Begleitdokumente als Markdown; wer Word
braucht, bekommt dasselbe Dokument als .docx. python-docx (mit lxml) käme
dafür ins Bundle — für Überschriften, Absätze, Listen, Zitate und Tabellen
reicht eine Seite XML. Ein .docx ist ein Zip mit vier Pflichtdateien.

Verstanden wird, was `dokumente.py` und `ausgabe.build_md` schreiben:
  # / ## / ###     Überschriften
  - …              Aufzählung        1. …   nummerierte Liste
  > …              Zitat/Hinweis (eingerückt, kursiv)
  | a | b |        Tabelle (erste Zeile = Kopf, die |---|-Zeile entfällt)
  ---              Trennlinie → Leerabsatz
  **fett**  *kursiv*  `code`  <https://…>  [Text](https://…)
Alles andere ist Fliesstext; aufeinanderfolgende Zeilen bilden EINEN Absatz.
"""
from __future__ import annotations

import io
import re
import zipfile
from xml.sax.saxutils import escape

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|`[^`]+`|<https?://[^>\s]+>|\[[^\]]+\]\(https?://[^)\s]+\))")


#: Maskierte Zeichen (\\* \\_ \\# …) wandern als Platzhalter durch die
#: Auszeichnungs-Erkennung und kommen in _lauf() wörtlich zurück
_MASKE = re.compile(r"\\([\\*_`<>|#+.\-])")
_PUA = 0xE000


def _maskiere(text: str) -> str:
    return _MASKE.sub(lambda m: chr(_PUA + ord(m.group(1))), text)


def _demaskiere(text: str) -> str:
    return "".join(chr(ord(z) - _PUA) if _PUA < ord(z) < _PUA + 128 else z for z in text)


def _lauf(text: str, *, fett: bool = False, kursiv: bool = False, code: bool = False) -> str:
    if not text:
        return ""
    text = _demaskiere(text)
    eig = ""
    if fett:
        eig += "<w:b/>"
    if kursiv:
        eig += "<w:i/>"
    if code:
        eig += '<w:rFonts w:ascii="Menlo" w:hAnsi="Menlo" w:cs="Menlo"/><w:sz w:val="19"/>'
    rpr = f"<w:rPr>{eig}</w:rPr>" if eig else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def _inline(text: str, *, fett: bool = False, kursiv: bool = False) -> str:
    aus = []
    for teil in _INLINE.split(_maskiere(text)):
        if not teil:
            continue
        if teil.startswith("**") and teil.endswith("**") and len(teil) > 4:
            aus.append(_lauf(teil[2:-2], fett=True, kursiv=kursiv))
        elif teil.startswith("`") and teil.endswith("`") and len(teil) > 2:
            aus.append(_lauf(teil[1:-1], fett=fett, kursiv=kursiv, code=True))
        elif teil.startswith("<http") and teil.endswith(">"):
            aus.append(_lauf(teil[1:-1], fett=fett, kursiv=kursiv))
        elif teil.startswith("[") and "](" in teil and teil.endswith(")"):
            wort, url = teil[1:-1].split("](", 1)
            aus.append(_lauf(f"{wort} ({url})", fett=fett, kursiv=kursiv))
        elif teil.startswith("*") and teil.endswith("*") and len(teil) > 2:
            aus.append(_lauf(teil[1:-1], fett=fett, kursiv=True))
        else:
            aus.append(_lauf(teil, fett=fett, kursiv=kursiv))
    return "".join(aus)


def _absatz(inhalt: str, stil: str | None = None, einzug: int = 0, haengend: int = 0) -> str:
    ppr = ""
    if stil:
        ppr += f'<w:pStyle w:val="{stil}"/>'
    if einzug:
        ppr += f'<w:ind w:left="{einzug}"' + (f' w:hanging="{haengend}"' if haengend else "") + "/>"
    return f"<w:p>{f'<w:pPr>{ppr}</w:pPr>' if ppr else ''}{inhalt}</w:p>"


def _tabelle(zeilen: list[list[str]]) -> str:
    spalten = max(len(z) for z in zeilen)
    rand = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
                   for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    aus = [(f'<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>{rand}</w:tblBorders>'
            '<w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar>'
            "</w:tblPr>")]
    for k, z in enumerate(zeilen):
        aus.append("<w:tr>")
        for c in range(spalten):
            zelle = z[c] if c < len(z) else ""
            aus.append("<w:tc><w:tcPr><w:tcW w:w=\"0\" w:type=\"auto\"/></w:tcPr>"
                       + _absatz(_inline(zelle, fett=(k == 0)), "TableText") + "</w:tc>")
        aus.append("</w:tr>")
    aus.append("</w:tbl>")
    return "".join(aus) + _absatz("")            # Word verlangt einen Absatz nach der Tabelle


def _zellen(zeile: str) -> list[str]:
    roh = zeile.strip().strip("|")
    return [z.strip().replace("\\|", "|") for z in re.split(r"(?<!\\)\|", roh)]


def _koerper(md: str) -> str:
    aus: list[str] = []
    absatz: list[str] = []
    tabelle: list[list[str]] = []

    def schliesse() -> None:
        if absatz:
            aus.append(_absatz(_inline(" ".join(absatz))))
            absatz.clear()
        if tabelle:
            aus.append(_tabelle(list(tabelle)))
            tabelle.clear()

    for zeile in md.splitlines():
        z = zeile.rstrip()
        if z.lstrip().startswith("|") and z.rstrip().endswith("|"):
            if absatz:
                schliesse()
            if not re.fullmatch(r"\s*\|[\s:|-]+\|\s*", z):
                tabelle.append(_zellen(z))
            continue
        if tabelle:
            schliesse()
        if not z.strip():
            schliesse()
        elif z.strip() == "---":
            schliesse()
            aus.append(_absatz(""))
        elif m := re.match(r"(#{1,3})\s+(.*)", z):
            schliesse()
            aus.append(_absatz(_inline(m.group(2)), f"Heading{len(m.group(1))}"))
        elif m := re.match(r"\s*[-*]\s+(.*)", z):
            schliesse()
            aus.append(_absatz(_lauf("•\t") + _inline(m.group(1)), None, 360, 360))
        elif m := re.match(r"\s*(\d+)[.)]\s+(.*)", z):
            schliesse()
            aus.append(_absatz(_lauf(f"{m.group(1)}.\t") + _inline(m.group(2)), None, 360, 360))
        elif z.startswith(">"):
            schliesse()
            aus.append(_absatz(_inline(z.lstrip("> ").strip(), kursiv=True), "Quote"))
        else:
            absatz.append(z.strip())
    schliesse()
    return "".join(aus)


_TYPEN = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
          '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
          "</Types>")
_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
         '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
         "</Relationships>")
_DOKRELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            "</Relationships>")


def _stil(sid: str, name: str, *, basis: str | None = "Normal", groesse: int | None = None,
          fett: bool = False, kursiv: bool = False, vor: int = 0, nach: int = 120,
          einzug: int = 0, halten: bool = False, standard: bool = False) -> str:
    rpr = ("<w:b/>" if fett else "") + ("<w:i/>" if kursiv else "") + \
          (f'<w:sz w:val="{groesse}"/><w:szCs w:val="{groesse}"/>' if groesse else "")
    ppr = f'<w:spacing w:before="{vor}" w:after="{nach}"/>' + \
          (f'<w:ind w:left="{einzug}"/>' if einzug else "") + ("<w:keepNext/>" if halten else "")
    return (f'<w:style w:type="paragraph" w:styleId="{sid}"{" w:default=\"1\"" if standard else ""}>'
            f'<w:name w:val="{name}"/>' + (f'<w:basedOn w:val="{basis}"/>' if basis and not standard else "")
            + "<w:qFormat/>" + f"<w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>")


def _styles() -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:styles xmlns:w="{_W}"><w:docDefaults><w:rPrDefault><w:rPr>'
            '<w:rFonts w:ascii="Helvetica Neue" w:hAnsi="Helvetica Neue" w:cs="Arial" w:eastAsia="Arial"/>'
            '<w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="de-CH"/></w:rPr></w:rPrDefault>'
            '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="288" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
            "</w:docDefaults>"
            + _stil("Normal", "Normal", standard=True)
            + _stil("Heading1", "heading 1", groesse=32, fett=True, vor=240, nach=160, halten=True)
            + _stil("Heading2", "heading 2", groesse=26, fett=True, vor=280, nach=100, halten=True)
            + _stil("Heading3", "heading 3", groesse=22, fett=True, vor=200, nach=80, halten=True)
            + _stil("Quote", "Quote", kursiv=True, einzug=360, nach=160)
            + _stil("TableText", "Table Text", groesse=19, nach=40)
            + "</w:styles>")


def aus_markdown(md: str, *, titel: str = "", erstellt: str = "") -> bytes:
    """Das Dokument als .docx-Bytes. `erstellt` = ISO-Zeit für die
    Dateieigenschaften (leer = ohne — hält die Ausgabe reproduzierbar)."""
    dokument = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document xmlns:w="{_W}"><w:body>{_koerper(md)}'
                '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                '<w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417" w:header="708" w:footer="708" w:gutter="0"/>'
                "</w:sectPr></w:body></w:document>")
    zeit = (f'<dcterms:created xsi:type="dcterms:W3CDTF">{escape(erstellt)}</dcterms:created>'
            if erstellt else "")
    kern = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"<dc:title>{escape(titel)}</dc:title><dc:creator>ResearchTranscript</dc:creator>{zeit}"
            "</cp:coreProperties>")
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, inhalt in (("[Content_Types].xml", _TYPEN), ("_rels/.rels", _RELS),
                             ("docProps/core.xml", kern), ("word/document.xml", dokument),
                             ("word/styles.xml", _styles()),
                             ("word/_rels/document.xml.rels", _DOKRELS)):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, inhalt)
    return puffer.getvalue()
