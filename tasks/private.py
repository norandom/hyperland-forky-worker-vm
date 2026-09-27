"""Private data from private/ or the encrypted private.tar.age (see privdata.py):
proprietary fonts, license keys (hypr-licenses; Sublime Text's license file)."""
import sys
import tomllib
from io import StringIO
from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import privdata  # noqa: E402

home = host.data.desktop_home

files.put(name="hypr-licenses (license keys -> clipboard)", src="files/bin/hypr-licenses",
          dest=f"{home}/.local/bin/hypr-licenses", mode="755")
files.put(name="Licenses entry in the app menu", src="files/applications/hypr-licenses.desktop",
          dest=f"{home}/.local/share/applications/hypr-licenses.desktop", mode="644")

src = privdata.load()
if src is None:
    print("private data: none (no private/ or private.tar.age); see private.example/")
else:
    # --- Fonts -> /usr/local/share/fonts/private ------------------------------------------
    fonts = sorted(p for p in (src / "fonts").rglob("*") if p.suffix.lower() in (".ttf", ".otf", ".ttc"))
    dest_dir = "/usr/local/share/fonts/private"
    put = [
        files.put(name=f"Private font: {p.name}", src=str(p), dest=f"{dest_dir}/{p.name}",
                  mode="644", create_remote_dir=True, _sudo=True)
        for p in fonts
    ]
    keep = " ".join(f"'{p.name}'" for p in fonts)
    removed = server.shell(
        name="Private fonts: remove ones no longer in private data",
        commands=[f"""[ -d {dest_dir} ] || exit 0
cd {dest_dir}; for f in *; do [ -f "$f" ] || continue
  case " {keep} " in *" '$f' "*) ;; *) rm -f -- "$f"; echo "removed $f";; esac; done"""],
        _sudo=True,
    )
    server.shell(name="Private fonts: font cache", commands=[f"mkdir -p {dest_dir}; fc-cache -f {dest_dir} >/dev/null"],
                 _sudo=True, _if=lambda: any(op.did_change() for op in put) or removed.did_change())

    # --- Licenses ------------------------------------------------------------------------
    lic_file = src / "licenses.toml"
    if lic_file.is_file():
        files.put(name="License keys (~/.local/share/licenses/licenses.toml, 0600)", src=str(lic_file),
                  dest=f"{home}/.local/share/licenses/licenses.toml", mode="600", create_remote_dir=True)
        lic = tomllib.loads(lic_file.read_text())
        sublime = lic.get("sublime-text", {}).get("key", "").strip()
        if sublime and "..." not in sublime:
            files.put(name="Sublime Text license file", src=StringIO(sublime + "\n"),
                      dest=f"{home}/.config/sublime-text/Local/License.sublime_license",
                      mode="600", create_remote_dir=True)
