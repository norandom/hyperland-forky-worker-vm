"""Private data (proprietary fonts, license keys) kept out of the public repo.

    uv run python privdata.py keygen    # new age key in ~/.config/age/keys.txt, added as recipient
    uv run python privdata.py seal      # private/  -> private.tar.age (commit this file)
    uv run python privdata.py open      # private.tar.age -> private/ (to edit, then seal again)

private/ is git-ignored; only the encrypted private.tar.age is committed. It is
encrypted (age, via pyrage) to every recipient in private.recipients: age keys
(age1...) or SSH public keys (ssh-ed25519 / ssh-rsa). Decryption uses the
identities in $PRIVATE_IDENTITY (colon-separated paths), else ~/.config/age/keys.txt
and ~/.ssh/id_ed25519 (unencrypted SSH keys only).

The deploy (tasks/private.py) uses private/ when it exists, otherwise decrypts
private.tar.age in memory. With neither, private data is skipped.
See private.example/ for the layout.
"""
import atexit
import io
import os
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

import pyrage
from pyrage import ssh, x25519

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / "private"
ARCHIVE = ROOT / "private.tar.age"
RECIPIENTS = ROOT / "private.recipients"
AGE_KEYS = Path.home() / ".config/age/keys.txt"


def _identity_paths():
    env = os.environ.get("PRIVATE_IDENTITY")
    if env:
        return [Path(p).expanduser() for p in env.split(":") if p]
    return [AGE_KEYS, Path.home() / ".ssh/id_ed25519"]


def identities():
    ids = []
    for path in _identity_paths():
        if not path.is_file():
            continue
        data = path.read_bytes()
        if b"AGE-SECRET-KEY-" in data:
            ids += [x25519.Identity.from_str(line.strip()) for line in data.decode().splitlines()
                    if line.startswith("AGE-SECRET-KEY-")]
        else:
            try:
                ids.append(ssh.Identity.from_buffer(data))
            except Exception:  # passphrase-protected or unsupported key type
                pass
    return ids


def recipients():
    out = []
    for line in RECIPIENTS.read_text().splitlines() if RECIPIENTS.exists() else []:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(x25519.Recipient.from_str(line) if line.startswith("age1") else ssh.Recipient.from_str(line))
    return out


def seal():
    recips = recipients()
    if not recips:
        sys.exit(f"no recipients in {RECIPIENTS.name} (run: uv run python privdata.py keygen)")
    if not PRIVATE.is_dir():
        sys.exit(f"{PRIVATE} does not exist")
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for p in sorted(PRIVATE.rglob("*")):
            if p.is_file():
                info = tar.gettarinfo(p, arcname=str(p.relative_to(PRIVATE)))
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = 0
                with p.open("rb") as f:
                    tar.addfile(info, f)
    ARCHIVE.write_bytes(pyrage.encrypt(buf.getvalue(), recips))
    print(f"{ARCHIVE.name}: {len(recips)} recipient(s), {ARCHIVE.stat().st_size} bytes")


def _extract(dest: Path):
    ids = identities()
    if not ids:
        raise RuntimeError("no identity found (see PRIVATE_IDENTITY in privdata.py)")
    data = pyrage.decrypt(ARCHIVE.read_bytes(), ids)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        tar.extractall(dest, filter="data")


def open_():
    if PRIVATE.exists() and "--force" not in sys.argv:
        sys.exit(f"{PRIVATE} exists; use --force to overwrite it from {ARCHIVE.name}")
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    _extract(PRIVATE)
    print(f"decrypted into {PRIVATE}")


def keygen():
    if AGE_KEYS.exists():
        key = next(l for l in AGE_KEYS.read_text().splitlines() if l.startswith("AGE-SECRET-KEY-"))
        pub = str(x25519.Identity.from_str(key).to_public())
        print(f"{AGE_KEYS} exists")
    else:
        ident = x25519.Identity.generate()
        pub = str(ident.to_public())
        AGE_KEYS.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        AGE_KEYS.touch(mode=0o600)
        AGE_KEYS.write_text(f"# public key: {pub}\n{ident}\n")
        print(f"new key: {AGE_KEYS} (back it up: without it private.tar.age can't be decrypted)")
    lines = RECIPIENTS.read_text().splitlines() if RECIPIENTS.exists() else []
    if pub not in lines:
        RECIPIENTS.write_text("\n".join(lines + [pub]) + "\n")
        print(f"added to {RECIPIENTS.name}: {pub}")


def load():
    """Directory with the private data for this deploy, or None."""
    if PRIVATE.is_dir():
        return PRIVATE
    if not ARCHIVE.exists():
        return None
    tmp = Path(tempfile.mkdtemp(prefix="debian-hypr-private-"))
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)
    try:
        _extract(tmp)
    except Exception as e:  # wrong key, no key: deploy the rest
        print(f"private data skipped: {ARCHIVE.name} could not be decrypted ({e})", file=sys.stderr)
        return None
    return tmp


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"seal": seal, "open": open_, "keygen": keygen}.get(cmd, lambda: sys.exit(__doc__))()
