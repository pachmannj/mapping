// KVĚT — skutečná lilie (časosběr Mixkit 34700, 64 fází rozkvětu v Texture 3D), hudba řídí, jak moc je rozkvetlá.
// Reál: lilie se rozvíjí s energií, kopák ji „nadechne“, okraj růstu (kde právě raší) se rozsvítí na hi-hatech.
// Mapa času: lilie potemní a ukáže svůj vlastní čas růstu jako vrstevnice (izochrony) — každá vrstevnice svítí
// podle svého frekvenčního pásma, spektrum tak proudí po cestách, kudy květ rostl; kopák pošle vlnu od pupenu ven.
// vstup 0 = mapa času příchodu (2D, rozmazaná), vstup 1 = Texture 3D se všemi fázemi (vrstva 0 = pupen)
uniform vec4 uB0;   // rozkvět (0–1), nádech kopáku, záře okraje růstu, váha mapy času
uniform vec4 uB1;   // střed květu v textuře x, y, poloměr květu, počet vrstevnic
uniform vec4 uB2;   // posun vrstevnic, poloha vlny kopáku, síla vlny, odstín
uniform vec4 uB3;   // zoom, váha reálu, jas, poměr stran
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;   // 12 frekvenčních pásem
out vec4 fragColor;

float band(float i) {                                  // jen desetinná čísla (int z NaN shodí Vulkan na Macu)
	i = clamp(i, 0., 11.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(i, 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }
vec3 phase(vec2 t, float w) {
	if (t.x < 0. || t.y < 0. || t.x > 1. || t.y > 1.) return vec3(0.);
	return texture(sTD3DInputs[0], vec3(t, (clamp(w, 0., 1.) * 63. + .5) / 64.)).rgb;
}

void main() {
	float asp = max(uB3.w, .1);
	vec2 t = uB1.xy + (vUV.st - .5) * vec2(asp, 1.) / max(uB3.x, .1);   // souřadnice v textuře květu
	bool inside = t.x > 0. && t.y > 0. && t.x < 1. && t.y < 1.;
	float a = inside ? texture(sTD2DInputs[0], t).r : 1.;              // kdy sem květ dorazí
	float w = uB0.x;
	vec3 real = phase(t, w + uB0.y);
	vec2 bd = min(t, 1. - t);
	float border = smoothstep(.01, .04, min(bd.x, bd.y));              // bez rámečku na okraji textury
	float front = exp(-pow((a - w) / .035, 2.)) * step(a, .97) * border;   // okraj růstu: právě rašící část květu
	vec3 col = real * (1. + front * uB0.z) * uB3.y;

	if (uB0.w > .005) {
		float N = max(uB1.w, 2.);
		float x = a * N - uB2.x;
		float f = fract(x), d = min(f, 1. - f) / max(fwidth(x), 1e-4);
		float line = (1. - smoothstep(.4, 1.6, d)) * step(a, .965) * border;
		float idx = floor(x + .5);
		float bnd = band(mod(idx, 12.));
		vec3 lc = mix(hue(uB2.w + idx * .083), vec3(1., .75, .45), .25) * line * (.15 + bnd * bnd * 2.6);
		float wave = exp(-pow((a - uB2.y) / .025, 2.)) * uB2.z * step(a, .97) * border;
		vec3 fr = vec3(1., .85, .6) * front * 1.4;
		vec3 iso = phase(t, w) * .12 + lc + fr + hue(uB2.w + .5) * wave * 1.5;
		col += iso * uB0.w;
	}
	fragColor = TDOutputSwizzle(vec4(max(col, 0.) * uB3.z, 1.));
}
