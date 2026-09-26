"""Build hypr-rdp with the hypr-rdp-clearcodec patches as a Debian package.

    dagger call deb export --path=dist/        # -> dist/hypr-rdp-clearcodec_<ver>_amd64.deb

The patches and helper files come from files/hypr-rdp in this repository.
"""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type

BUILD_DEPS = [
    "ca-certificates", "curl", "patch", "pkg-config", "make", "cmake", "clang", "libclang-dev",
    "cargo", "rustc", "dpkg-dev",
    "libva-dev", "libpipewire-0.3-dev", "libxkbcommon-dev", "libwayland-dev",
    "libgbm-dev", "libfuse3-dev", "libpulse-dev", "libssl-dev",
]

PATCHES = ["clearcodec.patch", "planar.patch", "capture-pacing.patch"]
IRONRDP_PATCH = "ironrdp-planar.patch"
IRONRDP_REV = "5198cde"


@object_type
class HyprRdpDeb:
    @function
    def builder(
        self,
        base: Annotated[str, Doc("Debian base image")] = "debian:forky-slim",
    ) -> dagger.Container:
        """Debian container with the Rust toolchain and hypr-rdp build dependencies."""
        return (
            dag.container()
            .from_(base)
            .with_env_variable("DEBIAN_FRONTEND", "noninteractive")
            .with_mounted_cache("/var/cache/apt/archives", dag.cache_volume("apt-archives"))
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "--no-install-recommends", *BUILD_DEPS])
        )

    @function
    async def deb(
        self,
        files: Annotated[
            dagger.Directory,
            DefaultPath("files/hypr-rdp"),
            Doc("Directory with the patches, hypr-rdp-cursor and the user unit"),
        ],
        version: Annotated[str, Doc("hypr-rdp upstream version")] = "0.1.6",
        sha256: Annotated[str, Doc("sha256 of the upstream release tarball")] = (
            "6857d170da5d678211eb5318bb03c1bd3ff9503f5c26cf0ea05755fa63ff1d13"
        ),
        revision: Annotated[str, Doc("Debian package revision")] = "3",
        base: Annotated[str, Doc("Debian base image")] = "debian:forky-slim",
    ) -> dagger.File:
        """Build the patched hypr-rdp and return the .deb."""
        pkg = "hypr-rdp-clearcodec"
        full = f"{version}-{revision}"
        src = f"/build/hypr-rdp-{version}"
        tarball = f"https://github.com/MuNeNICK/hypr-rdp/archive/refs/tags/v{version}.tar.gz"

        apply = " && ".join(f"patch -Np1 -i /in/{p}" for p in PATCHES)
        build = f"""set -eu
cd /build
curl -fsSL -o src.tar.gz {tarball}
echo "{sha256}  src.tar.gz" | sha256sum -c --quiet
tar xzf src.tar.gz
cd {src}
{apply}
cargo fetch --locked
patch -d "$(echo $CARGO_HOME/git/checkouts/ironrdp-*/{IRONRDP_REV})" -Np1 -i /in/{IRONRDP_PATCH}
cargo build --frozen --release
"""

        control = f"""Package: {pkg}
Version: {full}
Section: net
Priority: optional
Architecture: amd64
Maintainer: hyperland-forky-worker-vm <noreply@github.com>
Depends: ${{shlibs:Depends}}, fuse3, pulseaudio-utils
Provides: hypr-rdp
Conflicts: hypr-rdp
Replaces: hypr-rdp
Homepage: https://github.com/MuNeNICK/hypr-rdp
Description: Native RDP server for Hyprland (ClearCodec/planar, capture pacing)
 hypr-rdp {version} with the hypr-rdp-clearcodec patches: egfx_codec
 "clearcodec" (lossless, damage-only) and "planar", plus capture request
 pacing for GPU-less VMs. Includes hypr-rdp-cursor and a systemd user unit.
"""

        package = f"""set -eu
root=/pkg/{pkg}_{full}_amd64
install -Dm755 {src}/target/release/hypr-rdp $root/usr/bin/hypr-rdp
install -Dm755 /in/hypr-rdp-cursor $root/usr/bin/hypr-rdp-cursor
sed 's|/usr/local/bin/hypr-rdp|/usr/bin/hypr-rdp|' /in/hypr-rdp.service > /tmp/unit
install -Dm644 /tmp/unit $root/usr/lib/systemd/user/hypr-rdp.service
install -Dm644 {src}/LICENSE $root/usr/share/doc/{pkg}/copyright
install -d $root/DEBIAN
cat > /tmp/control <<'EOF'
{control}EOF
# dpkg-shlibdeps wants a source-format debian/control next to the tree
cd /pkg && mkdir -p debian
printf 'Source: {pkg}\n\nPackage: {pkg}\nArchitecture: amd64\n' > debian/control
deps=$(dpkg-shlibdeps -O -e$root/usr/bin/hypr-rdp | sed -n 's/^shlibs:Depends=//p')
test -n "$deps"
sed "s|\\${{shlibs:Depends}}|$deps|" /tmp/control > $root/DEBIAN/control
dpkg-deb --root-owner-group --build $root /pkg/out.deb
dpkg-deb --info /pkg/out.deb
"""

        built = (
            self.builder(base)
            # Only crate downloads are cached; git checkouts (IronRDP, patched in
            # place) are fetched fresh every build.
            .with_mounted_cache("/root/.cargo-home/registry", dag.cache_volume("hypr-rdp-cargo-registry"))
            .with_env_variable("CARGO_HOME", "/root/.cargo-home")
            .with_directory("/in", files)
            .with_exec(["sh", "-c", "rm -rf /build && mkdir -p /build"])
            .with_exec(["sh", "-c", build])
            .with_exec(["sh", "-c", package])
        )
        return built.file("/pkg/out.deb").with_name(f"{pkg}_{full}_amd64.deb")
