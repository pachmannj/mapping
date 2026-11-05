// HEAT — cihlová mřížka čtverců: 3D simplex šum + vlny z úderů (port z heat_ndex.html)
uniform vec4 uH0;   // čas šumu, počet řad cihel, jas, práh (odřízne tmavé cihly → čisté plátno)
uniform vec4 uH1;   // kontrast šumu, poloměr vln (px), odstín, míra barvy
uniform vec4 uR0; uniform vec4 uR1; uniform vec4 uR2; uniform vec4 uR3;   // vlny: x, y (px), čas od úderu, síla
uniform vec4 uR4; uniform vec4 uR5; uniform vec4 uR6; uniform vec4 uR7;
out vec4 fragColor;

// simplex šum 3D (Ashima Arts / Stefan Gustavson, MIT)
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
float ripple(vec4 r, vec2 p) {
	if (r.w <= 0.) return 0.;
	float d = length(p - r.xy), R = uH1.y;
	return cos(d / (R * .2) - r.z * 6.) * .7 * r.w * exp(-d * d / (R * R)) * exp(-r.z * 1.2);
}
vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }

void main() {
	vec2 res = uTDOutputInfo.res.zw;
	vec2 px = vec2(vUV.s, 1. - vUV.t) * res;
	float bs = floor(res.y / uH0.y);
	float row = floor(px.y / bs);
	bool odd = mod(row, 2.) > .5;
	float off = odd ? -bs * .5 : 0.;
	float col = floor((px.x - off) / bs);
	vec2 o = vec2(off + col * bs, row * bs);
	vec2 ctr = o + bs * .5, inb = px - o;
	float colEff = odd ? col - .5 : col;
	float n = (snoise(vec3(colEff * .04, row * .04, uH0.x * .3)) + 1.) * .5;
	float shade = clamp(.5 + (n - .5) * 1.2 * uH1.x, 0., 1.);
	shade += ripple(uR0, ctr) + ripple(uR1, ctr) + ripple(uR2, ctr) + ripple(uR3, ctr);
	shade += ripple(uR4, ctr) + ripple(uR5, ctr) + ripple(uR6, ctr) + ripple(uR7, ctr);
	shade = clamp((shade - uH0.w) / max(1. - uH0.w, .01), 0., 1.);
	float stroke = step(1., inb.x) * step(1., inb.y) * step(inb.x, bs - 1.) * step(inb.y, bs - 1.);
	vec3 c = mix(vec3(1.), hue(uH1.z + shade * .2), uH1.w);
	fragColor = TDOutputSwizzle(vec4(c * shade * stroke * uH0.z, 1.));
}
