// KRASOHLED — vertex shader (port z webové verze)
// síť přehozená přes ikonu: zaoblený čtverec + kříž z laloků; čelní 2D pohled, reliéf jen ohýbá čáry
uniform vec4 uA;   // t, n1, n2, mix
uniform vec4 uB;   // rot, lobeR, ring, core
uniform vec4 uC;   // bulge, ripple, relief, aspect
uniform vec4 uD;   // treble, angle, scale, twist
uniform vec4 uE;   // freq, shockR, shockA, flux
uniform vec4 uF;   // pulse, flash, hue, colour
uniform vec4 uG;   // lobK, coreA, gain, -
uniform vec4 uL0;  // laloky 0–3
uniform vec4 uL1;  // laloky 4–7
uniform vec4 uL2;  // laloky 8–11

out Vertex { vec3 c; float a; } oVert;

float lobv(int i) {
  i = i % 12;
  vec4 v = i < 4 ? uL0 : (i < 8 ? uL1 : uL2);
  int j = i % 4;
  return j == 0 ? v.x : (j == 1 ? v.y : (j == 2 ? v.z : v.w));
}
float smin(float a, float b, float k) { float h = clamp(.5 + .5 * (b - a) / k, 0., 1.); return mix(b, a, h) - k * h * (1. - h); }
float sdRBox(vec2 p, vec2 b, float r) { vec2 q = abs(p) - b + r; return length(max(q, 0.)) + min(max(q.x, q.y), 0.) - r; }

float shapeH(vec2 p, float n) {
  float r = length(p), a = atan(p.y, p.x) + uB.x + uD.w * r, seg = 6.2831853 / n;
  float li = mod(floor((a + seg * .5) / seg), n);
  float fr = fract((a + seg * .5) / seg);
  int i0 = int(li), i1 = int(mod(li + 1., n)), i9 = int(mod(li - 1. + n, n));
  float amp = lobv(i0) + (lobv(i1) - lobv(i0)) * smoothstep(.75, 1., fr) * .5 + (lobv(i9) - lobv(i0)) * smoothstep(.25, 0., fr) * .5;
  a = mod(a + seg * .5, seg) - seg * .5;
  vec2 q = r * vec2(cos(a), sin(a));
  float dl = length(q - vec2(uB.z, 0.)) - uB.y;
  float dx = smin(dl, r - uB.w, .22);
  float dome = clamp(-dx / (uB.y + .08), 0., 1.);
  float ripple = sin(q.x * 16. * uE.x - uA.x * 2.1) * cos(abs(q.y) * 13. * uE.x + uA.x * 1.3);
  float core = smoothstep(uB.w + .1, 0., r);
  float lob = 1. + uG.x * (amp - .35) + uG.y * core;
  return uC.x * lob * sin(dome * 1.5707963) * .42 + uC.y * .045 * ripple * (1. - dome * .6);
}
float H(vec2 p) {
  float box = sdRBox(p, vec2(.95), .28);
  float plate = smoothstep(.0, -.08, box);
  float h = mix(shapeH(p, uA.y), shapeH(p, uA.z), uA.w) * plate + .06 * plate;
  float r = length(p), x = (r - uE.y) * 7.;
  h += uE.z * sin((r - uE.y) * 34.) * exp(-x * x) * plate;
  h += uE.w * .035 * sin(p.x * 61. + uA.x * 9.) * sin(p.y * 57. - uA.x * 7.) * plate;
  return h * uC.z;
}
void main() {
  float c = cos(uD.y), s = sin(uD.y);
  vec2 p = mat2(c, -s, s, c) * P.xy;
  float box = sdRBox(p, vec2(.95), .28);
  float h = H(p);
  float e = .012;
  vec2 g = vec2(H(p + vec2(e, 0.)) - H(p - vec2(e, 0.)), H(p + vec2(0., e)) - H(p - vec2(0., e))) / (2. * e);
  vec3 n = normalize(vec3(-g, 1.));
  g /= 1. + length(g) * .7;
  float sh = .25 + .75 * max(dot(n, normalize(vec3(-.5, .6, .8))), 0.);
  vec3 lo = vec3(.235, .373, .667), hi = vec3(.88, .9, .96);
  float lv = clamp(sh * (.55 + h * 1.4) + uD.x * .25, 0., 1.);
  vec3 base = mix(lo, hi, lv);
  float hh = uF.z + h * .35 + length(p) * .18 + sh * .08;
  vec3 k = clamp(abs(mod(hh * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.);
  vec3 col = mix(vec3(1.), k, .72) * (.3 + lv * .95);
  oVert.c = mix(base, col, uF.w) * (1. + uF.y) * uG.z;
  oVert.a = smoothstep(.02, -.04, box);
  float hc = min(h, 1.9);
  vec2 q = p - g * .085 * (.6 + hc) + p * hc * .22;
  gl_Position = vec4(q.x * uD.z * (1. + uF.x) / uC.w, q.y * uD.z * (1. + uF.x), 0., 1.);
}
