"""Bash with Kali-style history; xfce4-terminal (paste review dialog) themed like Terminator."""
from io import StringIO

from pyinfra import host
from pyinfra.operations import apt, files, server

home = host.data.desktop_home

apt.packages(name="bash-completion", packages=["bash-completion"], no_recommends=True, _sudo=True)

files.put(name="grml-inspired bash (prompt, aliases, dir stack, functions)",
          src="files/bash/grml.bash", dest=f"{home}/.config/bash/grml.bash", mode="644")
files.block(
    name="bash: load the grml-inspired config",
    path=f"{home}/.bashrc",
    marker="# {mark} debian-hypr: grml",
    content='[ -r "$HOME/.config/bash/grml.bash" ] && . "$HOME/.config/bash/grml.bash"',
    try_prevent_shell_expansion=True,
)

# --- Kali-like history -------------------------------------------------------------------
files.block(
    name="bash: large, shared, timestamped history (Kali-style)",
    path=f"{home}/.bashrc",
    marker="# {mark} debian-hypr: history",
    content="""HISTSIZE=100000
HISTFILESIZE=200000
HISTCONTROL=ignoreboth:erasedups
HISTTIMEFORMAT='%F %T  '
HISTIGNORE='ls:ll:cd:pwd:bg:fg:clear:history:exit'
shopt -s histappend cmdhist
# Every terminal sees the others' commands immediately (like zsh share_history on Kali).
PROMPT_COMMAND="history -a; history -n${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
export PATH="$HOME/.local/bin:$PATH"
""",
    try_prevent_shell_expansion=True,
)

files.put(
    name="readline: type a prefix + Up/Down to search history (Kali-style)",
    src=StringIO("""# Managed by debian-hypr
$include /etc/inputrc
"\\e[A": history-search-backward
"\\e[B": history-search-forward
"\\eOA": history-search-backward
"\\eOB": history-search-forward
set completion-ignore-case on
set show-all-if-ambiguous on
set colored-stats on
"""),
    dest=f"{home}/.inputrc",
    mode="644",
)

# --- xfce4-terminal: cobalt like Terminator, unsafe-paste review dialog on ---------------
palette = ";".join([
    "#00347d", "#e87a74", "#7ac48a", "#f1dc9a", "#8bb4e0", "#b89cd9", "#6f88a7", "#e8dfc9",
    "#1453af", "#e87a74", "#7ac48a", "#ffe9a8", "#8bb4e0", "#d29acb", "#8bb4e0", "#fff8f0",
])
props = {
    "/misc-show-unsafe-paste-dialog": ("bool", "true"),
    "/misc-cursor-blinks": ("bool", "false"),
    "/color-use-theme": ("bool", "false"),
    "/color-background": ("string", "#0049b2"),
    "/color-foreground": ("string", "#fff8f0"),
    "/color-cursor": ("string", "#f1dc9a"),
    "/color-cursor-use-default": ("bool", "false"),
    "/color-palette": ("string", palette),
    "/font-use-system": ("bool", "false"),
    "/font-name": ("string", "JetBrainsMono Nerd Font 11"),
    "/misc-menubar-default": ("bool", "false"),
    "/scrolling-bar": ("string", "TERMINAL_SCROLLBAR_NONE"),
}
cmds = [
    f"xfconf-query -c xfce4-terminal -p {p} -n -t {t} -s '{v}' 2>/dev/null || "
    f"xfconf-query -c xfce4-terminal -p {p} -s '{v}'"
    for p, (t, v) in props.items()
]
server.shell(
    name="xfce4-terminal: cobalt theme, JetBrainsMono Nerd Font, paste review dialog",
    commands=[f"export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus; {c}" for c in cmds],
)
