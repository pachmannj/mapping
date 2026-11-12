// MEMBRÁNA — vlnění plátna: vlnová rovnice (jako kůže bubnu), údery do ní pouští impulzy
// vstup 0 = předchozí stav (r = výška teď, g = výška minule)
uniform vec4 uW0;   // rychlost vln (c², ≤ 0,45), útlum, -, -
uniform vec4 uI0; uniform vec4 uI1; uniform vec4 uI2; uniform vec4 uI3;   // impulzy: x, y (0–1), síla, poloměr
out vec4 fragColor;

float imp(vec4 i, vec2 uv, float asp) {
	if (i.z == 0. || i.w <= 0.) return 0.;
	vec2 d = (uv - i.xy) * vec2(asp, 1.);
	return i.z * exp(-dot(d, d) / (i.w * i.w));
}

void main() {
	vec2 res = uTDOutputInfo.res.zw, px = 1. / max(res, vec2(1.));
	float asp = res.x / max(res.y, 1.);
	vec2 uv = vUV.st;
	vec4 s = texture(sTD2DInputs[0], uv);
	float h = s.r, hp = s.g;
	float lap = texture(sTD2DInputs[0], uv + vec2(px.x, 0.)).r + texture(sTD2DInputs[0], uv - vec2(px.x, 0.)).r
	          + texture(sTD2DInputs[0], uv + vec2(0., px.y)).r + texture(sTD2DInputs[0], uv - vec2(0., px.y)).r - 4. * h;
	float hn = (2. * h - hp + clamp(uW0.x, 0., .45) * lap) * clamp(uW0.y, 0., 1.);
	hn += imp(uI0, uv, asp) + imp(uI1, uv, asp) + imp(uI2, uv, asp) + imp(uI3, uv, asp);
	hn = clamp(hn, -1., 1.);
	if (hn != hn) hn = 0.;                             // NaN pojistka
	fragColor = vec4(hn, h, 0., 1.);
}
