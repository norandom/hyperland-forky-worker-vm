# The away lock

The VM is a thin client for day-to-day work over RDP, with agents that keep working while you're
away. While you're connected, you're the pro and nothing changes; while you're not, `hypr-away`
(root, `files/sbin/hypr-away`) takes the keys away.

## What locks

You are the pro while you're connected: nothing changes. When the RDP session is gone for
10 minutes (`away_grace_seconds`), `hypr-away` (root) locks:

* `sudo` asks for your password: agents still running on lose root
* `ptrace_scope=1`: processes can't read each other's memory

Reconnect and it unlocks within seconds. "Connected" means a session from another machine,
served by the real `/usr/bin/hypr-rdp`, with picture data flowing, so a bare TCP connect
without the password, or a connection a local process makes itself, doesn't count.
`sudo journalctl -u hypr-away` shows every lock and unlock.

## What it does and doesn't stop

| | |
|---|---|
| ✅ unattended agents doing something unplanned while you're away | no sudo |
| ⚠️ malware while you're connected | you have passwordless sudo then, and that is root |
| ⚠️ the RDP password | stored in plain text in `~/.config/hypr-rdp/password`. Keep it different from your login password |
