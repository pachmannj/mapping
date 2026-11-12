// KVĚT — generativní 3D květ: každá instance mřížky = jeden okvětní lístek (nebo semínko ve středu).
// Lístky jsou rozmístěné zlatým úhlem (fylotaxe), vnější kruhy reagují na basy, vnitřní na výšky.
// Osa květu míří ke kameře (+z); zavřený pupen = lístky podél osy, rozkvetlý = lístky do stran.
uniform vec4 uF0;   // počet instancí, rozkvět (0–1.2), velikost, čas
uniform vec4 uF1;   // vlna kopáku (poloha 0–1.5 od středu ven), síla vlny, zkroucení, chvění špiček
uniform vec4 uF2;   // odstín, sytost, jas, natočení květu (rad)
uniform vec4 uF3;   // prohnutí lístku do misky, zahnutí špičky ven, režim (0 lístky, 1 semínka), -
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;   // 12 frekvenčních pásem
out Vertex { vec3 col; vec2 uv; float a; float mode; } oVert;

float band(float i) {                                  // jen desetinná čísla (int z NaN shodí Vulkan na Macu)
	i = clamp(i, 0., 11.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(i, 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }

void main() {
	float N = max(uF0.x, 1.);
	float i = float(TDInstanceID());
	vec3 P0 = TDPos();                                    // mřížka 1×1: x = napříč lístkem, y = podél lístku
	float u = P0.x, v = P0.y + .5;
	float ri = sqrt((i + .5) / N);                        // 0 = střed, 1 = vnější okraj
	float az = i * 2.39996323 + uF2.w + uF1.z * ri;      // zlatý úhel + natočení + zkroucení virblem
	vec3 radial = vec3(cos(az), sin(az), 0.), tang = vec3(-sin(az), cos(az), 0.);
	float b = mix(band(floor((1. - ri) * 11.)), band(min(floor((1. - ri) * 11.) + 1., 11.)), fract((1. - ri) * 11.));  // vnější = basy
	float wave = exp(-pow((ri - uF1.x) / .12, 2.)) * uF1.y;   // vlna kopáku putuje od středu ven
	vec3 pos; vec3 col; float alpha;
	if (uF3.z < .5) {
		// ── lístek ──
		float bl = clamp(uF0.y * (.55 + ri * .65) + b * .35 + wave * .4, 0., 1.25);
		float tilt = mix(.12, 1.62, bl) * mix(.75, 1., ri);   // úhel od osy květu
		vec3 dir = radial * sin(tilt) + vec3(0., 0., cos(tilt));
		vec3 nrm = cross(dir, tang);
		float L = mix(.1, .78, pow(ri, .8)) * uF0.z * (1. + wave * .35 + b * .18);
		float W = L * mix(.45, .72, ri);
		float prof = sin(3.14159 * pow(clamp(v, 0., 1.), .7));    // tvar lístku: úzký u základny, široký uprostřed, špička
		float x = u * 2. * W * .5 * prof;
		float along = v * L;
		float up = pow(abs(u * 2.), 2.) * W * .3 * uF3.x                     // miska
		         - v * v * L * .3 * uF3.y * bl                                // špička se zahne ven
		         + sin(uF0.w * 9. + i * 1.7) * uF1.w * v * v * .04;           // chvění na hihat
		vec3 base = radial * (.02 + ri * .06) * uF0.z;
		pos = base + tang * x + dir * along + nrm * up;
		vec3 c0 = mix(vec3(1.), hue(uF2.x + ri * .25), uF2.y);
		vec3 c1 = mix(vec3(1.), hue(uF2.x + .08 + ri * .25 + b * .1), uF2.y * .8);
		col = mix(c0 * .35, c1, v) * (1. + wave * .6);
		alpha = (.3 + b * .55 + wave * .4) * smoothstep(0., .08, v) * 2.2 / sqrt(N);   // víc lístků přes sebe = každý slabší (aditivní míchání)
		oVert.uv = vec2(u * 2., v);
	} else {
		// ── semínka ve středu (spirála jako slunečnice) ──
		float r = sqrt((i + .5) / N) * .13 * uF0.z * (1. + wave * .4);
		vec3 c = vec3(cos(i * 2.39996323 + uF2.w * .5), sin(i * 2.39996323 + uF2.w * .5), 0.) * r;
		c.z = (.13 * uF0.z - r) * .6 * (1. + uF0.y * .3);
		float s = (.006 + .008 * (1. - r / (.13 * uF0.z + 1e-4))) * uF0.z * (1. + wave * 1.5 + b * .5);
		pos = c + vec3(u, v - .5, 0.) * s * 2.;
		col = mix(vec3(1., .95, .8), hue(uF2.x + .55), uF2.y * .6) * (1. + wave * 2.);
		alpha = .55 + wave;
		oVert.uv = vec2(u * 2., (v - .5) * 2.);
	}
	gl_Position = TDWorldToProj(TDDeform(vec4(pos, 1.)));
	oVert.col = col * uF2.z; oVert.a = alpha; oVert.mode = uF3.z;
}
