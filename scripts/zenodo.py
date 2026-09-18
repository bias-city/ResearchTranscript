#!/usr/bin/env python3
"""Zenodo: Software-DOI für ein Release, über die REST-Schnittstelle.

  python3 scripts/zenodo.py entwurf v0.6.0            erster Eintrag (Entwurf)
  python3 scripts/zenodo.py entwurf v0.6.1 --von ID   neue Version eines
                                                      veröffentlichten Eintrags
  python3 scripts/zenodo.py zeige ID                  Stand eines Eintrags
  python3 scripts/zenodo.py veroeffentlichen ID       UNUMKEHRBAR: vergibt die DOI

Metadaten: .zenodo.json, dazu Version und Datum aus dem Tag. Hochgeladen wird
das Quellarchiv des Tags (git archive), nicht das DMG — das bleibt bei GitHub.
Das Token steht nur im Schlüsselbund:
  security add-generic-password -s zenodo.org -a researchtranscript -w
Mit --sandbox gegen sandbox.zenodo.org (Dienst «sandbox.zenodo.org»).
NICHT zusätzlich die GitHub-Anbindung von Zenodo einschalten: das gäbe einen
zweiten Eintrag mit eigener Konzept-DOI.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
KONTO = "researchtranscript"
COMMUNITY = "bias-city"  # zenodo.org/communities/bias-city


def token(dienst: str) -> str:
    r = subprocess.run(
        ["security", "find-generic-password", "-s", dienst, "-a", KONTO, "-w"],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit(f"Kein Token im Schlüsselbund (Dienst {dienst}, Konto {KONTO}).")
    return r.stdout.strip()


class Zenodo:
    def __init__(self, sandbox: bool):
        self.host = "sandbox.zenodo.org" if sandbox else "zenodo.org"
        self.api = f"https://{self.host}/api"
        self._kopf = {"Authorization": f"Bearer {token(self.host)}"}

    def ruf(self, methode: str, url: str, *, daten=None, roh: bytes | None = None,
            nativ: bool = False):
        if not url.startswith("http"):
            url = self.api + url
        kopf = dict(self._kopf)
        if nativ:  # sonst antwortet /records im alten Format, ohne «parent»
            kopf["Accept"] = "application/vnd.inveniordm.v1+json"
        koerper = None
        if roh is not None:
            koerper, kopf["Content-Type"] = roh, "application/octet-stream"
        elif daten is not None:
            koerper, kopf["Content-Type"] = json.dumps(daten).encode(), "application/json"
        anfrage = urllib.request.Request(url, data=koerper, method=methode, headers=kopf)
        try:
            with urllib.request.urlopen(anfrage, timeout=600) as antwort:
                text = antwort.read().decode()
        except urllib.error.HTTPError as e:
            sys.exit(f"{methode} {url}: HTTP {e.code}\n{e.read().decode()[:2000]}")
        return json.loads(text) if text else {}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=WURZEL, check=True,
                          capture_output=True, text=True).stdout.strip()


def metadaten(tag: str) -> dict:
    m = json.loads((WURZEL / ".zenodo.json").read_text(encoding="utf-8"))
    m["version"] = tag.lstrip("v")
    m["publication_date"] = git("log", "-1", "--format=%cs", tag)
    return m


def archiv(tag: str) -> tuple[str, bytes]:
    name = f"ResearchTranscript-{tag.lstrip('v')}"
    roh = subprocess.run(
        ["git", "archive", "--format=zip", f"--prefix={name}/", tag],
        cwd=WURZEL, check=True, capture_output=True,
    ).stdout
    return f"{name}.zip", roh


def zeige(e: dict) -> None:
    m = e.get("metadata", {})
    print(f"ID            {e.get('id')}")
    print(f"Zustand       {e.get('state')}  veröffentlicht: {e.get('submitted')}")
    print(f"Titel         {m.get('title')}  {m.get('version', '')}")
    print(f"Datum         {m.get('publication_date')}")
    print(f"DOI (Version) {e.get('doi') or m.get('prereserve_doi', {}).get('doi')}")
    if e.get("conceptdoi"):
        print(f"DOI (alle)    {e['conceptdoi']}")
    for f in e.get("files", []):
        print(f"Datei         {f.get('filename')}  {f.get('filesize')} Bytes  {f.get('checksum')}")
    print(f"Ansehen       {e.get('links', {}).get('html')}")


def entwurf(z: Zenodo, tag: str, von: int | None) -> None:
    if von is None:
        e = z.ruf("POST", "/deposit/depositions", daten={})
    else:
        alt = z.ruf("POST", f"/deposit/depositions/{von}/actions/newversion")
        e = z.ruf("GET", alt["links"]["latest_draft"])
        for f in e.get("files", []):  # die neue Version erbt die alten Dateien
            z.ruf("DELETE", f"/deposit/depositions/{e['id']}/files/{f['id']}")
    name, roh = archiv(tag)
    z.ruf("PUT", f"{e['links']['bucket']}/{name}", roh=roh)
    z.ruf("PUT", f"/deposit/depositions/{e['id']}", daten={"metadata": metadaten(tag)})
    if von is None:  # spätere Versionen erben die Community vom Eintrag
        c = z.ruf("GET", f"/communities/{COMMUNITY}")
        z.ruf("PUT", f"/records/{e['id']}/draft/review",
              daten={"receiver": {"community": c["id"]}, "type": "community-submission"})
        print(f"Community     {COMMUNITY} (Einreichung vorbereitet)")
    zeige(z.ruf("GET", f"/deposit/depositions/{e['id']}"))
    print("\nEntwurf — nichts ist veröffentlicht.")


def veroeffentliche(z: Zenodo, eid: int) -> None:
    """Mit Community-Einreichung: einreichen und als Eigentümer annehmen —
    das Annehmen veröffentlicht. Ohne Einreichung: direkt veröffentlichen."""
    entwurf_ = z.ruf("GET", f"/records/{eid}/draft", nativ=True)
    pruefung = (entwurf_.get("parent") or {}).get("review")
    if not pruefung:
        zeige(z.ruf("POST", f"/deposit/depositions/{eid}/actions/publish"))
        return
    r = z.ruf("POST", f"/records/{eid}/draft/actions/submit-review",
              daten={"payload": {"content": "Release", "format": "html"}})
    if r.get("status") != "accepted":
        r = z.ruf("POST", f"/requests/{r['id']}/actions/accept", daten={})
    print(f"Einreichung   {r.get('status')}")
    zeige(z.ruf("GET", f"/deposit/depositions/{eid}"))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--sandbox", action="store_true")
    sub = p.add_subparsers(dest="befehl", required=True)
    a = sub.add_parser("entwurf")
    a.add_argument("tag")
    a.add_argument("--von", type=int)
    sub.add_parser("zeige").add_argument("id", type=int)
    v = sub.add_parser("veroeffentlichen")
    v.add_argument("id", type=int)
    v.add_argument("--ja", action="store_true", help="ohne Rückfrage")
    arg = p.parse_args()
    z = Zenodo(arg.sandbox)
    if arg.befehl == "entwurf":
        entwurf(z, arg.tag, arg.von)
    elif arg.befehl == "zeige":
        zeige(z.ruf("GET", f"/deposit/depositions/{arg.id}"))
    else:
        if not arg.ja and input("Veröffentlichen ist unumkehrbar. «ja» tippen: ") != "ja":
            sys.exit("Abgebrochen.")
        veroeffentliche(z, arg.id)


if __name__ == "__main__":
    main()
