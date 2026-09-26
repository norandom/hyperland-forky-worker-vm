#!/bin/bash
# Build hypr-rdp <version> with the hypr-rdp-clearcodec patches and install it
# to /usr/local/bin. Run as the desktop user (uses sudo only to install).
#   build.sh <version> <sha256> <stamp>
set -euo pipefail
ver=$1 sha=$2 stamp=$3
src=$(cd "$(dirname "$0")" && pwd)
work=$HOME/.cache/hypr-rdp-build

rm -rf "$work"; mkdir -p "$work"; cd "$work"
curl -fsSL -o hypr-rdp.tar.gz "https://github.com/MuNeNICK/hypr-rdp/archive/refs/tags/v$ver.tar.gz"
echo "$sha  hypr-rdp.tar.gz" | sha256sum -c --quiet
tar xzf hypr-rdp.tar.gz
cd "hypr-rdp-$ver"

patch -Np1 -i "$src/clearcodec.patch"   # egfx_codec = "clearcodec"
patch -Np1 -i "$src/planar.patch"       # egfx_codec = "planar"
patch -Np1 -i "$src/capture-pacing.patch"  # no full-screen captures on pointer motion

export CARGO_HOME="$work/cargo-home"    # private, so IronRDP can be patched
cargo fetch --locked
ironrdp=$(echo "$CARGO_HOME"/git/checkouts/ironrdp-*/5198cde)
patch -d "$ironrdp" -Np1 -i "$src/ironrdp-planar.patch"

unset CFLAGS CXXFLAGS LDFLAGS
cargo build --frozen --release

sudo install -Dm755 target/release/hypr-rdp /usr/local/bin/hypr-rdp
sudo install -Dm755 "$src/hypr-rdp-cursor" /usr/local/bin/hypr-rdp-cursor
sudo install -d "$(dirname "$stamp")"
echo "$ver $(cat "$src"/*.patch | sha256sum | cut -d' ' -f1)" | sudo tee "$stamp" >/dev/null
cd /; rm -rf "$work"                    # ~1.5 GB of build output
echo "installed hypr-rdp $ver"
