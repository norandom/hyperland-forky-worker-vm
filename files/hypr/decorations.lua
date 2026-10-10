-- Managed by debian-hypr. Title bars from the Debian package
-- hyprland-plugin-hyprbars (ABI-locked to the installed Hyprland).
--
-- Two styles, switch any time (no redeploy):  hypr-deco win311 | mac
-- The choice lives in ~/.config/hypr/decorations-style (default: mac).
hl.plugin.load("/usr/lib/x86_64-linux-gnu/hyprland/plugins/libhyprbars.so")

-- The plugin loads after this config pass; configure it on the next reload.
if not (hl.plugin and hl.plugin.hyprbars) then
  return
end

-- This VM's colour (hostcolor.lua, written by the deploy from the hostname): you see which
-- RDP VM you're on. Without it, the original navy / cream.
local ok, hc = pcall(require, "hostcolor")
if not ok or type(hc) ~= "table" then hc = { color = "000080", pale = "ebe3d6" } end

local style = "mac"
local f = io.open((os.getenv("HOME") or "") .. "/.config/hypr/decorations-style", "r")
if f then
  style = (f:read("*l") or "mac"):match("^%s*(%S+)") or "mac"
  f:close()
end

local maximize = "hyprctl dispatch 'hl.dsp.window.fullscreen({ mode = \"maximized\" })'"
local close = "hyprctl dispatch 'hl.dsp.window.close()'"
local minimize = "hyprctl dispatch 'hl.dsp.window.move({ workspace = \"special:minimized\", follow = false })'"
local glass = "$HOME/.local/bin/hypr-glass"   -- milky see-through on/off
local pin = "$HOME/.local/bin/hypr-pin"       -- stay on top on/off

if style == "win311" then
  -- Windows 3.11: navy title bar, white centred title, square buttons on the right.
  hl.config({
    general = { col = { active_border = "rgb(" .. hc.color .. ")", inactive_border = "rgb(c0c0c0)" } },
    plugin = {
      hyprbars = {
        bar_height = 22,
        bar_color = "rgb(" .. hc.color .. ")",
        ["col.text"] = "rgb(ffffff)",
        bar_text_size = 11,
        bar_text_font = "Sans Bold",
        bar_text_align = "center",
        bar_buttons_alignment = "right",
        bar_padding = 4,
        bar_button_padding = 2,
        on_double_click = maximize,
      },
    },
  })
  -- First added = outermost: [▒][⊤][⊟][⊠] = glass, on top, minimize, close.
  hl.plugin.hyprbars.add_button({
    bg_color = "rgba(00000000)", fg_color = "rgb(ffffff)", size = 22, icon = "⊠", action = close,
  })
  hl.plugin.hyprbars.add_button({
    bg_color = "rgba(00000000)", fg_color = "rgb(ffffff)", size = 22, icon = "⊟", action = minimize,
  })
  hl.plugin.hyprbars.add_button({
    bg_color = "rgba(00000000)", fg_color = "rgb(ffffff)", size = 22, icon = "⊤", action = pin,
  })
  hl.plugin.hyprbars.add_button({
    bg_color = "rgba(00000000)", fg_color = "rgb(ffffff)", size = 22, icon = "▒", action = glass,
  })
else
  -- macOS-like: a pale tint of the host colour, navy text, red/green buttons on the left.
  hl.config({
    general = { col = { active_border = "rgb(" .. hc.color .. ")" } },
    plugin = {
      hyprbars = {
        bar_height = 24,
        bar_color = "rgb(" .. hc.pale .. ")",
        ["col.text"] = "rgb(2b4570)",
        bar_text_size = 11,
        bar_text_font = "JetBrainsMono Nerd Font",
        bar_text_align = "center",
        bar_buttons_alignment = "left",
        bar_padding = 10,
        on_double_click = maximize,
      },
    },
  })
  hl.plugin.hyprbars.add_button({
    bg_color = "rgb(ff5f57)", fg_color = "rgb(4d0000)", size = 12, icon = "", action = close,
  })
  hl.plugin.hyprbars.add_button({
    bg_color = "rgb(28c840)", fg_color = "rgb(003300)", size = 12, icon = "", action = maximize,
  })
  hl.plugin.hyprbars.add_button({
    bg_color = "rgb(8bb4e0)", fg_color = "rgb(00347d)", size = 12, icon = "", action = glass,
  })
  hl.plugin.hyprbars.add_button({
    bg_color = "rgb(a0a0a0)", fg_color = "rgb(333333)", size = 12, icon = "", action = pin,
  })
end
