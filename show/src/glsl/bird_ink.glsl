// PTÁK — inkoust / kouř: obrys ptáka se vpouští do zpětné vazby, kterou unáší proudící šumové pole.
// vstup 0 = předchozí snímek (Feedback TOP), vstup 1 = pták s máchnutím (barva + maska)
uniform vec4 uI0;   // čas, rychlost proudění, útlum, síla vpouštění
uniform vec4 uI1;   // odstín, sytost, poměr stran, měřítko víření
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
vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }

void main() {
	vec2 res = uTDOutputInfo.res.zw, px = 1. / max(res, vec2(1.));
	float asp = max(uI1.z, .1);
	vec2 uv = vUV.st, p = (uv - .5) * vec2(asp, 1.);
	// proudění bez zdrojů: gradient šumu otočený o 90°
	const float e = .02;
	float sc = uI1.w, t = uI0.x * .15;
	float n0 = snoise(vec3(p * sc, t)), nx = snoise(vec3((p + vec2(e, 0.)) * sc, t)), ny = snoise(vec3((p + vec2(0., e)) * sc, t));
	vec2 flow = vec2(ny - n0, -(nx - n0)) / e;
	vec2 back = uv - flow * uI0.y * px * 6.;
	vec3 prev = texture(sTD2DInputs[0], back).rgb * clamp(uI0.z, 0., .995);
	vec4 b = texture(sTD2DInputs[1], uv);
	float ax = texture(sTD2DInputs[1], uv + vec2(px.x, 0.)).a - texture(sTD2DInputs[1], uv - vec2(px.x, 0.)).a;
	float ay = texture(sTD2DInputs[1], uv + vec2(0., px.y)).a - texture(sTD2DInputs[1], uv - vec2(0., px.y)).a;
	float edge = clamp(length(vec2(ax, ay)) * 2., 0., 1.);
	vec3 ink = mix(vec3(1.), hue(uI1.x + edge * .15), uI1.y) * (edge + b.a * .08) * uI0.w;
	fragColor = TDOutputSwizzle(vec4(max(prev, ink), 1.));
}
