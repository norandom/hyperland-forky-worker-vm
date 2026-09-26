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
    -- Magnetic snapping for floating windows.
    snap = { enabled = true, window_gap = 40, monitor_gap = 50, respect_gaps = false },
  },
  decoration = {
    rounding = 0,
    blur = { enabled = false },   -- software rendering: no blur
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

-- Floating vs tiling: see layouts.lua (layout modes, SUPER + L).

-- Keep Hyprland's cursor hidden across config reloads while an RDP session
-- is active (flag set by hypr-rdp-cursor via hypr-rdp-sessionwatch).
local rdp_flag = io.open((os.getenv("XDG_RUNTIME_DIR") or "/tmp") .. "/hypr-rdp-active", "r")
if rdp_flag then
  rdp_flag:close()
  hl.config({ cursor = { invisible = true } })
end
