// KRASOHLED — post: krasohledové zrcadlení obrazu, chromatická aberace, záře, vinětace, zrno, záblesk
// vstup 0 = render, vstup 1 = rozmazaná záře, vstup 2 = stopy (zpětná vazba)
uniform vec4 uQ0;   // segmenty krasohledu, míra krasohledu, chromatická aberace, záře
uniform vec4 uQ1;   // vinětace, zrno, záblesk, čas
uniform vec4 uQ2;   // poměr stran, natočení krasohledu, expozice, síla stop
out vec4 fragColor;

float hash(vec2 p) { p = fract(p * vec2(443.897, 441.423)); p += dot(p, p.yx + 19.19); return fract((p.x + p.y) * p.x); }
vec2 kal(vec2 uv, float n, float rot) {
  vec2 p = uv - .5; p.x *= uQ2.x;
  float r = length(p), a = atan(p.y, p.x) + rot, seg = 6.2831853 / n;
  a = mod(a, seg); a = abs(a - seg * .5);
  p = r * vec2(cos(a), sin(a)); p.x /= uQ2.x;
  return p + .5;
}
vec3 scene(vec2 uv) { return texture(sTD2DInputs[0], uv).rgb + texture(sTD2DInputs[2], uv).rgb * uQ2.w; }
vec3 sampleCA(vec2 uv, float ca) {
  vec2 d = (uv - .5) * ca;
  return vec3(scene(uv + d).r, scene(uv).g, scene(uv - d).b);
}
void main() {
  vec2 uv = vUV.st;
  vec3 col = sampleCA(uv, uQ0.z);
  if (uQ0.y > .001) {
    vec2 ku = kal(uv, max(uQ0.x, 2.), uQ2.y);
    col = mix(col, sampleCA(ku, uQ0.z), uQ0.y);
  }
  col += texture(sTD2DInputs[1], uv).rgb * uQ0.w;
  vec2 p = uv - .5; p.x *= uQ2.x;
  col *= 1. - uQ1.x * smoothstep(.35, 1.1, length(p));
  col = 1. - exp(-col * uQ2.z);                          // filmové tónování: jas se nepřepálí do bílé
  col = pow(col, vec3(1.35));                             // hlubší černé, výraznější kresba
  col += (hash(uv * 1024. + uQ1.w) - .5) * uQ1.y;
  col += uQ1.z;
  fragColor = TDOutputSwizzle(vec4(max(col, 0.), 1.));
}
