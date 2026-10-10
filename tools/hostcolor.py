#!/usr/bin/env python3
"""Which VM am I on? One colour per hostname for the window decorations.

The hue comes from a hash of the hostname (stable for the life of the VM); lightness and
chroma are fixed in OKLCH, so every host's colour carries the same weight, and lightness is
lowered until white text keeps a WCAG contrast of at least 4.6 (AA is 4.5).

    python3 tools/hostcolor.py debb vm2 vm3     # as fleet_hosts, in order; warns for hues < 30° apart

Hosts listed in group_data's fleet_hosts get their hue from their position (golden angle from
debb's hue: the first 8 are clearly apart); unlisted hosts fall back to the hash, which can land
close to another host. decor_colors = {"vm2": "#5a3fa0"} overrides one host by hand.
"""
import hashlib
import math
import sys

MIN_CONTRAST = 4.6    # white text on the colour
TOO_CLOSE = 30        # degrees of hue


def _srgb(c):  # linear -> gamma encoded, 0..1
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def oklch_to_rgb(L, C, h):
    """OKLCH -> linear sRGB (Björn Ottosson's matrices); None when out of gamut."""
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
           -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
           -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return rgb if all(-1e-4 <= c <= 1 + 1e-4 for c in rgb) else None


def in_gamut(L, h, C=0.14):
    """The most saturated colour of that lightness and hue that sRGB can show."""
    while C > 0:
        rgb = oklch_to_rgb(L, C, h)
        if rgb:
            return rgb
        C -= 0.005
    return oklch_to_rgb(L, 0, h)


def luminance(rgb):  # WCAG relative luminance, linear channels
    r, g, b = (min(1, max(0, c)) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(rgb, other=(1.0, 1.0, 1.0)):
    a, b = luminance(rgb) + 0.05, luminance(other) + 0.05
    return max(a, b) / min(a, b)


def to_hex(rgb):
    return "".join(f"{round(min(1, max(0, _srgb(c))) * 255):02x}" for c in rgb)


def hue_of(hostname):
    return int.from_bytes(hashlib.sha256(hostname.encode()).digest()[:4], "big") % 360


BASE_HUE = 224        # debb's hash hue: slot 0 keeps the colour it had
GOLDEN = 137.508


def host_hue(hostname, fleet=()):
    if hostname in fleet:
        return round(BASE_HUE + list(fleet).index(hostname) * GOLDEN) % 360
    return hue_of(hostname)


def color_for(hostname, override=None, fleet=()):
    """{'hex', 'pale', 'hue', 'contrast'}: hex = the host colour (bars, borders; white text),
    pale = a light tint of the same hue for light bars (dark navy text)."""
    hue = host_hue(hostname, fleet)
    if override:
        hx = override.lstrip("#")
        rgb = tuple(_linear(int(hx[i:i + 2], 16) / 255) for i in (0, 2, 4))
        L = 0.47
    else:
        L = 0.47
        rgb = in_gamut(L, hue)
        while contrast(rgb) < MIN_CONTRAST and L > 0.2:
            L -= 0.01
            rgb = in_gamut(L, hue)
    pale = in_gamut(0.93, hue, 0.035)
    return {"hex": to_hex(rgb), "pale": to_hex(pale), "hue": hue, "contrast": round(contrast(rgb), 1),
            "pale_contrast": round(contrast(pale, (_linear(0x2b / 255), _linear(0x45 / 255), _linear(0x70 / 255))), 1)}


def main(names):
    cols = {n: color_for(n, fleet=names) for n in names}  # the names in fleet_hosts order
    for n, c in cols.items():
        print(f"{n:16} #{c['hex']}  hue {c['hue']:3}  white text {c['contrast']}:1   pale #{c['pale']} navy text {c['pale_contrast']}:1")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = abs(cols[a]["hue"] - cols[b]["hue"])
            d = min(d, 360 - d)
            if d < TOO_CLOSE:
                print(f"too close: {a} and {b} ({d}° apart): give one an override, decor_colors in group_data")


if __name__ == "__main__":
    main(sys.argv[1:] or ["debb"])
