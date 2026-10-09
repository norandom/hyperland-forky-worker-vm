-- Managed by debian-hypr.
-- Layout modes (switch: SUPER + L, the bar button, or `hypr-layout <mode>`):
--   dynamic        floating windows (default); remembers each app's position/size
--   golden-h       master left 61.8 %, others stacked right
--   golden-v       master top 61.8 %, others stacked below
--   golden-spiral  every split 61.8 : 38.2, spiralling in (Fibonacci)
-- Also: when the RDP screen changes size, floating windows are scaled with it.

local HOME = os.getenv("HOME") or ""
local MODE_FILE = HOME .. "/.config/hypr/layout-mode"
local GEOM_FILE = HOME .. "/.local/state/hypr-window-geometry"
local PHI = 0.618

local function read_line(path)
  local f = io.open(path, "r")
  if not f then return nil end
  local l = f:read("*l"); f:close()
  return l and l:match("^%s*(%S+)")
end

local mode = read_line(MODE_FILE) or "dynamic"

if mode == "golden-h" or mode == "golden-v" then
  hl.config({
    general = { layout = "master" },
    master = { mfact = PHI, orientation = (mode == "golden-h") and "left" or "top", new_status = "slave" },
  })
elseif mode == "golden-spiral" then
  hl.config({
    general = { layout = "dwindle" },
    -- split ratio 1.0 = 50/50; 2 * 0.618 = 1.236 gives 61.8 : 38.2
    dwindle = { default_split_ratio = 2 * PHI, preserve_split = true, force_split = 2 },
  })
else
  mode = "dynamic"
  hl.config({ general = { layout = "dwindle" } })
  -- Stacking (non-tiling): every new window floats, centered.
  hl.window_rule({ match = { class = ".*" }, float = true, center = true })
end

-- --- dynamic: remember geometry per application class ------------------------------
-- Stored as fractions of the monitor, so it survives RDP resolution changes.
local geom = {}
-- Apps that size themselves (fixed character grid): never remembered or resized.
local OWN_SIZE = { X3270 = true, ["snitch-alert"] = true }  -- snitch-alert: sized by its window rule
do
  local f = io.open(GEOM_FILE, "r")
  if f then
    for line in f:lines() do
      local class, x, y, w, h = line:match("^(%S+) (%S+) (%S+) (%S+) (%S+)$")
      if class then geom[class] = { tonumber(x), tonumber(y), tonumber(w), tonumber(h) } end
    end
    f:close()
  end
end

local function save_geom()
  os.execute("mkdir -p '" .. HOME .. "/.local/state'")
  local f = io.open(GEOM_FILE, "w")
  if not f then return end
  for class, g in pairs(geom) do
    f:write(string.format("%s %.5f %.5f %.5f %.5f\n", class, g[1], g[2], g[3], g[4]))
  end
  f:close()
end

local function mon_box(m)
  return m.position.x, m.position.y, m.size.width / m.scale, m.size.height / m.scale
end

local function addr_sel(w) return "address:" .. w.address end

-- Floating windows stay below the top bar: the title bar (hyprbars, drawn
-- above the window) must not end up under waybar.
local function title_height()
  return read_line(HOME .. "/.config/hypr/decorations-style") == "win311" and 22 or 24
end

local function top_limit(m)
  local r = type(m.reserved) == "table" and (m.reserved.top or 0) or 0
  return m.position.y + r + title_height()
end

if mode == "dynamic" then
  hl.on("window.close", function(w)
    if not (w and w.floating and w.class and w.class ~= "" and w.monitor) or OWN_SIZE[w.class] then return end
    local mx, my, mw, mh = mon_box(w.monitor)
    geom[w.class] = { (w.at.x - mx) / mw, (w.at.y - my) / mh, w.size.x / mw, w.size.y / mh }
    save_geom()
  end)

  hl.on("window.open", function(w)
    if not w then return end
    if w.class and OWN_SIZE[w.class] then return end
    local g, sel = w.class and geom[w.class], addr_sel(w)
    hl.timer(function()
      local win = w
      if not (win and win.floating and win.monitor) then return end
      if not g then
        -- new app: centred by Hyprland; keep its title bar below the top bar
        local top = top_limit(win.monitor)
        if win.at.y < top then
          hl.dispatch(hl.dsp.window.move({ x = win.at.x, y = top, window = sel }))
        end
        return
      end
      local mx, my, mw, mh = mon_box(win.monitor)
      local x = math.floor(mx + g[1] * mw)
      local y = math.max(top_limit(win.monitor), math.floor(my + g[2] * mh))
      -- Cascade: another window of the same app already at that spot would hide
      -- the new one exactly (looks as if it closed at once); step 32 px down/right.
      for _ = 1, 10 do
        local taken = false
        for _, o in ipairs(hl.get_windows() or {}) do
          if o.address ~= win.address and o.class == win.class and o.mapped
            and math.abs(o.at.x - x) < 16 and math.abs(o.at.y - y) < 16 then
            taken = true
            break
          end
        end
        if not taken then break end
        x, y = x + 32, y + 32
      end
      local h = math.min(math.floor(g[4] * mh), math.floor(my + mh - y))
      local wd = math.min(math.floor(g[3] * mw), math.floor(mx + mw - x))
      hl.dispatch(hl.dsp.window.resize({ x = wd, y = h, window = sel }))
      hl.dispatch(hl.dsp.window.move({ x = x, y = y, window = sel }))
    end, { timeout = 80, type = "oneshot" })
  end)
end

-- --- Scale floating windows when a monitor (the RDP output) changes size -------------
-- Hyprland pushes windows back on-screen before we hear about a resize, so the
-- geometry is snapshotted (as fractions of the monitor) while the size is stable
-- and restored from that snapshot afterwards. Scaling back up is then exact.
local last, snap = {}, {}

local function snapshot()
  local mons = {}
  for _, m in ipairs(hl.get_monitors() or {}) do
    local x, y, w, h = mon_box(m)
    mons[m.name] = { x, y, w, h }
    last[m.name] = last[m.name] or { x, y, w, h }
  end
  for _, w in ipairs(hl.get_windows() or {}) do
    local m = w.monitor and mons[w.monitor.name]
    local l = m and last[w.monitor.name]
    -- only while the monitor still has the size we last acted on
    if m and l and l[3] == m[3] and l[4] == m[4] and w.floating and w.fullscreen == 0 then
      snap[w.address] = { w.monitor.name, (w.at.x - m[1]) / m[3], (w.at.y - m[2]) / m[4],
                          w.size.x / m[3], w.size.y / m[4] }
    end
  end
end

-- dynamic: keep the per-app memory current even for windows that are never
-- closed (reboot, logout): write changed geometry every few seconds.
local ticks, dirty = 0, false
local function remember_open_windows()
  if mode ~= "dynamic" then return end
  for _, w in ipairs(hl.get_windows() or {}) do
    local g = snap[w.address]
    if g and w.class and w.class ~= "" and not w.class:find("%s") and not OWN_SIZE[w.class] then
      local cur = geom[w.class]
      local new = { g[2], g[3], g[4], g[5] }
      if not cur or math.abs(cur[1] - new[1]) + math.abs(cur[2] - new[2])
                     + math.abs(cur[3] - new[3]) + math.abs(cur[4] - new[4]) > 0.002 then
        geom[w.class] = new
        dirty = true
      end
    end
  end
  if dirty then save_geom(); dirty = false end
end

-- Push floating windows back below the bar once they have stopped moving
-- (a window that moved since the last tick may still be dragged).
local seen = {}
local function keep_below_bar()
  local mons, now = {}, {}
  for _, m in ipairs(hl.get_monitors() or {}) do mons[m.name] = m end
  for _, w in ipairs(hl.get_windows() or {}) do
    local m = w.monitor and mons[w.monitor.name]
    local pos = w.at.x .. "," .. w.at.y
    if m and w.floating and w.fullscreen == 0 and seen[w.address] == pos then
      local top = top_limit(m)
      if w.at.y < top then
        local sel = addr_sel(w)
        local avail = m.position.y + m.size.height / m.scale - top
        if w.size.y > avail then
          hl.dispatch(hl.dsp.window.resize({ x = w.size.x, y = math.floor(avail), window = sel }))
        end
        hl.dispatch(hl.dsp.window.move({ x = w.at.x, y = top, window = sel }))
      end
    end
    now[w.address] = pos
  end
  seen = now
end

snapshot()
hl.timer(function()
  keep_below_bar()
  snapshot()
  ticks = ticks + 1
  if ticks % 5 == 0 then remember_open_windows() end
end, { timeout = 1000, type = "repeat" })

hl.on("monitor.layout_changed", function()
  for _, m in ipairs(hl.get_monitors() or {}) do
    local nx, ny, nw, nh = mon_box(m)
    local o = last[m.name]
    last[m.name] = { nx, ny, nw, nh }
    if o and (o[3] ~= nw or o[4] ~= nh) then
      for _, w in ipairs(hl.get_windows() or {}) do
        local g = snap[w.address]
        if g and g[1] == m.name and w.floating and w.fullscreen == 0 then
          local sel = addr_sel(w)
          hl.dispatch(hl.dsp.window.resize({ x = math.max(200, math.floor(g[4] * nw)),
                                             y = math.max(120, math.floor(g[5] * nh)), window = sel }))
          hl.dispatch(hl.dsp.window.move({ x = math.floor(nx + g[2] * nw),
                                           y = math.max(top_limit(m), math.floor(ny + g[3] * nh)), window = sel }))
        end
      end
    end
  end
end)
