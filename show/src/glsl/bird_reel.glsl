// PTÁK — styl „čtyři vrstvy dohromady“: šedé tělo s bílým obrysem, tyrkysové světelné stopy za pohybem,
// červeno-oranžový barevný lem posunutý proti pohybu a rastr z teček (halftone), který přichází s hudbou.
// vstup 0 = předchozí snímek (Feedback TOP), vstup 1 = vyříznutý pták (rgb předem vynásobené, a = maska)
// výstup 0 = stav stop (jde do Feedback TOP, bez rastru), výstup 1 = hotový pták: rgb předem vynásobené, a = krytí (pro 3D okno)
uniform vec4 uR0;   // směr stop x, y (v pixelech za snímek), útlum stop, síla stop
uniform vec4 uR1;   // posun barevného lemu (px), síla lemu, rastr (0–1), velikost tečky (px)
uniform vec4 uR2;   // jas těla, jas obrysu, odstín stop (0 = tyrkys), záblesk (kopák)
layout(location = 0) out vec4 oTrail;
layout(location = 1) out vec4 oCol;

vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }
vec3 hueRot(vec3 c, float a) {
	float y = dot(c, vec3(.299, .587, .114)), i = dot(c, vec3(.596, -.274, -.322)), q = dot(c, vec3(.211, -.523, .312));
	float ca = cos(a), sa = sin(a); float i2 = i * ca - q * sa, q2 = i * sa + q * ca;
	return max(vec3(y + .956 * i2 + .621 * q2, y - .272 * i2 - .647 * q2, y - 1.106 * i2 + 1.703 * q2), 0.);
}

void main() {
	vec2 res = uTDOutputInfo.res.zw, px = 1. / max(res, vec2(1.));
	vec2 uv = vUV.st;
	vec4 b = texture(sTD2DInputs[1], uv);
	float l = dot(b.rgb, vec3(.3, .5, .2));
	// obrys z gradientu masky
	float ax = texture(sTD2DInputs[1], uv + vec2(px.x * 1.5, 0.)).a - texture(sTD2DInputs[1], uv - vec2(px.x * 1.5, 0.)).a;
	float ay = texture(sTD2DInputs[1], uv + vec2(0., px.y * 1.5)).a - texture(sTD2DInputs[1], uv - vec2(0., px.y * 1.5)).a;
	float edge = clamp(length(vec2(ax, ay)) * 1.6, 0., 1.);
	// 1) tělo: šedé, kresba peří zůstane
	vec3 body = vec3(l * .9 + .05) * b.a * uR2.x;
	// 2) obrys: bílý s nádechem tyrkysu
	vec3 rim = mix(vec3(1.), vec3(.6, 1., .95), .3) * edge * uR2.y;
	// 3) barevný lem: maska posunutá proti směru pohybu, jen tam, kde pták není
	vec2 dir = normalize(uR0.xy + vec2(1e-5));
	float aOff = texture(sTD2DInputs[1], uv + dir * uR1.x * px).a;
	float aOff2 = texture(sTD2DInputs[1], uv + dir * uR1.x * 2. * px).a;
	vec3 fringe = (vec3(1., .25, .08) * max(aOff - b.a, 0.) + vec3(1., .6, .1) * max(aOff2 - aOff, 0.) * .7) * uR1.y;
	// 4) stopy: předchozí snímek posunutý ve směru stop, zbarvený do tyrkysu, s útlumem
	vec4 prev = texture(sTD2DInputs[0], uv - uR0.xy * px);
	vec3 teal = hueRot(vec3(.1, 1., .8), uR2.z * 6.2832);
	vec3 trail = mix(prev.rgb, teal * dot(prev.rgb, vec3(.33)) * 1.6, .25) * clamp(uR0.z, 0., .98);
	vec3 src = (edge * 1.2 + b.a * l * .5) * teal * uR0.w;   // stopy se rodí z obrysu a světlých míst
	vec3 trails = max(trail, src);
	vec3 col = max(trails, body + rim + fringe) + vec3(1.) * edge * uR2.w;
	// rastr z teček: velikost tečky podle jasu, tečky barvy obrazu
	if (uR1.z > .005) {
		float cs = max(uR1.w, 2.);
		vec2 cell = uv * res / cs;
		vec2 f = fract(cell) - .5;
		vec3 cc = texture(sTD2DInputs[1], (floor(cell) + .5) * cs * px).rgb;
		float lum = max(max(col.r, col.g), col.b);
		float r = sqrt(clamp(lum, 0., 1.)) * .62;
		float dot_ = 1. - smoothstep(r - .08, r + .08, length(f));
		col = mix(col, col * dot_ * 1.6, uR1.z);
	}
	float a = clamp(max(b.a, max(max(col.r, col.g), col.b)), 0., 1.);
	oTrail = vec4(trails, 1.);
	oCol = vec4(col, a);
}
