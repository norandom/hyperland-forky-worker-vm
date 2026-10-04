"""Per-user developer tools: uv, npm globals + pnpm, Aikido Safe Chain, Neovim (nvim-simple),\nccusage, euporie, Claude Code skills."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import files, server, systemd

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

# --- Neovim: nvim-simple (CUA keys, menu bar, Berg theme), pinned --------------------------
# github.com/norandom/nvim-simple at host.data.nvim_simple_commit; its vim-plug plugins
# (quickui, airline, nerdtree, devicons) are installed headless on first deploy.
rev = host.data.nvim_simple_commit
cfg = f"{home}/.config/nvim"
server.shell(
    name=f"nvim: nvim-simple {rev[:7]} (old LazyVim config moved to ~/.config/nvim.lazyvim)",
    commands=[f"""[ "$(cat {cfg}/.nvim-simple 2>/dev/null)" = "{rev}" ] && exit 0; set -e
if [ -e {cfg}/lazyvim.json ]; then
  rm -rf {cfg}.lazyvim; mv {cfg} {cfg}.lazyvim
  rm -rf {home}/.local/share/nvim/lazy {home}/.local/share/nvim/mason {home}/.local/share/nvim/snacks \
         {home}/.local/state/nvim/lazy {home}/.cache/nvim
fi
t=$(mktemp -d)
git -C "$t" init -q && git -C "$t" fetch -q --depth 1 https://github.com/norandom/nvim-simple.git {rev}
git -C "$t" checkout -q FETCH_HEAD
mkdir -p {cfg}; cp -r "$t"/nvim/. {cfg}/
echo {rev} > {cfg}/.nvim-simple; rm -rf "$t\""""],
)
files.put(name="nvim: Berg light for the cream terminal theme (dark otherwise)",
          src="files/nvim/plugin/debian-hypr-theme.lua", dest=f"{cfg}/plugin/debian-hypr-theme.lua", mode="644")
server.shell(
    name="nvim: install plugins (headless PlugInstall)",
    commands=[env + f"[ -d {cfg}/plugged/vim-quickui ] || "
              "timeout 600 nvim --headless +PlugInstall +qall >/dev/null 2>&1 || true"],
)

# --- rclone mounts (e.g. OneDrive personal) as systemd user services ----------------------
for remote, folder in host.data.rclone_mounts.items():
    unit = files.put(
        name=f"rclone mount {remote}: -> ~/{folder} (user service)",
        src=StringIO(f"""# Managed by debian-hypr
[Unit]
Description=rclone mount {remote}: on ~/{folder}
After=network-online.target

[Service]
Type=notify
# Skipped until the remote exists (rclone config)
ExecCondition=/bin/sh -c '/usr/local/bin/rclone listremotes | grep -qx {remote}:'
ExecStartPre=/bin/mkdir -p %h/{folder}
ExecStart=/usr/local/bin/rclone mount {remote}: %h/{folder} --vfs-cache-mode full --vfs-cache-max-size 2G --dir-cache-time 5m
ExecStop=/bin/fusermount3 -uz %h/{folder}
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
"""),
        dest=f"{home}/.config/systemd/user/rclone-{remote}.service",
        mode="644",
    )
    server.shell(name=f"rclone-{remote}: systemd user daemon-reload", commands=["systemctl --user daemon-reload"],
                 _if=unit.did_change)
    systemd.service(name=f"rclone-{remote}.service enabled", service=f"rclone-{remote}.service",
                    user_mode=True, enabled=True, running=True)

# --- Agent / notebook tools ---------------------------------------------------------------
# --- Kubernetes: ax (built with Go), shell completion for kubectl / helm / ax / rc -----------
ax = host.data.get("ax_version")
if ax:
    server.shell(
        name=f"ax {ax} (Google's agentic orchestration CLI, built with Go)",
        commands=[f"""[ "$(cat {home}/.local/share/debian-hypr/ax.version 2>/dev/null)" = "{ax}" ] || (set -e
GOTOOLCHAIN={host.data.ax_go_toolchain} GOBIN={bin_dir} go install github.com/google/ax/cmd/ax@{ax}
mkdir -p {home}/.local/share/debian-hypr && echo {ax} > {home}/.local/share/debian-hypr/ax.version)"""],
    )
comp = f"{home}/.local/share/bash-completion/completions"
server.shell(
    name="bash completion: kubectl (+ alias k), helm, ax, rc",
    commands=[f"""mkdir -p {comp}
command -v kubectl >/dev/null && kubectl completion bash > {comp}/kubectl && \
  {{ cat {comp}/kubectl; echo 'complete -o default -F __start_kubectl k'; }} > {comp}/k
command -v helm >/dev/null && helm completion bash > {comp}/helm
[ -x {bin_dir}/ax ] && {bin_dir}/ax completion bash > {comp}/ax 2>/dev/null || rm -f {comp}/ax
command -v rc >/dev/null && rc completions bash > {comp}/rc 2>/dev/null || rm -f {comp}/rc
true"""],
)

server.shell(
    name="Codex CLI (npm global; log in once with: codex login)",
    commands=[env + f"[ -x {bin_dir}/codex ] || npm install -g @openai/codex"],
)
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
