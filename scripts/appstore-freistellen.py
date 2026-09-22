#!/usr/bin/env python3
"""Fensteraufnahme freistellen: Schatten weg, Ecken gefüllt, exaktes Rechteck.

macOS nimmt mit Umschalt-Befehl-Vier + Leertaste das Fenster MIT Schatten auf.
Der Schatten liegt im Alphakanal; auf dem hellen Grund der Store-Montage würde
er als schmutziger Rand erscheinen, und die abgerundeten Ecken des Fensters
blieben als durchsichtige Zipfel stehen.

Dieses Skript schneidet deshalb auf den deckenden Fensterbereich zu und füllt
die vier gerundeten Ecken mit der Farbe des jeweils nächsten Fensterpixels in
derselben Zeile. Ergebnis: ein vollständig deckendes Rechteck. Die Rundung
setzt die Montage selbst (`border-radius`), ebenso den Schatten — so sehen alle
Motive gleich aus, egal womit sie aufgenommen wurden.

    python3 scripts/appstore-freistellen.py <eingabe.png> <ziel.png>
"""
import sys
from pathlib import Path

from PIL import Image

DECKEND = 250  # ab hier gilt ein Pixel als Fenster, darunter als Schatten


def freistellen(quelle: Path, ziel: Path) -> None:
    bild = Image.open(quelle).convert("RGBA")
    alpha = bild.getchannel("A")
    kasten = alpha.point(lambda a: 255 if a >= DECKEND else 0).getbbox()
    if kasten is None:
        raise SystemExit(f"ABBRUCH: kein deckender Bereich in {quelle}")
    bild = bild.crop(kasten)
    breite, hoehe = bild.size
    pixel = bild.load()

    # Ecken auffüllen: je Zeile von aussen nach innen bis zum ersten deckenden
    # Pixel, dessen Farbe dann nach aussen fortgeschrieben wird.
    for y in range(hoehe):
        x = 0
        while x < breite and pixel[x, y][3] < DECKEND:
            x += 1
        if x == breite:  # ganze Zeile durchsichtig – kommt bei sauberem Zuschnitt nicht vor
            continue
        farbe = pixel[x, y][:3] + (255,)
        for i in range(x):
            pixel[i, y] = farbe
        x = breite - 1
        while x >= 0 and pixel[x, y][3] < DECKEND:
            x -= 1
        farbe = pixel[x, y][:3] + (255,)
        for i in range(x + 1, breite):
            pixel[i, y] = farbe

    ziel.parent.mkdir(parents=True, exist_ok=True)
    bild.convert("RGB").save(ziel)
    print(f"✓ {ziel.name}: {breite}×{hoehe} (aus {quelle.name})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    freistellen(Path(sys.argv[1]), Path(sys.argv[2]))
