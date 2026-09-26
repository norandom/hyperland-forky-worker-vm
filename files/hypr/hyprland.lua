-- Managed by debian-hypr. Hyprland 0.56 Lua config for a GPU-less VM used
-- over RDP. Same behaviour as the Omarchy setup, without Omarchy.
local dir = (os.getenv("HOME") or "") .. "/.config/hypr/"
package.path = dir .. "?.lua;" .. package.path
-- Re-read our modules on every reload.
for _, m in ipairs({ "monitors", "input", "looknfeel", "layouts", "bindings", "autostart",
                     "decorations", "aerosnap", "cursorzone" }) do
  package.loaded[m] = nil
end

-- Memory/CPU on software rendering (llvmpipe): fewer malloc arenas and
-- fewer llvmpipe threads; no accessibility bus.
hl.env("MALLOC_ARENA_MAX", "2")
hl.env("LP_NUM_THREADS", "2")
hl.env("NO_AT_BRIDGE", "1")
hl.env("XCURSOR_THEME", "Adwaita")
hl.env("XCURSOR_SIZE", "24")

require("monitors")    -- RDP output size memory, console off during RDP
require("input")       -- de layout, Right Option = Super
require("looknfeel")   -- colours, snapping, no animations
require("layouts")     -- dynamic (floating, remembers) / golden-h / golden-v / golden-spiral
require("bindings")    -- keys
require("autostart")   -- waybar, mako
require("decorations") -- hyprbars title bars (Debian package)
require("aerosnap")    -- drag to screen edge -> half / maximize
require("cursorzone")  -- during RDP show Hyprland's cursor only in resize zones
