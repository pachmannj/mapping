// KYTICE — procedurální květiny z bodů (chryzantémy, pivoňky, lilie, stonky, listy, pyl).
// Každý pixel výstupu = jeden bod. Z jeho pořadí se odvodí květina, část (lístek / tyčinka / stonek / list / pyl),
// číslo lístku a místo na lístku (u = od středu ke špičce, v = napříč). Tvar lístku je oblouk se zakřivením,
// takže rozkvět je jen změna úhlů — květiny opravdu rozkvétají. Každá květina poslouchá své frekvenční pásmo
// (rozkvět, vlnění lístků, záře). Pohyb je organický a plynulý: vítr ohýbá stonky, po lístcích běží vlny, mlha proudí
// polem jako u Vortexu — hudba mění rychlost a sílu proudění, nic neskáče.
// Výstup 0 = poloha (xyz, násobek velikosti), výstup 1 = barva (rgb, alfa).
uniform vec4 uA0;   // čas, rozkvět (0–1), dýchání (vyhlazené), chvění (vyhlazené)
uniform vec4 uA1;   // poloha vlny kopáku (0 = střed, 1.5 = za špičkami), síla vlny, rozpad do mlhy, jas
uniform vec4 uA2;   // odstín posun, záře lilií, sytost, -
uniform vec4 uA3;   // fáze proudění (hudební čas), síla větru, vlnění lístků, -
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;   // 12 frekvenčních pásem (vyhlazená v sc_bouquet.py)
layout(location = 0) out vec4 oPos;
layout(location = 1) out vec4 oCol;

float h1(float n) { return fract(sin(n * 12.9898 + 4.1414) * 43758.5453); }   // jen pro malá čísla (index lístku, květiny)
float pcg(uint v) {                                    // celočíselný hash: bez pruhů i pro půl milionu bodů
	uint st = v * 747796405u + 2891336453u;
	uint w = ((st >> ((st >> 28u) + 4u)) ^ st) * 277803737u;
	return float((w >> 22u) ^ w) / 4294967295.;
}
float h2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float band(float i) {                                  // jen desetinná čísla (int z NaN shodí Vulkan na Macu)
	i = clamp(i, 0., 11.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(i, 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
vec3 noise3(vec3 p) {                                  // hladký vektorový šum (součet sinů, levný)
	return vec3(sin(p.y * 1.7 + p.z * 1.3 + sin(p.x * 2.1)), sin(p.z * 1.9 + p.x * 1.1 + sin(p.y * 1.7)),
	            sin(p.x * 1.5 + p.y * 2.3 + sin(p.z * 1.3)));
}

// květiny kytice: střed, osa (kam květ míří), typ (0 chryzantéma, 1 pivoňka, 2 lilie), velikost, pásmo (0–11)
void flower(float id, out vec3 c, out vec3 up, out float type, out float sc, out float bi) {
	if (id < .5)      { c = vec3(.15, .55, .2);    up = vec3(.15, .75, .65);  type = 2.; sc = 1.15; bi = 5.; }
	else if (id < 1.5){ c = vec3(-.78, .42, -.2);  up = vec3(-.5, .7, .5);    type = 2.; sc = .95;  bi = 8.; }
	else if (id < 2.5){ c = vec3(.88, .22, .2);    up = vec3(.55, .55, .65);  type = 2.; sc = .9;   bi = 3.; }
	else if (id < 3.5){ c = vec3(-.05, -.42, .62); up = vec3(.05, .3, .95);   type = 2.; sc = .8;   bi = 10.; }
	else if (id < 4.5){ c = vec3(.5, 1.0, -.55);   up = vec3(.3, .85, .3);    type = 2.; sc = .8;   bi = 6.; }
	else if (id < 5.5){ c = vec3(-.5, -.1, .3);    up = vec3(-.35, .6, .7);   type = 0.; sc = .95;  bi = 1.; }
	else if (id < 6.5){ c = vec3(.72, -.42, -.15); up = vec3(.45, .55, .7);   type = 1.; sc = 1.;   bi = 0.; }
	else if (id < 7.5){ c = vec3(-.4, -.8, .45);   up = vec3(-.1, .4, .9);    type = 0.; sc = .8;   bi = 9.; }
	else if (id < 8.5){ c = vec3(-1.05, -.35, -.4);up = vec3(-.55, .5, .65);  type = 1.; sc = .85;  bi = 2.; }
	else              { c = vec3(.55, -.95, .45);  up = vec3(.35, .35, .85);  type = 0.; sc = .65;  bi = 11.; }
	up = normalize(up);
}

// bod na lístku: oblouk v rovině (radiála, osa) se zakřivením kappa, šířka podle profilu, prohnutí napříč (cup)
vec3 petal(float theta, float r0, float L, float beta0, float kappa, float w, float cup, float u, float v,
           out vec3 nrm) {
	float k = abs(kappa) < .02 ? .02 : kappa;
	float s = L * u, b = beta0 + k * s;
	float rho = (sin(b) - sin(beta0)) / k, hh = (cos(beta0) - cos(b)) / k;
	vec3 rad = vec3(cos(theta), sin(theta), 0.), side = vec3(-sin(theta), cos(theta), 0.);
	vec3 T = rad * cos(b) + vec3(0., 0., sin(b));
	nrm = normalize(cross(T, side));
	return rad * (r0 + rho) + vec3(0., 0., hh) + side * v * w + nrm * v * v * cup * w;
}

void main() {
	ivec2 ip = ivec2(gl_FragCoord.xy);
	vec2 res = uTDOutputInfo.res.zw;
	float row = float(ip.y), idx = float(ip.y) * res.x + float(ip.x);
	uint ui = uint(ip.y) * uint(res.x) + uint(ip.x);
	float r1 = pcg(ui * 4u), r2 = pcg(ui * 4u + 1u), r3 = pcg(ui * 4u + 2u), r4 = pcg(ui * 4u + 3u);
	float t = uA0.x;
	float H = res.y;
	float ph = uA3.x;                                    // hudební čas: zrychluje s energií, nikdy neskočí
	// rozdělení řádků textury mezi květiny: 5 lilií (hlavní má nejvíc bodů), 3 chryzantémy, 2 pivoňky, ~3 % pyl
	float fr = row / H;
	float id = fr < .16 ? 0. : (fr < .27 ? 1. : (fr < .37 ? 2. : (fr < .46 ? 3. : (fr < .55 ? 4. :
	          (fr < .66 ? 5. : (fr < .76 ? 6. : (fr < .84 ? 7. : (fr < .91 ? 8. : (fr < .97 ? 9. : 10.)))))))));
	vec3 P; vec3 col; float alpha = .12, size = 1.;
	if (id > 9.5) {                                     // pyl a mlha volně ve vzduchu, proudí polem
		vec3 q = (vec3(r1, r2, r3) - .5) * vec3(4.5, 3.2, 3.);
		q += noise3(q * .6 + ph * .08) * .35 + vec3(0., fract(r4 + t * .01) * .4, 0.);
		float keep = step(.7, r1);                         // jen pětina pylu je vidět, zbytek by dělal zrno
		oPos = vec4(q, (.8 + r4) * keep); oCol = vec4(vec3(.8, .75, 1.) * (.05 + r4 * .12) * uA1.w * keep, 1.);
		return;
	}
	vec3 c, up; float type, sc, bi;
	flower(id, c, up, type, sc, bi);
	float fid = id;
	// každá květina poslouchá své pásmo (sousední pásma trochu taky)
	float bnd = band(bi) * .6 + (band(bi - 1.) + band(bi + 1.)) * .2;
	// rozkvět: společná energie + vlastní pásmo + pomalé dýchání v jiné fázi pro každou květinu
	float open = clamp(uA0.y * .55 + bnd * .6 - .08 + sin(ph * .23 + fid * 1.7) * .07, .04, 1.);
	// vítr: celý květ se kývá na stonku (plynulé pole, každá květina v jiné fázi), s energií silněji
	vec3 sway = noise3(vec3(fid * 2.3, ph * .35, fid * .7)) * uA3.y * (.08 + bnd * .07);
	up = normalize(up + sway * 1.6);
	vec3 lp, nrm = vec3(0., 0., 1.);
	float u = sqrt(r2), v = r3 * 2. - 1., part = r1;      // sqrt: víc bodů ke špičkám (lístek se rozšiřuje)           // part: 0–0.78 lístky, pak tyčinky / střed, stonek, listy
	float waveUV = 0., pid = 0.;
	if (part < .78) {
		float pr = part / .78;
		if (type < .5) {                                 // CHRYZANTÉMA: ~170 úzkých lístků ve spirále, špičky se stáčejí nahoru
			float N = 110., pi = floor(pr * N), layer = pi / N;
			float th = pi * 2.39996 + h1(pi + fid * 7.) * .2;
			float L = mix(.16, .55, pow(layer, .7)) * (.85 + h1(pi * 1.3) * .3);
			float b0 = mix(1.45, mix(1.2, -.35, layer), open);
			float kap = mix(2.6, 1.0, layer) * mix(1.4, 1., open);
			float wp = mix(.03, .065, layer) * pow(sin(3.1416 * clamp(u * .92 + .08, 0., 1.)), .6);
			lp = petal(th, .03, L, b0, kap, wp, .6, u, v, nrm); pid = pi;
			col = mix(vec3(.75, .62, .95), vec3(1., .95, 1.), u * .6 + layer * .3);
			alpha = .05 + .3 * pow(abs(v), 10.) + .12 * smoothstep(.9, 1., u);   // okraje a špičky lístků svítí (krajkový vzhled)
		} else if (type < 1.5) {                         // PIVOŇKA: ~55 širokých prohnutých lístků do koule
			float N = 55., pi = floor(pr * N), layer = pi / N;
			float th = pi * 2.39996 + h1(pi + fid * 5.) * .3;
			float L = mix(.14, .48, layer) * (.85 + h1(pi * 2.1) * .3);
			float b0 = mix(1.5, mix(1.45, .25, layer), open);
			float kap = mix(3.2, 1.4, layer);
			float wp = mix(.1, .26, layer) * pow(sin(3.1416 * clamp(u * .85 + .15, 0., 1.)), .45);
			lp = petal(th, .05, L, b0, kap, wp, .55, u, v, nrm); pid = pi;
			lp += nrm * sin(u * 18. + v * 6. + pi) * .006;   // zvlnění
			col = mix(vec3(1., .62, .78), vec3(1., .9, .95), u * .5 + layer * .4);
			alpha = .045 + .3 * pow(abs(v), 10.) + .15 * smoothstep(.88, 1., u);
		} else {                                         // LILIE: 6 dlouhých lístků, s rozkvětem se ohnou dozadu
			float pi = floor(pr * 6.), layer = mod(pi, 2.);
			float th = pi * 1.0472 + .3;
			float L = mix(.68, .78, layer);
			float b0 = mix(1.35, .6, open), kap = mix(.4, -2.4, open) * mix(1., .85, layer);
			float wp = mix(.13, .17, 1. - layer) * pow(sin(3.1416 * clamp(u, 0., 1.)), .75) * (1. - u * .25);
			lp = petal(th, .02, L, b0, kap, wp, .35, u, v, nrm); pid = pi;
			lp += nrm * pow(abs(v), 4.) * sin(u * 34. + pi) * .025;   // zvlněný okraj
			lp += nrm * smoothstep(.2, .0, abs(v)) * .01;           // žilka uprostřed
			vec3 deep = mix(vec3(1., .2, .62), vec3(.92, .3, .9), h1(fid * 5.3));   // každá lilie trochu jiný odstín růžové
			col = mix(vec3(1., .85, .95), deep, smoothstep(.05, .7, u) * (.6 + .4 * abs(v)));
			alpha = .06 + .35 * pow(abs(v), 8.) + .08 * smoothstep(.7, 1., u);
			size = 1.1;
		}
		waveUV = u;
		alpha *= .2 + .8 * smoothstep(.05, .5, u);      // střed květu, kde se lístky překrývají, nepřepálit
	} else if (part < .84) {                             // tyčinky (lilie) / střed květu
		if (type > 1.5) {
			float si = floor(r4 * 7.);
			float th = si * .8976 + .2;
			float L = si > 5.5 ? .5 : .62;               // čnělka je kratší a uprostřed
			lp = petal(th, .0, L, mix(1.5, 1.05, open), -.6, .006, 0., u, v, nrm);
			if (u > .93 && si < 5.5) {                   // prašník: oranžovočervený shluk
				lp += (vec3(r1, r3, r4) - .5) * .045;
				col = vec3(1., .35, .12); alpha = .45; size = 1.4;
			} else { col = vec3(.55, .9, .4); alpha = .18; }
		} else {
			float a = r4 * 6.2832, rr = sqrt(u) * (type < .5 ? .05 : .08);
			lp = vec3(cos(a) * rr, sin(a) * rr, .04 * (1. - u) + (type < .5 ? .0 : .03));
			col = type < .5 ? vec3(.9, .85, .5) : vec3(1., .8, .3); alpha = .07;
		}
	} else if (part < .93) {                             // stonek: dolů, mírný oblouk
		float Ls = 1.5;
		float a = r4 * 6.2832;
		lp = vec3(cos(a), sin(a), 0.) * .012 + vec3(sin(u * 2.2 + fid) * .12 * u, cos(u * 1.7 + fid) * .06 * u, -u * Ls);
		col = vec3(.35, .8, .35); alpha = .045;
	} else {                                             // listy na stonku
		float li = floor(r4 * 2.);
		float th = h1(li + fid * 3.) * 6.2832;
		lp = petal(th, .015, .5, .25, -1.1, .07 * pow(sin(3.1416 * u), .8), .5, u, v, nrm);
		lp.z -= mix(.7, 1.3, li) + .0;
		col = mix(vec3(.25, .7, .2), vec3(.6, 1., .35), pow(abs(v), 4.)); alpha = .025 + .06 * pow(abs(v), 8.);
	}
	// do světa: místní osa z = osa květu. Hlava květu se ve větru posune, stonek je dole ukotvený a ohne se.
	bool onStem = part >= .84;
	vec3 up0 = normalize(up - sway * 1.6);
	vec3 U = onStem ? up0 : up;
	vec3 X = normalize(cross(U, abs(U.y) < .9 ? vec3(0., 1., 0.) : vec3(1., 0., 0.))), Y = cross(U, X);
	float breathe = 1. + uA0.z * (.03 + bnd * .05);
	mat3 B = mat3(X, Y, U);
	vec3 head = sway * .9 * sc;
	float k = sc * 1.45;
	P = c * vec3(1.55, 1.15, 1.15) + B * lp * k * (onStem ? 1. : breathe);
	if (onStem) P += head * pow(clamp(1. + lp.z / 1.6, 0., 1.), 2.);   // čím blíž hlavě, tím víc se ohne
	else P += head;
	vec3 Nw = B * nrm;
	// vlnění lístků: vlna běží od středu ke špičkám, každý lístek v jiné fázi, síla podle pásma květiny
	float und = sin(waveUV * 5. - ph * 1.7 + pid * 1.3 + fid) * uA3.z * (.012 + bnd * .035) * waveUV * waveUV;
	P += Nw * und * k;
	// vlna kopáku: měkká, od středu ke špičkám
	float wv = exp(-pow((waveUV - uA1.x) / .22, 2.)) * uA1.y * step(.001, waveUV);
	P += Nw * wv * .045 * k;
	// chvění lístků (špičky víc), plynulé
	P += noise3(P * 2.3 + vec3(ph * .6, ph * .45, fid)) * uA0.w * .01 * (.3 + waveUV);
	// rozpad do mlhy: jen část bodů (r4^3) odplyne s proudem pole, s hudbou se vrátí
	float dis = uA1.z * pow(r4, 3.) * (.4 + waveUV);
	P += noise3(P * .8 + ph * .3) * dis * .6;
	alpha *= (1. - dis * .5);
	// barvy: lilie blikne na kopák, květy dýchají s pásmem
	float glow = (.55 + bnd * 1.1) * (type > 1.5 ? 1. + uA2.y * .8 : 1.);
	col = mix(vec3(dot(col, vec3(.33))), col, uA2.z);
	oPos = vec4(P, size * (1. + wv * .3));
	oCol = vec4(col * alpha * .4 * glow * uA1.w * (1. + wv * 1.), 1.);
}
