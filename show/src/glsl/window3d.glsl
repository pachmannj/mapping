// 3D OKNO VE ZDI — anamorfní iluze jako na billboardech v New Yorku: obraz na zdi je přesně ta perspektiva,
// kterou by divák (oko v bodě uW0) viděl skrz skutečný výklenek ve zdi. Objekt (lilie / pták) je karta v prostoru:
// uvnitř výklenku ho ořízne okraj otvoru, vystoupí-li před zeď (z > 0), přeroste rám a svítí na zeď kolem.
// Výklenek má stěny se stínem objektu, odlesk na podlaze, světlo od objektu a svítící hrany.
// Souřadnice: zeď = rovina z = 0, obraz má výšku 2 (y od -1 do 1), divák stojí v +z a dívá se do zdi.
// vstup 0 = objekt (rgb předem vynásobené alfou, a = maska), vstup 1 = rozmazaný objekt (měkký stín, barva světla)
uniform vec4 uW0;   // oko x, y, vzdálenost od zdi, poměr stran obrazu
uniform vec4 uW1;   // otvor: poloviční šířka, poloviční výška, hloubka výklenku, jas hran
uniform vec4 uW2;   // objekt: střed x, y, z (z > 0 = před zdí), poloviční výška karty
uniform vec4 uW3;   // poměr stran objektu, světlo x, y, z
uniform vec4 uW4;   // odstín stěn, síla mřížky, odlesk podlahy, síla stínu
uniform vec4 uW5;   // pulz hran (kopák), světlo objektu na stěny a zeď, celkový jas, střed otvoru y
out vec4 fragColor;

vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }

// průsečík paprsku s kartou objektu → barva + alfa (vec4(0) mimo kartu)
vec4 card(vec3 o, vec3 d, out float tHit) {
	tHit = -1.;
	if (abs(d.z) < 1e-5) return vec4(0.);
	float t = (uW2.z - o.z) / d.z;
	if (t <= 0.) return vec4(0.);
	vec3 q = o + d * t;
	float hh = max(uW2.w, .01), hw = hh * max(uW3.x, .05);
	vec2 uv = vec2((q.x - uW2.x) / (2. * hw) + .5, (q.y - uW2.y) / (2. * hh) + .5);
	if (uv.x < 0. || uv.y < 0. || uv.x > 1. || uv.y > 1.) return vec4(0.);
	tHit = t;
	return texture(sTD2DInputs[0], uv);
}
float cardShadow(vec3 x, vec3 L) {                       // kolik světla objekt zastíní v bodě x
	vec3 d = L - x;
	if (abs(d.z) < 1e-5) return 0.;
	float t = (uW2.z - x.z) / d.z;
	if (t <= 0. || t >= 1.) return 0.;
	vec3 q = x + d * t;
	float hh = max(uW2.w, .01), hw = hh * max(uW3.x, .05);
	vec2 uv = vec2((q.x - uW2.x) / (2. * hw) + .5, (q.y - uW2.y) / (2. * hh) + .5);
	if (uv.x < 0. || uv.y < 0. || uv.x > 1. || uv.y > 1.) return 0.;
	return texture(sTD2DInputs[1], uv).a;
}
vec3 objLight() {                                        // průměrná barva objektu = barva světla, které vyzařuje
	vec3 c = vec3(0.);
	for (int i = 0; i < 5; i++) {
		float a = float(i) * 1.2566;
		c += texture(sTD2DInputs[1], vec2(.5) + (i == 0 ? vec2(0.) : vec2(cos(a), sin(a)) * .22)).rgb;
	}
	return c / 5.;
}

void main() {
	float asp = max(uW0.w, .1);
	vec3 P = vec3((vUV.s - .5) * 2. * asp, (vUV.t - .5) * 2., 0.);   // bod na zdi
	vec3 E = vec3(uW0.x, uW0.y, max(uW0.z, .5));
	vec3 d = normalize(P - E);
	float tWall = length(P - E);
	float W = uW1.x, H = uW1.y, D = max(uW1.z, .05), oy = uW5.w;
	vec3 Lp = uW3.yzw;
	vec3 glowC = objLight() * uW5.y;
	vec3 Oc = uW2.xyz;
	bool inHole = abs(P.x) < W && abs(P.y - oy) < H;
	vec3 behind = vec3(0.);
	float tBehind = 1e9;

	if (inHole) {
		// paprsek vstoupil do výklenku: najdi stěnu, kterou trefí
		float tx = (d.x > 0. ? W - P.x : -W - P.x) / (abs(d.x) > 1e-5 ? d.x : 1e-5);
		float ty = (d.y > 0. ? oy + H - P.y : oy - H - P.y) / (abs(d.y) > 1e-5 ? d.y : 1e-5);
		float tz = (-D - P.z) / min(d.z, -1e-5);
		tx = tx < 0. ? 1e9 : tx; ty = ty < 0. ? 1e9 : ty;
		float t = min(tz, min(tx, ty));
		vec3 X = P + d * t;
		vec3 n; vec2 fc;                                    // normála a souřadnice na stěně (pro mřížku)
		if (t == tz)      { n = vec3(0., 0., 1.);               fc = vec2(X.x, X.y - oy); }
		else if (t == tx) { n = vec3(-sign(d.x), 0., 0.);       fc = vec2(X.z, X.y - oy); }
		else              { n = vec3(0., -sign(d.y), 0.);       fc = vec2(X.x, X.z); }
		// svítící hrany výklenku (kouty) + jemná mřížka
		vec3 eA = vec3(W - abs(X.x), H - abs(X.y - oy), D + X.z);   // vzdálenosti od stěn
		float e1 = min(min(eA.x, eA.y), eA.z);
		float corner = 0.;
		if (t == tz) corner = min(eA.x, eA.y); else if (t == tx) corner = min(eA.y, eA.z); else corner = min(eA.x, eA.z);
		float edge = exp(-corner / .006) + exp(-corner / .05) * .25;
		vec2 g = abs(fract(fc * 5. + .5) - .5) / max(fwidth(fc * 5.), vec2(1e-4));
		float grid = (1. - smoothstep(.0, 1.2, min(g.x, g.y))) * uW4.y;
		vec3 base = mix(vec3(.05), hue(uW4.x) * .12, .6);
		// osvětlení: horní přední světlo se stínem objektu + barevné světlo vyzařované objektem
		vec3 l = normalize(Lp - X);
		float sh = 1. - cardShadow(X, Lp) * uW4.w;
		float lam = max(dot(n, l), 0.) * sh;
		vec3 toO = Oc - X; float dO = length(toO);
		float lamO = max(dot(n, toO / max(dO, 1e-3)), 0.) / (1. + dO * dO * 3.);
		behind = base * (.12 + lam * 1.3) + glowC * lamO * 1.5 * sh
			+ (hue(uW4.x + .1) * .5 + .5) * (edge * uW1.w * (1. + uW5.x * 2.) + grid * .35 * (.4 + lam));
		// podlaha: odlesk objektu
		if (n.y > .5 && uW4.z > .001) {
			float tr; vec4 r = card(X, reflect(d, n), tr);
			behind += r.rgb * uW4.z * exp(-max(tr, 0.) * 1.5);
		}
		tBehind = tWall + t;
	} else {
		// zeď kolem otvoru: tmavá (skutečná zeď), jen ji osvítí objekt, když je před ní, a svítí rám otvoru
		vec2 q = vec2(abs(P.x) - W, abs(P.y - oy) - H);
		float dr = length(max(q, 0.)) + min(max(q.x, q.y), 0.);
		float frame = exp(-dr / .004) + exp(-dr / .04) * .2;
		behind = (hue(uW4.x + .1) * .5 + .5) * frame * uW1.w * (1. + uW5.x * 2.);
		float front = smoothstep(-.05, .2, Oc.z);
		vec3 toO = Oc - P; float dO = length(toO);
		float spill = max(toO.z, 0.) / max(dO, 1e-3) / (1. + dO * dO * 2.5);
		float sh = 1. - cardShadow(P, Lp) * uW4.w;
		behind += glowC * spill * front * 1.2 * sh;
		tBehind = tWall;
	}
	// objekt: kreslí se, je-li paprsek trefí dřív než stěnu výklenku / zeď
	float to; vec4 o = card(E, d, to);
	vec3 col = behind;
	if (to > 0. && to < tBehind) col = o.rgb + behind * (1. - o.a);
	fragColor = TDOutputSwizzle(vec4(max(col, 0.) * uW5.z, 1.));
}
