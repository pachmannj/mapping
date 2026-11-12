// PTÁK — časová mapa pro slit-scan (Time Machine TOP): jas pixelu = jak daleko do minulosti se pro něj sáhne.
// Vzory: 0 = od těla ven (křídla se táhnou za tělem), 1 = podél rozpětí, 2 = proudící šum, 3 = svislé skenování
uniform vec4 uT0;   // vzor (0–3, plynule), čas, střed ptáka x, y (0–1)
uniform vec4 uT1;   // osa rozpětí x, y, poměr stran, -
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

void main() {
	float asp = max(uT1.z, .1);
	vec2 p = (vUV.st - uT0.zw) * vec2(asp, 1.);
	vec2 u = normalize(uT1.xy + vec2(1e-5, 0.));
	float v0 = clamp(length(p) / .7, 0., 1.);
	float v1 = clamp(abs(dot(p, u)) / .6, 0., 1.);
	float v2 = snoise(vec3(p * 2.2, uT0.y * .25)) * .5 + .5;
	float v3 = vUV.t;
	float k = clamp(uT0.x, 0., 3.);
	float v = mix(mix(v0, v1, clamp(k, 0., 1.)), mix(v2, v3, clamp(k - 2., 0., 1.)), clamp(k - 1., 0., 1.));
	fragColor = vec4(vec3(clamp(v, 0., 1.)), 1.);
}
