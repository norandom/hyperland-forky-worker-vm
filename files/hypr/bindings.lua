-- Managed by debian-hypr. SUPER = Right Option on the Apple keyboard;
-- SHIFT + Print = one-shot Super (keyboards without a free Super key).
local function exec(cmd) return hl.dsp.exec_cmd(cmd) end
local app = "uwsm app -- "

-- Every SUPER binding below is also recorded for the one-shot "super" submap
-- (end of file): keyboards without a free Super key use SHIFT + Print instead.
local super_binds = {}
local bind = hl.bind
hl.bind = function(keys, action, opts)
  bind(keys, action, opts)
  local rest = keys:match("^SUPER %+ (.+)$")
  if rest then super_binds[#super_binds + 1] = { rest, action, opts } end
end

hl.bind("SUPER + RETURN", exec(app .. "hypr-term"), { description = "Terminal" })
hl.bind("SUPER + Y", exec("$HOME/.local/bin/hypr-termtheme next"), { description = "Next terminal theme" })
hl.bind("SUPER + SHIFT + RETURN", exec(app .. "xfce4-terminal"), { description = "Terminal (paste review)" })
hl.bind("SUPER + E", exec(app .. "xfe"), { description = "File manager" })
hl.bind("SUPER + V", exec("$HOME/.local/bin/hypr-cliphist pick"), { description = "Clipboard history" })
hl.bind("SUPER + G", exec("$HOME/.local/bin/hypr-glass"), { description = "Glass window on/off" })
hl.bind("SUPER + P", exec("$HOME/.local/bin/hypr-pin"), { description = "Stay on top on/off" })
hl.bind("SUPER + SPACE", exec(app .. "fuzzel"), { description = "Launcher (search)" })
hl.bind("SUPER + A", exec("$HOME/.local/bin/hypr-appmenu"), { description = "Application menu" })
hl.bind("SUPER + ESCAPE", exec("$HOME/.local/bin/hypr-appmenu power"), { description = "Power menu" })
hl.bind("SUPER + W", hl.dsp.window.close(), { description = "Close window" })
hl.bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen" }), { description = "Full screen" })
hl.bind("SUPER + SHIFT + F", hl.dsp.window.fullscreen({ mode = "maximized" }), { description = "Maximize" })
hl.bind("SUPER + T", hl.dsp.window.float({ action = "toggle" }), { description = "Toggle floating/tiling" })
hl.bind("SUPER + L", exec("$HOME/.local/bin/hypr-layout next"), { description = "Next layout mode" })
hl.bind("SUPER + SHIFT + M", exec("uwsm stop"), { description = "Log out (exit Hyprland)" })

-- Focus
hl.bind("SUPER + LEFT", hl.dsp.focus({ direction = "l" }), { description = "Focus left" })
hl.bind("SUPER + RIGHT", hl.dsp.focus({ direction = "r" }), { description = "Focus right" })
hl.bind("SUPER + UP", hl.dsp.focus({ direction = "u" }), { description = "Focus up" })
hl.bind("SUPER + DOWN", hl.dsp.focus({ direction = "d" }), { description = "Focus down" })
-- SUPER + TAB, not ALT + TAB: left Option is the Mac Option key (level 3, input.lua)
hl.bind("SUPER + TAB", hl.dsp.window.cycle_next(), { description = "Next window" })
hl.bind("SUPER + TAB", hl.dsp.window.bring_to_top(), { description = "Raise window" })

-- Mouse: SUPER + left drag = move, SUPER + right drag = resize
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true, description = "Move window" })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true, description = "Resize window" })

-- Keyboard resize: the two keys right of 0 (de: ß and ´)
hl.bind("SUPER + code:20", hl.dsp.window.resize({ x = -100, y = 0, relative = true }), { description = "Narrower" })
hl.bind("SUPER + code:21", hl.dsp.window.resize({ x = 100, y = 0, relative = true }), { description = "Wider" })
hl.bind("SUPER + SHIFT + code:20", hl.dsp.window.resize({ x = 0, y = -100, relative = true }), { description = "Shorter" })
hl.bind("SUPER + SHIFT + code:21", hl.dsp.window.resize({ x = 0, y = 100, relative = true }), { description = "Taller" })

-- Minimized windows (⊟ in the Windows 3.11 title bars) live on a hidden
-- workspace; SUPER + M shows / hides it.
hl.bind("SUPER + M", hl.dsp.workspace.toggle_special("minimized"), { description = "Show minimized windows" })

-- Right-click on the empty desktop opens the application menu at the cursor.
-- non_consuming: applications still receive every right-click.
local TITLEBAR = 26 -- hyprbars bar + border above each window
local function on_desktop(c)
  local mon = hl.get_monitor_at_cursor()
  if not mon or c.y < mon.position.y + (mon.reserved and mon.reserved.top or 0) then
    return false, nil -- on the top bar
  end
  for _, w in ipairs(hl.get_windows() or {}) do
    if w.visible and w.mapped then
      if c.x >= w.at.x - 4 and c.x <= w.at.x + w.size.x + 4
        and c.y >= w.at.y - TITLEBAR and c.y <= w.at.y + w.size.y + 4 then
        return false, nil
      end
    end
  end
  return true, mon
end

hl.bind("mouse:273", function()
  local c = hl.get_cursor_pos()
  if not c then return end
  local free, mon = on_desktop(c)
  if free then
    local x = math.floor(c.x - mon.position.x)
    local y = math.floor(c.y - mon.position.y)
    hl.exec_cmd("$HOME/.local/bin/hypr-appmenu --at " .. x .. " " .. y)
  end
end, { non_consuming = true, description = "Desktop menu (right-click)" })

hl.bind = bind

-- One-shot Super (GPD Pocket & co.: Windows key taken by Windows, no Right Option):
-- SHIFT + Print, or the ❖ bar button, then the key (or mouse drag) that would
-- follow SUPER. The submap resets after that one action; Escape or any other key
-- cancels. The bar shows "SUPER" while it is armed (hyprland/submap).
hl.define_submap("super", "reset", function()
  for _, b in ipairs(super_binds) do
    bind(b[1], b[2], b[3])
  end
  bind("ESCAPE", hl.dsp.submap("reset"), { description = "Cancel one-shot Super" })
  bind("catchall", hl.dsp.submap("reset"), { description = "Cancel one-shot Super" })
end)
hl.bind("SHIFT + Print", hl.dsp.submap("super"), { description = "One-shot Super (next key)" })
