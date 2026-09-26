-- During RDP sessions Hyprland's own cursor is hidden (the client draws one),
-- which also hides the resize arrow. Show Hyprland's cursor again only while
-- the pointer is in a window's resize zone on its right edge, bottom edge or
-- bottom-right corner, so resizing there gets visual feedback.

local TICK_MS = 100
local GRAB = 2 + 15 -- general.border_size + general.extend_border_grab_area
local FLAG = (os.getenv("XDG_RUNTIME_DIR") or "/tmp") .. "/hypr-rdp-active"

local shown = nil -- last state we set: true = visible, false = hidden

local function rdp_active()
  local f = io.open(FLAG, "r")
  if f then f:close() end
  return f ~= nil
end

local function in_resize_zone(c)
  for _, w in ipairs(hl.get_windows() or {}) do
    if w.visible and w.floating and w.fullscreen == 0 then
      local x1, y1 = w.at.x, w.at.y
      local x2, y2 = x1 + w.size.x, y1 + w.size.y
      local right = c.x > x2 and c.x <= x2 + GRAB and c.y >= y1 and c.y <= y2 + GRAB
      local bottom = c.y > y2 and c.y <= y2 + GRAB and c.x >= x1 and c.x <= x2 + GRAB
      if right or bottom then return true end
    end
  end
  return false
end

local function tick()
  if not rdp_active() then
    shown = nil -- session hooks own the cursor when no RDP client is connected
    return
  end
  local c = hl.get_cursor_pos()
  local want = c and in_resize_zone(c) or false
  if want ~= shown then
    shown = want
    hl.config({ cursor = { invisible = not want } })
  end
end

hl.timer(tick, { timeout = TICK_MS, type = "repeat" })
