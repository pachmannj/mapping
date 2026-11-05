// ECHOES 2.0 — zdrojové pole pro bílé linky (myšlenka: Noise → Edge → feedback → Limit → Displace, Daniel Steenhoff)
// Z webové verze zůstává logika ozvěn: kopák = vlna ze středu, virbl = vlna z náhodného místa,
// basa = vlnění kolem bloudícího bodu. Výstup je hladké šedé pole; linky z něj dělá řetězec Edge TOPů.
uniform vec4 uE0;   // čas šumu, perioda šumu, exponent, síla šumu
uniform vec4 uE1;   // bloudící bod x, y (0–1), síla vlny od basy, čas vlny
uniform vec4 uE2;   // posun šumu x, -, -, -
uniform vec4 uR0; uniform vec4 uR1; uniform vec4 uR2; uniform vec4 uR3;   // vlny: x, y (0–1), čas od úderu, síla
uniform vec4 uR4; uniform vec4 uR5; uniform vec4 uR6; uniform vec4 uR7;
out vec4 fragColor;

vec4 perm(vec4 x) { return mod(((x * 34.) + 1.) * x, 289.); }
float snoise(vec3 v) {
	const vec2 C = vec2(1. / 6., 1. / 3.);
	vec3 i = floor(v + dot(v, C.yyy)), x0 = v - i + dot(i, C.xxx);
	vec3 g = step(x0.yzx, x0.xyz), l = 1. - g, i1 = min(g.xyz, l.zxy), i2 = max(g.xyz, l.zxy);
	vec3 x1 = x0 - i1 + C.xxx, x2 = x0 - i2 + C.yyy, x3 = x0 - .5;
	i = mod(i, 289.);
	vec4 p = perm(perm(perm(i.z + vec4(0., i1.z, i2.z, 1.)) + i.y + vec4(0., i1.y, i2.y, 1.)) + i.x + vec4(0., i1.x, i2.x, 1.));
	vec4 j = p - 49. * floor(p / 49.), x_ = floor(j / 7.), y_ = floor(j - 7. * x_);
	vec4 x = (x_ * 2. + .5) / 7. - 1., y = (y_ * 2. + .5) / 7. - 1., h = 1. - abs(x) - abs(y);
	vec4 b0 = vec4(x.xy, y.xy), b1 = vec4(x.zw, y.zw), s0 = floor(b0) * 2. + 1., s1 = floor(b1) * 2. + 1., sh = -step(h, vec4(0.));
	vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy, a1 = b1.xzyw + s1.xzyw * sh.zzww;
	vec3 p0 = vec3(a0.xy, h.x), p1 = vec3(a0.zw, h.y), p2 = vec3(a1.xy, h.z), p3 = vec3(a1.zw, h.w);
	vec4 nr = 1.79284291400159 - .85373472095314 * vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3));
	p0 *= nr.x; p1 *= nr.y; p2 *= nr.z; p3 *= nr.w;
	vec4 m = max(.6 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.);
	m = m * m;
	return 42. * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}
float ring(vec4 r, vec2 p) {                          // ozvěna: kruhová vlna, která se šíří a slábne
	if (r.w <= 0.) return 0.;
	float d = length(p - r.xy);
	float front = r.z * .45;
	return r.w * exp(-pow((d - front) / .035, 2.)) * exp(-r.z * .9) + r.w * .35 * sin((d - front) * 40.) * exp(-abs(d - front) * 12.) * exp(-r.z * 1.2);
}

void main() {
	vec2 res = uTDOutputInfo.res.zw;
	vec2 p = (vUV.st - .5) * vec2(res.x / res.y, 1.);
	float n = snoise(vec3(p / uE0.y + vec2(uE2.x, 0.), uE0.x)) * .5 + .5;
	float v = pow(n, uE0.z) * uE0.w;
	v += ring(uR0, p) + ring(uR1, p) + ring(uR2, p) + ring(uR3, p) + ring(uR4, p) + ring(uR5, p) + ring(uR6, p) + ring(uR7, p);
	vec2 m = (uE1.xy - .5) * vec2(res.x / res.y, 1.);
	float dm = length(p - m);
	v += sin(dm * 25. - uE1.w * 4.) * uE1.z * exp(-dm * 2.5);
	fragColor = TDOutputSwizzle(vec4(vec3(clamp(v, 0., 1.5)), 1.));
}
