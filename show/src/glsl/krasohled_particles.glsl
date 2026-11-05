// KRASOHLED — GPU částice: stav v textuře (xy = poloha, z = rychlost ven, w = život)
// každý pixel = jedna částice; vstup 0 = předchozí stav (zpětná vazba)
uniform vec4 uP0;   // čas, dt, šance zrodu, kopák
uniform vec4 uP1;   // rotace laloků, počet laloků, poloměr prstence, poloměr laloku
uniform vec4 uP2;   // rychlost proudění, víření, hustota hudby, síla tahu ke středu
out vec4 fragColor;

float hash(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }

vec2 flow(vec2 p, float t) {
  float a = sin(p.x * 2.7 + t * .41) * 1.7 + cos(p.y * 3.1 - t * .33) * 1.5 + sin((p.x + p.y) * 1.3 + t * .17) * 1.2;
  return vec2(cos(a), sin(a));
}

void main() {
  vec4 s = texture(sTD2DInputs[0], vUV.st);
  vec2 p = s.xy; float out_ = s.z, life = s.w;
  float t = uP0.x, dt = uP0.y;
  float h1 = hash(vUV.st * 913.1 + fract(t * .37)), h2 = hash(vUV.st * 37.7 + fract(t * .11) + 2.3), h3 = hash(vUV.st * 71.3 + 9.1);
  life -= dt * (.18 + h3 * .35);
  if (life <= 0.) {
    if (h1 < uP0.z) {                                    // zrození na jednom z laloků
      float n = max(uP1.y, 1.);
      float k = floor(h2 * n);
      float ang = (k + 0.) * 6.2831853 / n - uP1.x;
      vec2 c = uP1.z * vec2(cos(ang), sin(ang));
      float ra = h3 * 6.2831853, rr = uP1.w * sqrt(hash(vUV.st + t));
      p = c + rr * vec2(cos(ra), sin(ra));
      life = .6 + h3 * .6;
      out_ = .2 + uP0.w * 2.5 * (.5 + h2);                // kopák vystřelí částice ven
    } else { p = vec2(99.); life = 0.; }
  } else {
    vec2 v = flow(p * (1. + uP2.z), t) * uP2.x;
    vec2 perp = vec2(-p.y, p.x);
    v += perp * uP2.y;                                    // víření kolem středu
    v += normalize(p + 1e-4) * out_;                      // výstřel ven
    v -= p * uP2.w;                                       // tah zpět ke středu
    p += v * dt;
    out_ *= exp(-dt * 2.2);
  }
  fragColor = vec4(p, out_, life);
}
