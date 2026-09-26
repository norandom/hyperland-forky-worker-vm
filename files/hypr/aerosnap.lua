-- Windows-style edge snapping for floating windows.
-- Drag a window (title bar or SUPER+drag) until the cursor touches the
-- left/right screen edge -> left/right half; top edge -> maximized area.
-- Dragging a snapped window again restores its previous size.
-- Hyprland has no drag-end event, so a timer watches the active window:
-- a drag is over once the window has stopped moving for SETTLE_TICKS ticks.

local TICK_MS = 100
local SETTLE_TICKS = 3
local EDGE_PX = 2
local TITLE_BAR = 24 -- hyprbars bar_height (drawn above the window)
local BORDER = 2 -- general.border_size

local state = { addr = nil, at = nil, size = nil, moving = false, still = 0, cursor = nil, snapped = {} }

local function same(a, b)
  return a and b and a.x == b.x and a.y == b.y
end

local function snap_zone(cursor, mon)
  local mx, my = mon.position.x, mon.position.y
  local mw, mh = mon.size.width / mon.scale, mon.size.height / mon.scale
  if cursor.x <= mx + EDGE_PX then return "left", mx, my, mw, mh end
  if cursor.x >= mx + mw - 1 - EDGE_PX then return "right", mx, my, mw, mh end
  if cursor.y <= my + EDGE_PX then return "top", mx, my, mw, mh end
end

local function apply_snap(win, cursor)
  local mon = hl.get_monitor_at_cursor()
  if not mon then return end
  local zone, mx, my, mw, mh = snap_zone(cursor, mon)
  if not zone then return end

  local r = mon.reserved
  local ax, ay = mx + r.left, my + r.top
  local aw, ah = mw - r.left - r.right, mh - r.top - r.bottom

  local x, w = ax, aw
  if zone == "left" then w = aw / 2 end
  if zone == "right" then x, w = ax + aw / 2, aw / 2 end

  -- Leave room for the title bar and borders so the whole frame fits.
  local nx, ny = math.floor(x + BORDER), math.floor(ay + TITLE_BAR + BORDER)
  local nw, nh = math.floor(w - 2 * BORDER), math.floor(ah - TITLE_BAR - 2 * BORDER)

  state.snapped[win.address] = state.snapped[win.address] or { x = win.size.x, y = win.size.y }
  hl.dispatch(hl.dsp.window.resize({ x = nw, y = nh }))
  hl.dispatch(hl.dsp.window.move({ x = nx, y = ny }))
  state.at, state.size = { x = nx, y = ny }, { x = nw, y = nh }
end

local function tick()
  local win = hl.get_active_window()
  if not win or not win.floating or win.fullscreen ~= 0 then
    state.addr, state.moving = nil, false
    return
  end

  local at, size, cursor = win.at, win.size, hl.get_cursor_pos()

  if state.addr ~= win.address then
    state.addr, state.at, state.size, state.moving, state.still = win.address, at, size, false, 0
    return
  end

  if not same(at, state.at) and same(size, state.size) then
    -- Window is being dragged.
    if not state.moving then
      local orig = state.snapped[win.address]
      if orig then
        -- Unsnap: restore the pre-snap size, keep the cursor on the title bar.
        state.snapped[win.address] = nil
        hl.dispatch(hl.dsp.window.resize({ x = orig.x, y = orig.y }))
        hl.dispatch(hl.dsp.window.move({ x = math.floor(cursor.x - orig.x / 2), y = at.y }))
      end
    end
    state.moving, state.still, state.cursor = true, 0, cursor
  elseif state.moving then
    state.still = state.still + 1
    if state.still >= SETTLE_TICKS then
      state.moving = false
      apply_snap(win, state.cursor)
    end
  end

  state.at, state.size = win.at, win.size
end

if aerosnap_timer then
  pcall(function() aerosnap_timer:set_enabled(false) end)
end
aerosnap_timer = hl.timer(tick, { timeout = TICK_MS, type = "repeat" })
