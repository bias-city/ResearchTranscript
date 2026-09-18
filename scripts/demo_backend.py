"""Demo-Backend für die Screenshot-Pipeline (scripts/appstore-screenshots.mjs
--site): das echte Backend, aber mit ERFUNDENEN Zotero-Einträgen statt einer
Zotero-Datenbank — nie echte Bibliotheksdaten in Bildern. Start:

    uv run uvicorn demo_backend:app --app-dir ../scripts --port 5631
"""
import os
from pathlib import Path

from researchtranscript import zotero
from researchtranscript.main import app  # noqa: F401  (uvicorn lädt `app`)

ITEMS = [
    {"item_key": "ABCD1234", "item_type": "interview", "citekey": "whitfield2026",
     "title": "Interview on housing cooperatives, Basel", "date": "2026-03-04", "year": "2026",
     "publication": None, "doi": None,
     "abstract": "Conversation about housing cooperatives and participation.",
     "select_link": "zotero://select/library/items/ABCD1234", "library": "My Library",
     "creators": [{"first": "Nora", "last": "Whitfield", "role": "interviewer"},
                  {"first": "Julian", "last": "Marsh", "role": "interviewee"}]},
    {"item_key": "EFGH5678", "item_type": "interview", "citekey": "whitfield2026a",
     "title": "Group discussion, neighbourhood workshop", "date": "2026-04-12", "year": "2026",
     "select_link": "zotero://select/library/items/EFGH5678", "library": "My Library",
     "creators": [{"first": "Nora", "last": "Whitfield", "role": "interviewer"}]},
    {"item_key": "ZZZZ9999", "item_type": "book", "citekey": "marsh2019",
     "title": "City and Cooperative", "date": "2019", "year": "2019",
     "select_link": "zotero://select/library/items/ZZZZ9999", "library": "My Library",
     "creators": [{"first": "Julian", "last": "Marsh", "role": "author"}]},
]

zotero.ez.items_with_pdfs = lambda *a, **k: [dict(i) for i in ITEMS]
zotero.ez.find_zotero_dir = lambda cfg=None: Path(os.environ.get("DEMO_ZOTERO_DIR", "/Users/nora/Zotero"))
