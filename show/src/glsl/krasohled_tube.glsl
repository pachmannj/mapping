// KRASOHLED 2.0 — milion bodů na zkrouceném tunelu (myšlenka: Tube SOP → Twist → body v textuře → Noise, Acrylicode)
// Průřez tunelu má n laloků (morf mezi n1 a n2), výška každého laloku = jedno z 12 frekvenčních pásem.
// Kopák pošle tunelem rázovou vlnu, body tunelem proudí směrem ke kameře.
// výstup: buffer 0 = poloha (xyz, velikost), buffer 1 = barva
uniform vec4 uK0;   // čas šumu, zkroucení, délka tunelu, poloměr
uniform vec4 uK1;   // laloky n1, n2, morf, hloubka laloků
uniform vec4 uK2;   // poloha rázové vlny (z), síla vlny, síla šumu, měřítko šumu
uniform vec4 uK3;   // natočení průřezu, odstín, míra barvy, posun po délce (proudění)
uniform vec4 uK4;   // jas, záblesk kopáku, -, -
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;   // 12 pásem → laloky
layout(location = 0) out vec4 oPos;
layout(location = 1) out vec4 oCol;

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
float lobv(float i) {                                  // jen desetinná čísla: převod NaN na int shodí Vulkan na Macu
	i = mod(clamp(i, 0., 11.), 12.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(i, 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
float lobes(float a, float n) {                       // laloky: hladké vrcholy, každý se svou výškou
	n = max(floor(n + .5), 1.);                        // pojistka: před prvním nastavením uniform je n = 0
	float seg = 6.2831853 / n, k = (a + seg * .5) / seg;
	float li = mod(floor(k), n), fr = fract(k) - .5;
	float shape = cos(fr * 3.14159); shape *= shape;
	return shape * (.35 + lobv(li) * 1.3);
}
vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }

void main() {
	vec2 uv = vUV.st;
	float v = fract(uv.y + uK3.w);                       // proudění bodů tunelem
	float z = (v - .5) * uK0.z;
	float a0 = uv.x * 6.2831853;
	float a = a0 + uK3.x + uK0.y * z;                    // zkroucení podél tunelu
	float L = mix(lobes(a0 + uK3.x, uK1.x), lobes(a0 + uK3.x, uK1.y), uK1.z);
	float r = uK0.w * (1. + uK1.w * L);
	float shock = uK2.y * exp(-pow((z - uK2.x) / .5, 2.));
	r *= 1. + shock;
	vec3 p = vec3(cos(a) * r, sin(a) * r, z);
	vec3 np = p * uK2.w + vec3(0., 0., uK0.x);
	p += vec3(snoise(np), snoise(np + 17.3), snoise(np + 41.7) * .5) * uK2.z * (1. + shock * 2.);
	float depthFade = smoothstep(0., .15, v) * smoothstep(1., .85, v);
	float lum = (.35 + L * .5 + shock * 2.) * depthFade * uK4.x;
	vec3 base = vec3(.55, .68, 1.);                      // původní modrobílá Krasohledu
	vec3 c = mix(base, hue(uK3.y + z * .05 + L * .2), uK3.z);
	c = mix(c, vec3(1.), clamp(shock * 1.5 + uK4.y, 0., 1.));
	oPos = vec4(p, 1. + shock * 1.5);
	oCol = vec4(c, clamp(lum, 0., 1.));
}
