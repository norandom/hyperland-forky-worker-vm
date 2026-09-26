"""Per-user developer tools: uv, npm globals + pnpm, Aikido Safe Chain, Neovim config,\nccusage, euporie, Claude Code skills."""
from pathlib import Path

from pyinfra import host
from pyinfra.operations import files, server

home = host.data.desktop_home
bin_dir = f"{home}/.local/bin"
env = f'export PATH="{bin_dir}:$PATH"; '

# --- npm globals go to ~/.local (no sudo), then pnpm --------------------------------------
files.line(name="npm global prefix = ~/.local", path=f"{home}/.npmrc",
           line=r"^prefix=.*", replace=f"prefix={home}/.local")
server.shell(
    name="pnpm (npm global, user-level)",
    commands=[env + f"[ -x {bin_dir}/pnpm ] || npm install -g pnpm"],
)

# --- uv (Astral installer, user-level) ---------------------------------------------------------
server.shell(
    name="uv + uvx in ~/.local/bin",
    commands=[f"[ -x {bin_dir}/uv ] || (curl -LsSf https://astral.sh/uv/install.sh | "
              f"env UV_NO_MODIFY_PATH=1 UV_INSTALL_DIR={bin_dir} sh)"],
)

# --- Aikido Safe Chain: malware check for npm/npx/pnpm/pip/uv/uvx ... ---------------------
ver = host.data.safe_chain_version
sha = host.data.safe_chain_installer_sha256
server.shell(
    name=f"Aikido Safe Chain {ver} (pinned installer, checksum verified)",
    commands=[f"""[ -x {home}/.safe-chain/bin/safe-chain ] || (set -e
t=$(mktemp)
curl -fsSL https://github.com/AikidoSec/safe-chain/releases/download/{ver}/install-safe-chain.sh -o "$t"
echo "{sha}  $t" | sha256sum -c -
sh "$t"
rm -f "$t")"""],
)

# --- Neovim: Omarchy's LazyVim config, cream-blue theme ------------------------------------
nvim = [
    files.put(name=f"nvim: {p}", src=f"files/nvim/{p}", dest=f"{home}/.config/nvim/{p}", mode="644")
    for p in sorted(str(f.relative_to("files/nvim")) for f in Path("files/nvim").rglob("*") if f.is_file())
]
# Omarchy preloads every theme plugin for live theme switching; one of them
# (gthelding/monokai-pro.nvim) no longer exists and breaks startup. Only the
# Cream Blue (aether) theme is used here.
removed = files.file(name="nvim: no all-themes preload", path=f"{home}/.config/nvim/lua/plugins/all-themes.lua",
                     present=False)
nvim.append(removed)

server.shell(
    name="nvim: install plugins (headless LazyVim sync)",
    commands=[env + "timeout 900 nvim --headless '+Lazy! sync' '+Lazy! clean' +qa >/dev/null 2>&1 || true"],
    _if=lambda: any(op.did_change() for op in nvim),
)

# --- Agent / notebook tools ---------------------------------------------------------------
server.shell(
    name="ccusage (Claude Code token usage and cost, npm global)",
    commands=[env + f"[ -x {bin_dir}/ccusage ] || npm install -g ccusage"],
)
server.shell(
    name="euporie (Jupyter notebooks in the terminal, uv tool with a Python kernel)",
    commands=[env + "uv tool list 2>/dev/null | grep -q '^euporie ' || uv tool install euporie --with ipykernel"],
)
server.shell(
    name="Claude Code skill: pretty-mermaid (Mermaid -> SVG / terminal ASCII)",
    commands=[env + f"[ -d {home}/.claude/skills/pretty-mermaid ] || "
              "npx -y skills add imxv/pretty-mermaid-skills@pretty-mermaid -g -y"],
)
