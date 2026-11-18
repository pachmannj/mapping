// KŘÍDLA — abstraktní pár křídel z peří: každé křídlo = kost (rameno → špička) a z ní vějíř per; vnitřní pera míří dolů,
// vnější (letky) pokračují ve směru kosti a jsou delší. Křídla mávají nahoru a dolů (úhel uW0.y), špičky se při pohybu
// opožďují (ohyb jako u skutečného křídla). Barvy jako termokamera: čím rychleji se část křídla pohybuje, tím je „teplejší“
// (fialová → červená → oranžová → žlutá → bílá). V pozadí hejno špačků z videa, ptáci teplí, jejich stopy chladnou.
// vstup 0 = stav hejna (R pták, G stopa, B hustota)
uniform vec4 uW0;   // čas, úhel mávnutí (rad), rychlost mávání (−1…1), teplo (energie)
uniform vec4 uW1;   // poměr stran, rozpětí, nasávání světla z hejna, jas hejna
uniform vec4 uW2;   // svislá poloha těla, kopák (záblesk), posun palety, jas křídel
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;
out vec4 fragColor;

float band(float i) {
	i = clamp(i, 0., 11.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(i, 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
// termokamera: 0 černá → modrofialová → purpurová → červená → oranžová → žlutá → 1 bílá
vec3 thermal(float t) {
	t = clamp(t, 0., 1.);
	vec3 c = mix(vec3(0.), vec3(.18, .02, .45), smoothstep(0., .18, t));
	c = mix(c, vec3(.75, .0, .65), smoothstep(.15, .38, t));
	c = mix(c, vec3(1., .12, .15), smoothstep(.35, .55, t));
	c = mix(c, vec3(1., .55, .0), smoothstep(.52, .72, t));
	c = mix(c, vec3(1., .92, .25), smoothstep(.7, .88, t));
	return mix(c, vec3(1.), smoothstep(.86, 1., t));
}
float segD(vec2 p, vec2 a, vec2 b, out float h) {
	vec2 pa = p - a, ba = b - a;
	h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0., 1.);
	return length(pa - ba * h);
}
vec2 rot(vec2 v, float a) { float c = cos(a), s = sin(a); return vec2(v.x * c - v.y * s, v.x * s + v.y * c); }

void main() {
	float asp = max(uW1.x, .1);
	vec2 uv = vUV.st, p = (uv - .5) * vec2(asp, 1.);
	p.y -= uW2.x;
	float span = max(uW1.y, .2), ang = uW0.y, vel = uW0.z;
	vec3 col = vec3(0.);
	const float N = 26.;
	float dens = texture(sTD2DInputs[0], uv).b;           // hustota hejna pod tímto místem
	for (int side = 0; side < 2; side++) {
		float sx = side == 0 ? 1. : -1.;
		vec2 q = vec2(p.x * sx, p.y);                       // levé křídlo = zrcadlo pravého
		vec2 sh = vec2(.035, .02);
		vec2 bone = rot(vec2(1., 0.), ang);
		for (int i = 0; i < 26; i++) {
			float t = float(i) / (N - 1.);
			// kost je ohnutá: vnější část se opožďuje za pohybem (drag)
			vec2 bdir = rot(bone, -vel * .35 * t * t);
			vec2 o = sh + bdir * (.46 * span) * pow(t, .85);
			float fa = -(1.45 - 1.3 * pow(t, .7));             // vnitřní pera dolů, letky ve směru kosti
			vec2 fdir = rot(bdir, fa - vel * .25 * (.3 + t));
			float L = (.1 + .3 * pow(t, 1.6)) * span;
			vec2 mid = o + fdir * L * .55;
			vec2 tip = mid + rot(fdir, -vel * .3 * t - .08) * L * .45;   // pero se na konci ohne
			float h1, h2;
			float d = min(segD(q, o, mid, h1), segD(q, mid, tip, h2));
			float w = (.0025 + .003 * t) * (1. - .5 * h2);
			float line = exp(-d / w) + exp(-d / (w * 8.)) * .18;
			float bnd = band(mod(float(i), 12.));
			// teplo: rychlost té části křídla + pásmo + celková energie; nasávání světla z hejna
			float heat = clamp(.15 + abs(vel) * (.2 + .45 * t) * uW0.w + bnd * .25 + uW2.y * .25 + dens * uW1.z, 0., .9);
			col += thermal(heat + uW2.z * .1) * line * (.16 + bnd * .3) * uW2.w;
		}
	}
	// tělo: svislý svítící oválek
	float body = exp(-length(p / vec2(.025, .09)) * 2.2);
	col += thermal(.62 + uW2.y * .3) * body * .9 * uW2.w;
	// hejno špačků: ptáci teplí, stopa chladne
	vec4 f = texture(sTD2DInputs[0], uv);
	col += (thermal(.72 + uW0.w * .15) * f.r + thermal(f.g * .4) * f.g * .35) * uW1.w;
	fragColor = TDOutputSwizzle(vec4(col, 1.));
}
