-- Managed by debian-hypr.
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })

-- hypr-rdp sizes its headless output to the RDP client at runtime. A config
-- reload would re-apply the rule above to it (wrong size), so re-assert the
-- last size recorded by hypr-rdp-modecache.service.
local runtime = os.getenv("XDG_RUNTIME_DIR") or "/tmp"
local cache = io.open(runtime .. "/hypr-rdp-mode", "r")
if cache then
  local mode, scale, position = (cache:read("*l") or ""):match("^(%S+) (%S+) (%S+)$")
  cache:close()
  if mode then
    hl.monitor({ output = "hypr-rdp", mode = mode, scale = tonumber(scale), position = position })
  end
end

-- While an RDP session is active (flag from hypr-rdp-cursor), keep the unused
-- Proxmox console output off across config reloads.
local active = io.open(runtime .. "/hypr-rdp-active", "r")
if active then
  active:close()
  hl.monitor({ output = "Virtual-1", disabled = true })
end
