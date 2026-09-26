"""Nerd Fonts (icon glyphs): JetBrainsMono (UI, as on Omarchy) and FiraCode (terminals)."""
from pyinfra import host
from pyinfra.operations import server

ver = host.data.nerd_font_version
for family, (sha, styles) in host.data.nerd_fonts.items():
    dest = f"/usr/local/share/fonts/{family.lower()}-nerd"
    names = " ".join(f"{family}NerdFont-{st}.ttf" for st in styles)
    server.shell(
        name=f"{family} Nerd Font {ver} ({', '.join(styles)}; checksum verified)",
        commands=[f"""[ -f {dest}/.v{ver} ] || (set -e
t=$(mktemp -d)
curl -fsSL -o "$t/f.tar.xz" https://github.com/ryanoasis/nerd-fonts/releases/download/v{ver}/{family}.tar.xz
echo "{sha}  $t/f.tar.xz" | sha256sum -c --quiet
install -d -m 755 {dest}
tar -xJf "$t/f.tar.xz" -C {dest} {names}
chmod 644 {dest}/*.ttf; touch {dest}/.v{ver}; rm -rf "$t"
fc-cache -f {dest} >/dev/null)"""],
        _sudo=True,
    )

from pyinfra.operations import files  # noqa: E402

fc = files.template(
    name=f"fontconfig: hintslight, {host.data.font_rendering} antialiasing, monospace = Nerd Font",
    src="templates/fontconfig/fonts.conf.j2",
    dest=f"{host.data.desktop_home}/.config/fontconfig/fonts.conf",
    mode="644",
)
server.shell(name="fontconfig cache", commands=["fc-cache -f >/dev/null"], _if=fc.did_change)
