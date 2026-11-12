// KVĚT — Časová socha: všech 64 fází rozkvětu naskládaných do hloubky a promítnutých paprsky jako jeden svítící objem.
// Čas je třetí rozměr: obrys květu v každé z 28 fází je svítící vrstva, dohromady tunel / socha celého rozkvětu.
// Vrstva „teď“ (aktuální rozkvět) je plná lilie uvnitř sochy, vrstvy za ní zakrývá. Každá časová vrstva dýchá podle svého frekvenčního pásma, kopák sochu natáhne.
// vstup 0 = Texture 3D se všemi fázemi
uniform vec4 uV0;   // přítomnost (fáze 0–1), hloubka socha, natočení kamery (rad), váha looku
uniform vec4 uV1;   // střed květu x, y, poloměr výřezu, poměr stran
uniform vec4 uV2;   // odstín, zbarvení času, hustota, jas
uniform vec4 uV3;   // náklon kamery (rad), ostrost přítomnosti, zoom, -
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;
out vec4 fragColor;

float band(float i) {
	i = clamp(i, 0., 11.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(i, 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
float bandS(float x) { x = clamp(x, 0., 11.); return mix(band(floor(x)), band(min(floor(x) + 1., 11.)), smoothstep(0., 1., fract(x))); }
float lum(vec3 c) { return dot(c, vec3(.3, .5, .2)); }
vec3 phase(vec2 t, float w) {
	if (t.x < 0. || t.y < 0. || t.x > 1. || t.y > 1.) return vec3(0.);
	return texture(sTD3DInputs[0], vec3(t, (clamp(w, 0., 1.) * 63. + .5) / 64.)).rgb;
}
vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }
vec3 hueRot(vec3 c, float a) {
	float y = dot(c, vec3(.299, .587, .114)), i = dot(c, vec3(.596, -.274, -.322)), q = dot(c, vec3(.211, -.523, .312));
	float ca = cos(a), sa = sin(a); float i2 = i * ca - q * sa, q2 = i * sa + q * ca;
	return max(vec3(y + .956 * i2 + .621 * q2, y - .272 * i2 - .647 * q2, y - 1.106 * i2 + 1.703 * q2), 0.);
}

void main() {
	if (uV0.w < .002) { fragColor = vec4(0., 0., 0., 1.); return; }
	float asp = max(uV1.w, .1);
	vec2 sc = (vUV.st - .5) * vec2(asp, 1.);
	float dz = max(uV0.y, .05);                    // poloviční hloubka sochy
	float R = max(uV1.z, .05);
	// kamera: dívá se na střed, natočená kolem svislé osy (yaw) a mírně shora (pitch)
	float cy = cos(uV0.z), sy = sin(uV0.z), cp = cos(uV3.x), sp = sin(uV3.x);
	mat3 rot = mat3(cy, 0., sy, 0., 1., 0., -sy, 0., cy) * mat3(1., 0., 0., 0., cp, -sp, 0., sp, cp);
	vec3 ro = rot * vec3(0., 0., -4.2);
	vec3 rd = normalize(rot * vec3(sc + vec2(.08, -.16), 1.9 * max(uV3.z, .2)));
	// vrstvy času = roviny z = konst.; vpředu (blíž kameře) rozvitá lilie, vzadu pupen
	vec3 acc = vec3(0.);
	float zNow = (.5 - clamp(uV0.x, 0., 1.)) * 2. * dz;
	float tNow = (zNow - ro.z) / rd.z, aNow = 0.;
	vec2 pn = (ro + rd * tNow).xy;
	if (tNow > 0. && abs(pn.x) < 1. && abs(pn.y) < 1.) {               // přítomnost: plná lilie uvnitř sochy
		vec3 c = phase(uV1.xy + pn * R, uV0.x);
		aNow = smoothstep(.08, .4, dot(c, vec3(.3, .5, .2)));
		acc += c * aNow * 1.3 * smoothstep(1., .75, max(abs(pn.x), abs(pn.y)));
	}
	const float NS = 28.;
	for (int k = 0; k < 28; k++) {
		float tm = (float(k) + .5) / NS;
		float z = (.5 - tm) * 2. * dz;
		float tp = (z - ro.z) / rd.z;
		vec2 p = (ro + rd * tp).xy;
		if (tp < 0. || abs(p.x) > 1. || abs(p.y) > 1.) continue;
		vec2 tx = uV1.xy + p * R;
		float e = .004;
		float lx = lum(phase(tx + vec2(e, 0.), tm)) - lum(phase(tx - vec2(e, 0.), tm));
		float ly = lum(phase(tx + vec2(0., e), tm)) - lum(phase(tx - vec2(0., e), tm));
		float edge = smoothstep(.06, .3, length(vec2(lx, ly)));       // ostrý obrys květu v této fázi
		float b = bandS(tm * 11.);
		float near = abs(tm - uV0.x) * uV3.y;
		float vis = smoothstep(.15, 1., near);                            // u přítomnosti obrys nepřekrývá lilii
		vec3 cc = mix(phase(tx, tm) * 3., hue(uV2.x + tm * .9 + b * .25) * 1.3, uV2.y);
		float occl = tp > tNow ? 1. - aNow * .85 : 1.;                     // vrstvy za přítomností jsou jí zakryté
		acc += smoothstep(1., .75, max(abs(p.x), abs(p.y))) * cc * edge * (.015 + b * b * .45) * vis * occl * uV2.z;
	}
	fragColor = TDOutputSwizzle(vec4(acc * uV2.w * uV0.w, 1.));
}
