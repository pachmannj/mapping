// ECHOES — tečkový rastr: Perlinův šum + vlny z úderů (port z echoes_index.html)
// Místo kliknutí myší vlny spouští kopák (střed) a virbl (náhodné místo), místo myši bloudí bod řízený basou.
uniform vec4 uE0;   // čas šumu, rozestup teček (px), jas, práh (odřízne slabé tečky → čisté plátno)
uniform vec4 uE1;   // bloudící bod x, y (px), síla vlny od basy, čas vlny
uniform vec4 uE2;   // odstín, míra barvy, kontrast šumu, -
uniform vec4 uR0; uniform vec4 uR1; uniform vec4 uR2; uniform vec4 uR3;   // vlny: x, y (px), čas od úderu, síla
uniform vec4 uR4; uniform vec4 uR5; uniform vec4 uR6; uniform vec4 uR7;
out vec4 fragColor;

vec2 g2(vec2 p) { p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3))); return -1. + 2. * fract(sin(p) * 43758.5453); }
float perlin(vec2 p) {
	vec2 i = floor(p), f = fract(p), u = f * f * f * (f * (f * 6. - 15.) + 10.);
	return mix(mix(dot(g2(i), f), dot(g2(i + vec2(1, 0)), f - vec2(1, 0)), u.x),
	           mix(dot(g2(i + vec2(0, 1)), f - vec2(0, 1)), dot(g2(i + vec2(1, 1)), f - vec2(1, 1)), u.x), u.y) * 1.4;
}
float pulse(vec4 r, vec2 p, float k) {
	if (r.w <= 0.) return 0.;
	float d = length(p - r.xy) / k;
	return sin((d - 200. * r.z) * .05) * r.w * exp(-d * .003) * exp(-r.z * 1.);
}
vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }

void main() {
	vec2 res = uTDOutputInfo.res.zw, px = vUV.st * res;
	float k = res.x / 1440.;                                   // měřítko vůči původní webové verzi
	float sp = uE0.y * k;
	vec2 cell = floor(px / sp), ctr = (cell + .5) * sp;
	vec2 q = ctr / k;
	float v = (perlin(q * .002 + uE0.x * .2) + 1.) * .5;
	v = .5 + (v - .5) * uE2.z;
	v += pulse(uR0, ctr, k) + pulse(uR1, ctr, k) + pulse(uR2, ctr, k) + pulse(uR3, ctr, k);
	v += pulse(uR4, ctr, k) + pulse(uR5, ctr, k) + pulse(uR6, ctr, k) + pulse(uR7, ctr, k);
	float dm = length(ctr - uE1.xy) / k;
	v += sin((dm - 150. * uE1.w) * .02) * uE1.z * exp(-dm * .002);
	v = clamp((v - uE0.w) / max(1. - uE0.w, .01), 0., 1.);
	float maxR = sp * .5, rad = v * maxR;
	if (rad < maxR * .1) rad = maxR * .1 * v;
	float d = length(px - ctr);
	float a = 1. - smoothstep(rad - .75, rad + .75, d);
	vec3 col = mix(vec3(1.), hue(uE2.x + v * .15), uE2.y);
	fragColor = TDOutputSwizzle(vec4(col * a * uE0.z, 1.));
}
