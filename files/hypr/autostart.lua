-- Managed by debian-hypr. Started once per Hyprland start (not on reload).
-- waybar runs as the Debian package's user service (graphical-session.target).
hl.on("hyprland.start", function()
  -- Autologin starts the session on the Proxmox console: locked until RDP logs in
  -- (hypr-rdp-session unlocks) or someone types the password at the console.
  hl.exec_cmd('[ -e "$XDG_RUNTIME_DIR/hypr-rdp-active" ] || hyprlock')
  hl.exec_cmd("uwsm app -- mako")
  -- hyprbars is loaded after the first config pass; reload once so
  -- decorations.lua can configure it.
  hl.exec_cmd("sleep 1 && hyprctl reload")
  -- Fixedsys as core X fonts for NEdit (Xwayland font path)
  hl.exec_cmd("$HOME/.local/bin/hypr-xfonts")
end)
