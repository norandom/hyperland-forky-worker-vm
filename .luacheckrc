-- luacheck (lint workflow): Hyprland's Lua config and the nvim theme
std = "max"
globals = {
  "hl",              -- Hyprland's Lua API
  "vim",             -- Neovim
  "aerosnap_timer",  -- global on purpose: survives config reloads, so the old timer can be stopped
}
max_line_length = false  -- long hl.* calls are the repo's style (as in ruff's config)
