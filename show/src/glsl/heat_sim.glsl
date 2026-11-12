// HEAT 2.0 — simulace: body stoupají v tepelném poli, každý má životnost a pak se vrátí do své cihly
// (myšlenka: feedback + noise pole + „life“ komponenta + Point Transform s maskou, supermarket sallad)
// Z webové verze zůstává logika: tepelné pole = 3D simplex šum přes cihly, kopák / virbl = vlny tepla.
// vstup 0 = předchozí stav (xyz, život), vstup 1 = výchozí polohy (cihlová mřížka)
// výstup: buffer 0 = nový stav, buffer 1 = poloha k vykreslení (xyz, velikost), buffer 2 = barva
uniform vec4 uH0;   // čas, dt, rychlost života (1 / životnost), síla proudění
uniform vec4 uH1;   // stoupání, kontrast tepla, práh tepla (maska), měřítko šumu
uniform vec4 uH2;   // natočení horkých bodů, zvětšení horkých bodů, míra barvy, jas
uniform vec4 uH3;   // energie, kopák, -, -
uniform vec4 uR0; uniform vec4 uR1; uniform vec4 uR2; uniform vec4 uR3;   // vlny tepla: x, y, čas od úderu, síla
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;   // 12 frekvenčních pásem (basy vlevo → výšky vpravo)
uniform vec4 uH4;   // síla spektra, jiskření (hihat), poměr stran, -
layout(location = 0) out vec4 oState;
layout(location = 1) out vec4 oPos;
layout(location = 2) out vec4 oCol;

uvec3 pcg3d(uvec3 v) {
	v = v * 1664525u + 1013904223u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	v ^= v >> 16u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	return v;
}
vec3 rnd3(uvec3 v) { return vec3(pcg3d(v)) * (1. / 4294967295.); }
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
vec3 flow(vec3 p, float t) {                          // proudění: gradient šumu otočený o 90° (bez zdrojů a propadů)
	const float e = .05;
	float n0 = snoise(vec3(p.xy, t));
	float nx = snoise(vec3(p.xy + vec2(e, 0.), t)), ny = snoise(vec3(p.xy + vec2(0., e), t));
	return vec3(ny - n0, -(nx - n0), 0.) / e + vec3(0., 0., snoise(p * 1.7 + t) * .3);
}
float wave(vec4 r, vec2 p) {
	if (r.w <= 0.) return 0.;
	float d = length(p - r.xy), front = r.z * .7;
	return r.w * exp(-pow((d - front) / .12, 2.)) * exp(-r.z * 1.1);
}
float band(float i) {                                  // jen desetinná čísla (int z NaN shodí Vulkan na Macu)
	i = clamp(i, 0., 11.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(i, 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
float spectrum(vec2 q) {                               // žhnoucí ekvalizér: každé pásmo rozpálí svůj sloupec do výšky podle síly
	float x = clamp((q.x / max(uH4.z, .1) * .5 + .5) * 12. - .5, 0., 11.);
	float b = mix(band(floor(x)), band(min(floor(x) + 1., 11.)), smoothstep(0., 1., fract(x)));
	float top = -1. + b * 2.1;                           // výška plamene
	return b * smoothstep(top + .05, top - .35, q.y);
}
vec3 heatRamp(float h) {                              // černá → tmavě rudá → oranžová → žlutá → bílá
	vec3 c = mix(vec3(.25, .0, .0), vec3(1., .18, .02), smoothstep(0., .4, h));
	c = mix(c, vec3(1., .65, .1), smoothstep(.35, .7, h));
	return mix(c, vec3(1., .97, .85), smoothstep(.7, 1., h));
}

void main() {
	vec4 st = texture(sTD2DInputs[0], vUV.st), start = texture(sTD2DInputs[1], vUV.st);
	vec3 r = rnd3(uvec3(gl_FragCoord.xy, uint(uH0.x * 60.)));
	float t = uH0.x, dt = min(uH0.y, .05);
	vec3 p = st.xyz;
	float life = st.w;
	if (life <= 0. && dot(p, p) == 0.) { p = start.xyz; life = start.w; }      // první snímek: rozprostřít životy
	life += dt * uH0.z * (.6 + start.w * .8);
	if (life >= 1.) { p = start.xyz; life = 0.; }                               // „life“: návrat do cihly
	// teplo: šum přes cihly (jako ve webové verzi) + vlny z úderů
	float h = snoise(vec3(start.xy * uH1.w, t * .3)) * .5 + .5;
	h = clamp(.5 + (h - .5) * uH1.y, 0., 1.);
	float w = wave(uR0, start.xy) + wave(uR1, start.xy) + wave(uR2, start.xy) + wave(uR3, start.xy);
	h = clamp(h * .45 + spectrum(start.xy) * uH4.x + w, 0., 1.5);       // tvar dělá hlavně spektrum, šum je jen podklad
	float hot = smoothstep(uH1.z, uH1.z + .25, h);
	float lift = hot * smoothstep(.05, .3, life);                               // cihla nejdřív žhne na místě, pak se z ní uvolní částice
	vec3 v = flow(p * 1.3, t * .4) * uH0.w * .22 * lift + vec3(0., uH1.x * .6 * lift, 0.);
	vec2 away = p.xy - (uR0.w > 0. ? uR0.xy : vec2(0.));
	v.xy += normalize(away + 1e-4) * w * .6 * (.3 + hot);
	p += v * dt;
	oState = vec4(p, life);
	// Point Transform z videa: horké body se otáčí a zvětšují podle hudby (maska = teplo)
	float ang = uH2.x * hot, sc = 1. + uH2.y * hot;
	vec3 q = p;
	q.xy = mat2(cos(ang), -sin(ang), sin(ang), cos(ang)) * q.xy * sc;
	q.z += hot * life * .6;
	float fade = smoothstep(0., .08, life) * smoothstep(1., .55, life);             // stoupající částice vyhasnou dřív → žádný závoj přes celý obraz
	float spark = 1. + uH4.y * step(.93, r.x) * 2.5;                              // hihat: krátké jiskření horkých bodů
	float lum = hot * fade * uH2.w * (1. + uH3.y * .5) * mix(1., .4, lift) * spark;
	vec3 c = mix(vec3(mix(.3, 1., h)), heatRamp(h * (.6 + life * .5)), uH2.z);
	oPos = vec4(q, .7 + hot * .6);
	oCol = vec4(c, clamp(lum, 0., 1.));
}
