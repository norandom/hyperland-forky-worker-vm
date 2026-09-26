"""Optional GRUB password. Only runs when GRUB_PASSWORD is set locally:

    GRUB_PASSWORD='...' .venv/bin/pyinfra inventory.py tasks/grub_password.py

Normal boot stays unattended (entries are --unrestricted); editing entries or
opening the GRUB console needs the password. The PBKDF2 hash is computed here,
so the plain password never reaches the host.
"""
import hashlib
import os
from io import StringIO

from pyinfra import host
from pyinfra.operations import files, server

password = os.environ.get("GRUB_PASSWORD")

if password:
    salt = hashlib.sha256(host.name.encode() + b"debian-hypr-grub").digest()  # stable per host
    iterations = 10000
    digest = hashlib.pbkdf2_hmac("sha512", password.encode(), salt, iterations, 64)
    pbkdf2 = f"grub.pbkdf2.sha512.{iterations}.{salt.hex().upper()}.{digest.hex().upper()}"
    su = host.data.grub_superuser

    pw = files.put(
        name="GRUB superuser + password hash",
        src=StringIO(f"""#!/bin/sh
# Managed by debian-hypr
cat <<'GRUBEOF'
set superusers="{su}"
password_pbkdf2 {su} {pbkdf2}
GRUBEOF
"""),
        dest="/etc/grub.d/01_password",
        mode="755",
        _sudo=True,
    )
    unrestricted = files.line(
        name="Boot entries stay bootable without the password",
        path="/etc/grub.d/10_linux",
        line=r'^CLASS="--class gnu-linux --class gnu --class os"$',
        replace='CLASS="--class gnu-linux --class gnu --class os --unrestricted"',
        _sudo=True,
    )
    server.shell(
        name="update-grub",
        commands=["update-grub"],
        _sudo=True,
        _if=lambda: pw.did_change() or unrestricted.did_change(),
    )
