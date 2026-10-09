-- Managed by debian-hypr. Colours: cream-blue-light
-- (github.com/norandom/opencode-cream-blue).
hl.config({
  general = {
    gaps_in = 4,
    gaps_out = 8,
    border_size = 2,
    col = {
      active_border = "rgb(4a90d9)",
      inactive_border = "rgb(d9d0c0)",
    },
    resize_on_border = true,
    layout = "dwindle",
    -- Magnetic snapping for floating windows: gentle (pulls only within 10-12 px).
    snap = { enabled = true, window_gap = 10, monitor_gap = 12, respect_gaps = false },
  },
  decoration = {
    rounding = 0,
    -- Light milky blur, but only for windows switched to glass (hypr-glass,
    -- title bar button); the rule below turns it off for everything else.
    blur = {
      enabled = true, size = 2, passes = 1, noise = 0.02,
      brightness = 1.2, contrast = 0.8, vibrancy = 0, new_optimizations = true,
    },
    shadow = { enabled = false },
  },
  animations = { enabled = false },
  misc = {
    disable_hyprland_logo = true,
    disable_splash_rendering = true,
    force_default_wallpaper = 0,
    -- The "wallpaper": a plain colour costs no memory (no wallpaper process).
    background_color = 0xff3a3a3a,
  },
  ecosystem = { no_update_news = true, no_donation_nag = true },
})

-- No blur by default; hypr-glass overrides this per window.
hl.window_rule({ name = "no-blur-default", match = { class = ".*" }, no_blur = true })

-- Floating vs tiling: see layouts.lua (layout modes, SUPER + L).

-- Keep Hyprland's cursor hidden across config reloads while an RDP session
-- is active (flag set by hypr-rdp-cursor via hypr-rdp-sessionwatch).
local rdp_flag = io.open((os.getenv("XDG_RUNTIME_DIR") or "/tmp") .. "/hypr-rdp-active", "r")
if rdp_flag then
  rdp_flag:close()
  hl.config({ cursor = { invisible = true } })
end

-- Window shadows: off by default (software rendering draws them on the CPU).
-- Switch: hypr-shadow on|off. The look follows the title bar style (hypr-deco).
do
  local HOME = os.getenv("HOME") or ""
  local function first(path, default)
    local f = io.open(path, "r")
    if not f then return default end
    local v = (f:read("*l") or ""):match("^%s*(%S+)") or default
    f:close()
    return v
  end
  if first(HOME .. "/.config/hypr/window-shadows", "off") == "on" then
    if first(HOME .. "/.config/hypr/decorations-style", "mac") == "win311" then
      -- Windows 3.11: hard black drop shadow, bottom right
      hl.config({ decoration = { shadow = {
        enabled = true, sharp = true, range = 0, offset = "4 4", color = "rgba(000000aa)",
      } } })
    else
      -- soft, subtle shadow
      hl.config({ decoration = { shadow = {
        enabled = true, sharp = false, range = 14, render_power = 3, offset = "0 3", color = "rgba(1a2a3f33)",
      } } })
    end
  end
end

-- Night filter (hypr-nightmode, the rabbit in the bar): a config reload resets the
-- screen shader, so re-apply the chosen one here.
do
  local f = io.open(os.getenv("HOME") .. "/.local/state/hypr-nightmode", "r")
  if f then
    local mode = (f:read("l") or ""):match("%a+"); f:close()
    if mode == "green" or mode == "dark" then
      hl.config({ decoration = { screen_shader = os.getenv("HOME") .. "/.config/hypr/shaders/night-" .. mode .. ".glsl" } })
    end
  end
end

-- snitch alert popups (Little Snitch): small, floating, centred, on top of everything
hl.window_rule({ name = "snitch-alert", match = { class = "snitch-alert" }, float = true, center = true, size = "1000 280", pin = true })

-- hyprlock (console lock): if it ever crashes, `hyprlock` can be started again to take over
hl.config({ misc = { allow_session_lock_restore = true } })
