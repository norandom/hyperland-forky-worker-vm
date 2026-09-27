#version 300 es
// Managed by debian-hypr. Night filter "green" (hypr-nightmode, the rabbit in the bar).
// Works in OKLab (perceptual): keeps the lightness contrast that makes text readable,
// caps the brightest white (less glare), reduces colourfulness, tints towards the mint of the film's screens and cuts blue.
precision highp float;
in vec2 v_texcoord;
uniform sampler2D tex;
out vec4 fragColor;

const float L_MIN = 0.10;      // lightness of black
const float L_MAX = 0.76;      // lightness of white (glare cap)
const float KEEP_CHROMA = 0.35;  // share of the original colourfulness
const vec2 TINT = vec2(-0.04470, 0.00515);   // OKLab (a, b) tint
const float BLUE_CAP = 0.80;   // blue at most this share of green

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSrgb(vec3 c) { return mix(12.92 * c, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

vec3 toOklab(vec3 rgb) {
    vec3 c = toLinear(rgb);
    vec3 lms = vec3(0.4122214708 * c.r + 0.5363325363 * c.g + 0.0514459929 * c.b,
                    0.2119034982 * c.r + 0.6806995451 * c.g + 0.1073969566 * c.b,
                    0.0883024619 * c.r + 0.2817188376 * c.g + 0.6299787005 * c.b);
    lms = pow(max(lms, vec3(0.0)), vec3(1.0 / 3.0));
    return vec3(0.2104542553 * lms.x + 0.7936177850 * lms.y - 0.0040720468 * lms.z,
                1.9779984951 * lms.x - 2.4285922050 * lms.y + 0.4505937099 * lms.z,
                0.0259040371 * lms.x + 0.7827717662 * lms.y - 0.8086757660 * lms.z);
}

vec3 fromOklab(vec3 lab) {
    vec3 lms = vec3(lab.x + 0.3963377774 * lab.y + 0.2158037573 * lab.z,
                    lab.x - 0.1055613458 * lab.y - 0.0638541728 * lab.z,
                    lab.x - 0.0894841775 * lab.y - 1.2914855480 * lab.z);
    lms = lms * lms * lms;
    vec3 c = vec3( 4.0767416621 * lms.x - 3.3077115913 * lms.y + 0.2309699292 * lms.z,
                  -1.2684380046 * lms.x + 2.6097574011 * lms.y - 0.3413193965 * lms.z,
                  -0.0041960863 * lms.x - 0.7034186147 * lms.y + 1.7076147010 * lms.z);
    return toSrgb(clamp(c, 0.0, 1.0));
}

void main() {
    vec4 px = texture(tex, v_texcoord);
    vec3 lab = toOklab(px.rgb);
    lab.x = L_MIN + (L_MAX - L_MIN) * lab.x;
    lab.yz = lab.yz * KEEP_CHROMA + TINT;
    vec3 rgb = fromOklab(lab);
    rgb.b = min(rgb.b, rgb.g * BLUE_CAP);
    fragColor = vec4(rgb, px.a);
}
