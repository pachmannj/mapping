// KVĚT — skutečná lilie (časosběr Mixkit 34700, 64 fází rozkvětu v Texture 3D): hudba řídí, jak moc je rozkvetlá.
// Netradiční looky: každý prstenec / výseč květu je v jiné fázi rozkvětu podle svého frekvenčního pásma,
// ozvěna několika fází přes sebe. vstup 0 = Texture 3D se všemi fázemi (vrstva 0 = pupen, 63 = rozkvetlá)
uniform vec4 uB0;   // základní rozkvět (0–1), síla spektrálních kruhů, síla výsečí, síla ozvěny
uniform vec4 uB1;   // střed květu v textuře x, y, poloměr květu, počet výsečí
uniform vec4 uB2;   // vlna kopáku (poloměr), síla vlny, posun odstínu (0 = přirozené barvy), sytost posunu
uniform vec4 uB3;   // zoom, natočení (rad), jas, poměr stran
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;   // 12 frekvenčních pásem
out vec4 fragColor;

float band(float i) {                                  // jen desetinná čísla (int z NaN shodí Vulkan na Macu)
	i = clamp(i, 0., 11.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(i, 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
float bandS(float x) {                                 // plynule mezi pásmy
	x = clamp(x, 0., 11.);
	return mix(band(floor(x)), band(min(floor(x) + 1., 11.)), smoothstep(0., 1., fract(x)));
}
vec3 hueRot(vec3 c, float a) {
	float y = dot(c, vec3(.299, .587, .114)), i = dot(c, vec3(.596, -.274, -.322)), q = dot(c, vec3(.211, -.523, .312));
	float ca = cos(a), sa = sin(a); float i2 = i * ca - q * sa, q2 = i * sa + q * ca;
	return max(vec3(y + .956 * i2 + .621 * q2, y - .272 * i2 - .647 * q2, y - 1.106 * i2 + 1.703 * q2), 0.);
}
vec3 phase(vec2 t, float w) {
	if (t.x < 0. || t.y < 0. || t.x > 1. || t.y > 1.) return vec3(0.);
	return texture(sTD3DInputs[0], vec3(t, (clamp(w, 0., 1.) * 63. + .5) / 64.)).rgb;
}

void main() {
	float asp = max(uB3.w, .1);
	vec2 q = (vUV.st - .5) * vec2(asp, 1.) / max(uB3.x, .1);
	float ca = cos(uB3.y), sa = sin(uB3.y);
	q = mat2(ca, -sa, sa, ca) * q;
	vec2 c = uB1.xy, t = c + q;                                 // souřadnice v textuře květu
	vec2 d = t - c;
	float r = length(d) / max(uB1.z, .05);                     // 0 = střed květu, 1 = okraj
	float ang = atan(d.y, d.x) / 6.2831853 + .5;
	float w = uB0.x;
	w -= uB0.y * (1. - bandS(r * 11.)) * 1.1;                  // kruhy: střed = basy, okraj = výšky
	w -= uB0.z * (1. - band(floor(ang * uB1.w) * 11. / max(uB1.w - 1., 1.))) * 1.2;   // výseče: každá své pásmo
	w += uB2.y * exp(-pow((r - uB2.x) / .12, 2.));             // vlna kopáku: prstenec se na okamžik rozvine
	vec3 col = phase(t, w);
	if (uB0.w > .01) {                                         // ozvěna: starší fáze přes sebe, barevně posunuté
		col = max(col, hueRot(phase(t, w - .28), 1.1) * .75 * uB0.w);
		col = max(col, hueRot(phase(t, w - .56), 2.2) * .5 * uB0.w);
	}
	col = mix(col, hueRot(col, uB2.z), uB2.w);
	fragColor = TDOutputSwizzle(vec4(col * uB3.z, 1.));
}
