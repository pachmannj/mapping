// KYTICE / KVĚT — procedurální květiny z bodů (chryzantémy, pivoňky, lilie, tulipány, kopretiny, růže, stonky, listy, pyl).
// Režim jedné květiny (scéna Květ): všechny body patří jedné květině uprostřed, která se plynule promění (morf)
// z jednoho druhu na další — body přeletí z lístků jednoho druhu do lístků druhého.
// Každý pixel výstupu = jeden bod. Z jeho pořadí se odvodí květina, část (lístek / tyčinka / stonek / list / pyl),
// číslo lístku a místo na lístku (u = od středu ke špičce, v = napříč). Tvar lístku je oblouk se zakřivením,
// takže rozkvět je jen změna úhlů — květiny opravdu rozkvétají. Každá květina poslouchá své frekvenční pásmo
// (rozkvět, vlnění lístků, záře). Pohyb je organický a plynulý: vítr ohýbá stonky, po lístcích běží vlny, mlha proudí
// polem jako u Vortexu — hudba mění rychlost a sílu proudění, nic neskáče.
// Výstup 0 = poloha (xyz, násobek velikosti), výstup 1 = barva (rgb, alfa).
uniform vec4 uA0;   // čas, rozkvět (0–1), dýchání (vyhlazené), chvění (vyhlazené)
uniform vec4 uA1;   // poloha vlny kopáku (0 = střed, 1.5 = za špičkami), síla vlny, rozpad do mlhy, jas
uniform vec4 uA2;   // posun odstínu lilií (rad), záře lilií, sytost, rozptyl barev mezi liliemi
uniform vec4 uA3;   // fáze proudění (hudební čas), síla větru, vlnění lístků, -
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;   // 12 frekvenčních pásem (vyhlazená v sc_bouquet.py)
uniform vec4 uH0; uniform vec4 uH1; uniform vec4 uH2; uniform vec4 uH3;   // RÁNY: stáří (s), síla, odkud x, y
uniform vec4 uH4;   // délka mávnutí (s), rychlost šíření vlny (jednotek/s), -, -
uniform vec4 uM0;   // KVĚT: jedna květina (0/1), druh A, druh B, morf A → B (0–1)
uniform vec4 uM1;   // KVĚT: otočení květu kolem osy (rad), velikost, nafouknutí dlouhým tónem (0–1), náklon v rytmu (rad)
uniform vec4 uA4;   // RYTMUS: poloha v taktu (0–4 doby, plynule podle tempa), síla kopáku, síla virblu, síla hi-hatů
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
vec3 hueRot(vec3 c, float a) {                         // otočení odstínu se zachováním jasu
	float y = dot(c, vec3(.299, .587, .114)), i = dot(c, vec3(.596, -.274, -.322)), q = dot(c, vec3(.211, -.523, .312));
	float ca = cos(a), sa = sin(a); float i2 = i * ca - q * sa, q2 = i * sa + q * ca;
	return max(vec3(y + .956 * i2 + .621 * q2, y - .272 * i2 - .647 * q2, y - 1.106 * i2 + 1.703 * q2), 0.);
}
// jedno mávnutí: plynulý náběh i doběh (sin²), trvá T sekund
float flap1(float la, float T) { return (la > 0. && la < T) ? pow(sin(3.1416 * la / T), 2.) : 0.; }
// rána h (stáří, síla, odkud x, y): vlna dorazí ke květině za vzdálenost / rychlost; vrací mávnutí a jeho fázi
float hitFlap(vec4 h, vec2 at, float T, float spd, inout float ph) {
	float la = h.x - length(at - h.zw) / max(spd, .1);
	float f = flap1(la, T) * h.y;
	if (f > 0.) ph = max(ph, clamp(la / T, 0., 1.));
	return f;
}
vec3 noise3(vec3 p) {                                  // hladký vektorový šum (součet sinů, levný)
	return vec3(sin(p.y * 1.7 + p.z * 1.3 + sin(p.x * 2.1)), sin(p.z * 1.9 + p.x * 1.1 + sin(p.y * 1.7)),
	            sin(p.x * 1.5 + p.y * 2.3 + sin(p.z * 1.3)));
}

// květiny kytice: střed, osa (kam květ míří), typ (0 chryzantéma, 1 pivoňka, 2 lilie, 3 tulipán, 4 kopretina, 5 růže), velikost, pásmo
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

// HLAVA KVĚTU daného druhu: lístky (part < .78) a tyčinky / střed (part < .84), v místních souřadnicích (osa květu = z)
void headPoint(float type, float open, float part, float u, float v, float r1, float r3, float r4, float fid, float bnd,
               out vec3 lp, out vec3 nrm, out vec3 col, out float alpha, out float size, out float pid, out float waveUV) {
	nrm = vec3(0., 0., 1.); alpha = .12; size = 1.; pid = 0.; waveUV = 0.;
	float ha = uA2.x + ((bnd - .45) * 2. + (h1(fid * 7.7) - .5)) * uA2.w;   // posun barvy podle hudby
	if (part < .78) {
		float pr = part / .78;
		if (type < .5) {                                 // CHRYZANTÉMA: ~110 úzkých lístků ve spirále, špičky se stáčejí nahoru
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
			bool big = uM0.x > .5;                       // v Květu větší a růžová, v Kytici původní bílo-růžová
			float L = mix(.14, .48, layer) * (.85 + h1(pi * 2.1) * .3) * (big ? 1.3 : 1.);
			float b0 = mix(1.5, mix(1.45, .25, layer), open);
			float kap = mix(3.2, 1.4, layer);
			float wp = mix(.1, .26, layer) * pow(sin(3.1416 * clamp(u * .85 + .15, 0., 1.)), .45);
			lp = petal(th, .05, L, b0, kap, wp, .55, u, v, nrm); pid = pi;
			lp += nrm * sin(u * 18. + v * 6. + pi) * .006;   // zvlnění
			col = big ? hueRot(mix(vec3(1., .3, .6), vec3(1., .72, .85), u * .4 + layer * .35), ha * .8)
			          : mix(vec3(1., .62, .78), vec3(1., .9, .95), u * .5 + layer * .4);
			alpha = .045 + .3 * pow(abs(v), 10.) + .15 * smoothstep(.88, 1., u);
		} else if (type < 2.5) {                         // LILIE: 6 dlouhých lístků, s rozkvětem se ohnou dozadu
			float pi = floor(pr * 6.), layer = mod(pi, 2.);
			float th = pi * 1.0472 + .3;
			float L = mix(.68, .78, layer);
			float b0 = mix(1.35, .6, open), kap = mix(.4, -2.4, open) * mix(1., .85, layer);
			float wp = mix(.13, .17, 1. - layer) * pow(sin(3.1416 * clamp(u, 0., 1.)), .75) * (1. - u * .25);
			lp = petal(th, .02, L, b0, kap, wp, .35, u, v, nrm); pid = pi;
			lp += nrm * pow(abs(v), 4.) * sin(u * 34. + pi) * .025;   // zvlněný okraj
			lp += nrm * smoothstep(.2, .0, abs(v)) * .01;           // žilka uprostřed
			vec3 deep = hueRot(mix(vec3(1., .2, .62), vec3(.92, .3, .9), h1(fid * 5.3)), ha);
			col = mix(hueRot(vec3(1., .85, .95), ha * .5), deep, smoothstep(.05, .7, u) * (.6 + .4 * abs(v)));
			alpha = .06 + .35 * pow(abs(v), 8.) + .08 * smoothstep(.7, 1., u);
			size = 1.1;
		} else if (type < 3.5) {                         // TULIPÁN: 6 širokých lístků do kalichu, s rozkvětem se rozevře
			float pi = floor(pr * 6.), layer = mod(pi, 2.);
			float th = pi * 1.0472 + layer * .2;
			float L = mix(.55, .6, layer);
			float b0 = mix(1.52, 1.05, open), kap = mix(.9, -.2, open);
			float wp = .24 * pow(sin(3.1416 * clamp(u * .9 + .1, 0., 1.)), .5);
			lp = petal(th, .03, L, b0, kap, wp, .75, u, v, nrm); pid = pi;
			col = hueRot(mix(vec3(1., .78, .2), vec3(1., .18, .12), smoothstep(.15, .8, u)), ha * .7);
			alpha = .05 + .32 * pow(abs(v), 9.) + .1 * smoothstep(.85, 1., u);
			size = 1.05;
		} else if (type < 4.5) {                         // KOPRETINA: ~34 tenkých plochých bílých lístků kolem velkého středu
			float N = 34., pi = floor(pr * N);
			float th = pi * 6.2832 / N + h1(pi + fid) * .05;
			float L = .55 * (.92 + h1(pi * 3.7) * .16);
			float b0 = mix(1.25, .05, open), kap = mix(.6, -.25, open);
			float wp = .045 * pow(sin(3.1416 * clamp(u * .95 + .05, 0., 1.)), .4);
			lp = petal(th, .12, L, b0, kap, wp, .2, u, v, nrm); pid = pi;
			col = mix(vec3(.95, .95, 1.), hueRot(vec3(1., .85, .95), ha), smoothstep(.6, 1., u) * .5);
			alpha = .06 + .3 * pow(abs(v), 8.) + .1 * smoothstep(.9, 1., u);
		} else {                                         // RŮŽE: ~32 prohnutých lístků ve spirále, střed sevřený
			float N = 32., pi = floor(pr * N), layer = pi / N;
			float th = pi * 2.39996;
			float L = mix(.13, .45, layer) * (.9 + h1(pi * 2.7) * .2);
			float b0 = mix(1.56, mix(1.5, .55, pow(layer, 1.5)), open);
			float kap = mix(4.5, 1.6, layer);
			float wp = mix(.12, .3, layer) * pow(sin(3.1416 * clamp(u * .8 + .2, 0., 1.)), .45);
			lp = petal(th, .02, L, b0, kap, wp, .85, u, v, nrm); pid = pi;
			lp += nrm * pow(u, 3.) * pow(abs(v), 2.) * .04;         // okraje lístků se ohrnou ven
			col = hueRot(mix(vec3(.95, .1, .28), vec3(1., .45, .55), u * .4 + layer * .3), ha);
			alpha = .045 + .3 * pow(abs(v), 10.) + .14 * smoothstep(.88, 1., u);
		}
		waveUV = u;
		alpha *= .2 + .8 * smoothstep(.05, .5, u);      // střed květu, kde se lístky překrývají, nepřepálit
	} else {                                             // tyčinky (lilie) / střed květu
		if (type > 1.5 && type < 2.5) {
			float si = floor(r4 * 7.);
			float th = si * .8976 + .2;
			float L = si > 5.5 ? .5 : .62;               // čnělka je kratší a uprostřed
			lp = petal(th, .0, L, mix(1.5, 1.05, open), -.6, .006, 0., u, v, nrm);
			if (u > .93 && si < 5.5) {                   // prašník: oranžovočervený shluk
				lp += (vec3(r1, r3, r4) - .5) * .045;
				col = vec3(1., .35, .12); alpha = .45; size = 1.4;
			} else { col = vec3(.55, .9, .4); alpha = .18; }
		} else if (type > 3.5 && type < 4.5) {          // kopretina: velký žlutý polštář
			float a = r4 * 6.2832, rr = sqrt(u) * .13;
			lp = vec3(cos(a) * rr, sin(a) * rr, .07 * (1. - u * u));
			col = vec3(1., .78, .15); alpha = .16; size = 1.1;
		} else {
			float a = r4 * 6.2832, rr = sqrt(u) * (type < .5 ? .05 : .08);
			lp = vec3(cos(a) * rr, sin(a) * rr, .04 * (1. - u) + (type < .5 ? .0 : .03));
			col = type < .5 ? vec3(.9, .85, .5) : vec3(1., .8, .3); alpha = .07;
		}
	}
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
	if (uM0.x > .5) id = fr < (.97 - uM1.z * .12) ? 0. : 10.;   // dlouhý tón: víc bodů jde do atmosféry
	vec3 P; vec3 col; float alpha = .12, size = 1.;
	if (id > 9.5) {                                     // pyl a mlha volně ve vzduchu, proudí polem
		vec3 q = (vec3(r1, r2, r3) - .5) * vec3(4.5, 3.2, 3.);
		if (uM0.x > .5) {                                // Květ: atmosféra = oblak kolem květu, s dlouhým tónem se rozšíří a rozzáří
			vec3 dir = normalize(vec3(r1, r2, r3) - .5 + 1e-4);
			q = dir * (.6 + pow(r4, .5) * (1.2 + uM1.z * 1.6)) * (1. + uM1.y * .2);
			q += noise3(q * .7 + ph * .15) * (.25 + uM1.z * .4);
			oPos = vec4(q, .8 + r4 * 1.2);
			oCol = vec4(mix(vec3(.8, .6, 1.), hueRot(vec3(1., .4, .8), uA2.x), .5) * (.008 + r4 * .03) * (1. + uM1.z * 6.) * uA1.w, 1.);   // bez tónu skoro neviditelná
			return;
		}
		q += noise3(q * .6 + ph * .08) * .35 + vec3(0., fract(r4 + t * .01) * .4, 0.);
		float keep = step(.7 - uM1.z * .1, r1);            // část pylu; s dlouhým tónem houstne atmosféra
		q *= 1. + uM1.z * .2;
		oPos = vec4(q, (.8 + r4) * keep); oCol = vec4(vec3(.8, .75, 1.) * (.05 + r4 * .12) * (1. + uM1.z * .8) * uA1.w * keep, 1.);
		return;
	}
	vec3 c, up; float type, sc, bi;
	bool solo = uM0.x > .5;
	if (solo) { c = vec3(0.); up = normalize(vec3(0., .3, 1.)); type = uM0.y; sc = max(uM1.y, .1); bi = 5.; id = 0.; }
	else flower(id, c, up, type, sc, bi);
	float fid = id;
	// každá květina poslouchá své pásmo (sousední pásma trochu taky); jedna květina poslouchá celé spektrum
	float bnd = solo ? (band(2.) + band(5.) + band(8.)) / 3. : band(bi) * .6 + (band(bi - 1.) + band(bi + 1.)) * .2;
	float bx, env;
	// každá rána vyšle vlnu přes kytici: květina mávne, až k ní vlna dorazí (postupně, jako vlny Krasohledu)
	vec2 at = (c * vec3(1.55, 1.15, 1.15)).xy;
	float T = max(uH4.x, .2), spd = uH4.y;
	bx = 0.;
	env = hitFlap(uH0, at, T, spd, bx) + hitFlap(uH1, at, T, spd, bx) + hitFlap(uH2, at, T, spd, bx) + hitFlap(uH3, at, T, spd, bx);
	env = env / (1. + env * .35);                         // víc ran naráz se sčítá, ale měkce (nepřestřelí)
	// rozkvět: společná energie + vlastní pásmo + mávnutí z rány
	float open = clamp(uA0.y * .4 + bnd * .3 - .12 + env * 1.0 + uM1.z * (solo ? .35 : .3), .04, 1.);   // dlouhý tón květy rozevře
	// vítr: celý květ se kývá na stonku (plynulé pole, každá květina v jiné fázi), s energií silněji
	vec3 sway = noise3(vec3(fid * 2.3, ph * .35, fid * .7)) * uA3.y * (.04 + bnd * .04);
	// houpání v taktu: celá kytice se kolébá tam a zpět jednou za takt (2 doby na každou stranu)
	sway += vec3(sin(uA4.x * 1.5708 + fid * .35), .0, cos(uA4.x * 1.5708 + fid * .35) * .5) * .07 * (uA4.y * .7 + .15);
	up = normalize(up + sway * 1.6);
	vec3 lp, nrm = vec3(0., 0., 1.);
	float u = sqrt(r2), v = r3 * 2. - 1., part = r1;      // sqrt: víc bodů ke špičkám; part: 0–0.78 lístky, pak střed, stonek, listy
	float waveUV = 0., pid = 0.;
	if (part < .84) {
		headPoint(type, open, part, u, v, r1, r3, r4, fid, bnd, lp, nrm, col, alpha, size, pid, waveUV);
		if (solo && uM0.w > .001) {                      // morf do dalšího druhu: body přeletí z lístků jednoho druhu do druhého
			vec3 lp2, n2, c2; float a2, s2, p2, w2;
			headPoint(uM0.z, open, part, u, v, r1, r3, r4, fid, bnd, lp2, n2, c2, a2, s2, p2, w2);
			float m = smoothstep(0., 1., clamp(uM0.w * 1.15 - r4 * .15, 0., 1.));   // body přeletí v mírně rozložených časech
			vec3 mid = (lp + lp2) * .5 + vec3(0., 0., .25) * sin(m * 3.1416);    // oblouk přes střed: vír místo prolnutí
			lp = mix(mix(lp, mid, smoothstep(0., .5, m)), lp2, smoothstep(.5, 1., m));
			nrm = normalize(mix(nrm, n2, m)); col = mix(col, c2, m); alpha = mix(alpha, a2, m);
			size = mix(size, s2, m); waveUV = mix(waveUV, w2, m); pid = m < .5 ? pid : p2;
		}
		if (solo) {                                      // květ se pomalu otáčí kolem své osy
			float ca = cos(uM1.x), sa = sin(uM1.x);
			lp.xy = mat2(ca, -sa, sa, ca) * lp.xy; nrm.xy = mat2(ca, -sa, sa, ca) * nrm.xy;
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
	float breathe = 1. + uA0.z * (.02 + bnd * .03) + env * .1;
	mat3 B = mat3(X, Y, U);
	vec3 head = sway * .9 * sc;
	float k = sc * 1.45;
	P = c * vec3(1.55, 1.15, 1.15) + B * lp * k * (onStem ? 1. : breathe);
	if (onStem) P += head * pow(clamp(1. + lp.z / 1.6, 0., 1.), 2.);   // čím blíž hlavě, tím víc se ohne
	else P += head;
	vec3 Nw = B * nrm;
	// vlnění lístků: vlna běží od středu ke špičkám, každý lístek v jiné fázi, síla podle pásma květiny
	float und = sin(waveUV * 5. - uA4.x * 3.1416 + pid * 1.3 + fid) * uA3.z * (.008 + bnd * .02) * waveUV * waveUV;
	P += Nw * und * k;
	// vlna na svou dobu: s každým úderem proběhne lístky od středu ke špičkám (za ~2/3 doby)
	float wv = exp(-pow((waveUV - bx * 1.4) / .3, 2.)) * env * step(.001, waveUV) * uA1.y;   // mávnutí proběhne lístky od středu ke špičkám
	P += Nw * wv * .1 * k;
	// chvění lístků (špičky víc), plynulé
	if (uA0.w > .02) P += noise3(P * 2.3 + vec3(ph * .6, ph * .45, fid)) * uA0.w * .005 * (.3 + waveUV);
	// rozpad do mlhy: jen část bodů (r4^3) odplyne s proudem pole, s hudbou se vrátí
	float dis = (uA1.z + uM1.z * (solo ? .35 : .25)) * pow(r4, 3.) * (.4 + waveUV);
	if (dis > .002) P += noise3(P * .8 + ph * .3) * dis * .6;   // většina bodů mlhu nepočítá (šetří grafiku)
	alpha *= (1. - dis * .5);
	// barvy: lilie blikne na kopák, květy dýchají s pásmem
	float glow = (.5 + bnd * .8) * (.8 + env * .9) * (solo || (type > 1.5 && type < 2.5) ? 1. + uA2.y * .5 : 1.);
	col = mix(vec3(dot(col, vec3(.33))), col, uA2.z);
	if (!solo) {                                         // Kytice: rozjezd a dlouhý tón ji zvětší, pomalu se otáčí kolem svislé osy
		P *= uM1.y;
		float cs = cos(uM1.x), ss = sin(uM1.x); P.xz = mat2(cs, -ss, ss, cs) * P.xz;
	}
	{                                                    // náklon v rytmu: celá rostlina / kytice se nakloní od paty jako ve větru
		vec3 pv = solo ? vec3(0., -2.4, -.6) : vec3(0., -2.8, 0.);
		float ct = cos(uM1.w), st = sin(uM1.w);
		vec3 d = P - pv; P = pv + vec3(d.x * ct - d.y * st, d.x * st + d.y * ct, d.z);
	}
	oPos = vec4(P, size * (1. + wv * .3));
	oCol = vec4(col * alpha * 1.7 * glow * uA1.w * (1. + wv * 1.), 1.);
}
