-- Managed by debian-hypr. Started once per Hyprland start (not on reload).
-- waybar runs as the Debian package's user service (graphical-session.target).
hl.on("hyprland.start", function()
  hl.exec_cmd("uwsm app -- mako")
  -- hyprbars is loaded after the first config pass; reload once so
  -- decorations.lua can configure it.
  hl.exec_cmd("sleep 1 && hyprctl reload")
end)
