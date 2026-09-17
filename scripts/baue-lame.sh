#!/bin/sh
# libmp3lame für das Bundle bauen (Plan §5, Ton: AVFoundation + LAME).
#
# LAME ist LGPL-2.0+: dynamisch gelinkt (Contents/Frameworks), damit
# Nutzer die Bibliothek austauschen können; der Quell-Tarball wird neben
# die Bibliothek gelegt und zu jedem Release auf bias.city gehostet.
# Gebaut OHNE Decoder (kein mpg123 — die App dekodiert mit AVFoundation)
# und ohne Frontend: eine einzige dylib, die nur an libSystem hängt.
#
# Aufruf: scripts/baue-lame.sh [tarball]   (ohne Argument: Download)
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
ZIEL="$ROOT/frontend/src-tauri/resources/frameworks"
VERSION=4.0
SHA=3df5124d5ad3a98312ffd7ba6a9b36230e4f8a3e66d3ce0f425e336c32d216eb
URL="https://downloads.sourceforge.net/project/lame/lame/$VERSION/lame-$VERSION.tar.gz"
BAU=$(mktemp -d /tmp/lame-bau.XXXXXX)
TAR="${1:-$BAU/lame-$VERSION.tar.gz}"
[ -f "$TAR" ] || curl -sSL -o "$TAR" "$URL"
echo "$SHA  $TAR" | shasum -a 256 -c - >/dev/null || { echo "ABBRUCH: Prüfsumme des Tarballs stimmt nicht"; exit 1; }
tar xf "$TAR" -C "$BAU"
cd "$BAU/lame-$VERSION"
./configure --prefix="$BAU/out" --enable-shared --disable-static \
  --disable-decoder --disable-frontend --disable-gtktest >"$BAU/configure.log" 2>&1
make -j8 >"$BAU/make.log" 2>&1 && make install >"$BAU/install.log" 2>&1
mkdir -p "$ZIEL"
cp "$BAU/out/lib/libmp3lame.0.dylib" "$ZIEL/libmp3lame.dylib"
cp "$TAR" "$ZIEL/lame-$VERSION.tar.gz"
# Install-Name auf @rpath — die Hülle trägt @executable_path/../Frameworks
install_name_tool -id @rpath/libmp3lame.dylib "$ZIEL/libmp3lame.dylib"
otool -L "$ZIEL/libmp3lame.dylib" | sed -n 2,4p
echo "fertig: $ZIEL/libmp3lame.dylib ($(stat -f %z "$ZIEL/libmp3lame.dylib") Bytes), Quelle daneben"
rm -rf "$BAU"
