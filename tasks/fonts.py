"""JetBrainsMono Nerd Font (patched with icon glyphs), same files as Omarchy."""
from pyinfra import host
from pyinfra.operations import server

ver = host.data.nerd_font_version
dest = "/usr/local/share/fonts/jetbrains-mono-nerd"
server.shell(
    name=f"JetBrainsMono Nerd Font {ver} (Regular/Bold/Italic/BoldItalic, checksum verified)",
    commands=[f"""[ -f {dest}/.v{ver} ] || (set -e
t=$(mktemp -d)
curl -fsSL -o "$t/f.tar.xz" https://github.com/ryanoasis/nerd-fonts/releases/download/v{ver}/JetBrainsMono.tar.xz
echo "{host.data.nerd_font_sha256}  $t/f.tar.xz" | sha256sum -c --quiet
install -d -m 755 {dest}
tar -xJf "$t/f.tar.xz" -C {dest} JetBrainsMonoNerdFont-Regular.ttf JetBrainsMonoNerdFont-Bold.ttf \\
    JetBrainsMonoNerdFont-Italic.ttf JetBrainsMonoNerdFont-BoldItalic.ttf
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
