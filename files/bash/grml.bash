# Managed by debian-hypr. grml-inspired bash (grml's config is zsh-only;
# this ports the parts bash can do). History settings live in ~/.bashrc.
[[ $- == *i* ]] || return

# --- shell options (grml: auto_cd, correct, extended globbing) -----------------
shopt -s autocd cdspell dirspell globstar extglob checkwinsize no_empty_cmd_completion

# --- completion -------------------------------------------------------------------
[ -r /usr/share/bash-completion/bash_completion ] && . /usr/share/bash-completion/bash_completion

# --- colours ------------------------------------------------------------------------
command -v dircolors >/dev/null && eval "$(dircolors -b)"
alias ls='ls --color=auto -F'
alias grep='grep --color=auto'
alias diff='diff --color=auto'
alias ip='ip -color=auto'
# Keyboard layout (Hyprland, live): US / German without dead keys
alias kbus='hypr-kbd us' kbde='hypr-kbd de'

# --- grml aliases -------------------------------------------------------------------
alias l='ls -lF'
alias la='ls -la'
alias ll='ls -l'
alias lh='ls -hAl'
alias lsd='ls -d */'
alias da='du -sch'
alias j='jobs -l'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias d='dirs -v'
alias hist='history | grep --'

# --- directory stack like grml's auto_pushd: cd remembers, cd -N jumps back -------------
cd() {
  if [ "$#" -eq 1 ] && [[ $1 =~ ^-[0-9]+$ ]]; then
    builtin pushd "+${1#-}" >/dev/null
  elif [ "$#" -eq 0 ]; then
    builtin pushd "$HOME" >/dev/null
  else
    builtin pushd "$@" >/dev/null
  fi
}
DIRSTACKSIZE=20

# --- grml functions ------------------------------------------------------------------
mkcd() { mkdir -p -- "$1" && cd -- "$1"; }                 # make dir and enter it
cdt()  { cd "$(mktemp -d)" && pwd; }                        # cd into a fresh temp dir
bk()   { local f; for f in "$@"; do cp -a -- "$f" "$f.bak.$(date +%Y%m%dT%H%M%S)"; done; }  # backup copy
sll()  { local f; for f in "$@"; do while [ -L "$f" ]; do ls -l -- "$f"; f=$(readlink -- "$f"); done; ls -l -- "$f"; done; }  # follow symlinks
ssearch() { grep -rn --color=auto -- "$1" "${2:-.}"; }      # search recursively

# --- prompt: user@host cwd (git) %, red user for root, red exit code on failure ---------
[ -r /usr/lib/git-core/git-sh-prompt ] && . /usr/lib/git-core/git-sh-prompt
GIT_PS1_SHOWDIRTYSTATE=1
GIT_PS1_SHOWUNTRACKEDFILES=1
__grml_prompt() {
  local rc=$?
  local blue='\[\e[1;34m\]' red='\[\e[1;31m\]' yellow='\[\e[0;33m\]' bold='\[\e[1m\]' off='\[\e[0m\]'
  local user="$blue\u$off"; [ "$EUID" -eq 0 ] && user="$red\u$off"
  local code=""; [ "$rc" -ne 0 ] && code="$red$rc$off "
  local git=""; declare -F __git_ps1 >/dev/null && git="$yellow$(__git_ps1 ' (%s)')$off"
  # Short tmux-style terminal/tab title: current directory name only
  local title="\[\e]0;\W\a\]"
  PS1="$title$code$user@\h $bold\w$off$git \\$ "
}
PROMPT_COMMAND="__grml_prompt${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
