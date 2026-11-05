// KRASOHLED — zpětná vazba: předchozí snímek se přiblíží, pootočí, zvlní, zeslábne a posune barvu
// vstup 0 = předchozí výstup (Feedback TOP), vstup 1 = aktuální render, vstup 2 = pohyb z kamery
uniform vec4 uF0;   // útlum (0–1), zoom, rotace, posun odstínu
uniform vec4 uF1;   // zvlnění, čas, poměr stran, síla nového snímku
uniform vec4 uF2;   // síla kamery, odstín kamery, -, -
out vec4 fragColor;

vec3 hueRot(vec3 c, float a) {
  float y = dot(c, vec3(.299, .587, .114)), i = dot(c, vec3(.596, -.274, -.322)), q = dot(c, vec3(.211, -.523, .312));
  float ca = cos(a), sa = sin(a); float i2 = i * ca - q * sa, q2 = i * sa + q * ca;
  return vec3(y + .956 * i2 + .621 * q2, y - .272 * i2 - .647 * q2, y - 1.106 * i2 + 1.703 * q2);
}
void main() {
  vec2 uv = vUV.st - .5; uv.x *= uF1.z;
  float c = cos(uF0.z), s = sin(uF0.z);
  uv = mat2(c, -s, s, c) * uv / uF0.y;
  uv += uF1.x * .012 * vec2(sin(uv.y * 9. + uF1.y), cos(uv.x * 8. - uF1.y * 1.2));
  uv.x /= uF1.z; uv += .5;
  vec3 prev = texture(sTD2DInputs[0], uv).rgb * uF0.x;
  prev = max(hueRot(prev, uF0.w), 0.);
  vec3 base = texture(sTD2DInputs[1], vUV.st).rgb;
  float l = dot(base, vec3(.299, .587, .114));
  vec3 hi = base * smoothstep(.75, 1.5, l) * uF1.w;      // do stopy jdou jen nejjasnější hrany a částice
  float m = texture(sTD2DInputs[2], vec2(1. - vUV.s, vUV.t)).r * uF2.x;   // zrcadlený pohyb tanečníků / DJe
  vec3 mc = m * (.5 + .5 * cos(6.2831853 * (uF2.y + vec3(0., .33, .67))));
  fragColor = TDOutputSwizzle(vec4(max(prev, hi) + mc, 1.));
}
