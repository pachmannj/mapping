// MASTER — jas, odříznutí černé (kvůli průhlednému plátnu musí být černá opravdu černá),
// maska plátna s měkkým okrajem, záblesk / stroboskop, blackout a testovací obrazce pro mapování.
// vstup 0 = mix scén
uniform vec4 uM0;   // master jas, odříznutí černé, záblesk, blackout (0–1)
uniform vec4 uM1;   // maska: vlevo, vpravo, nahoře, dole (podíl obrazu)
uniform vec4 uM2;   // měkkost okraje masky, testovací obrazec (0 vyp, 1 mřížka, 2 bílá), -, čas
out vec4 fragColor;

float line(float v, float w) { return 1. - smoothstep(w * .5, w * .5 + 1., abs(v)); }

vec3 pattern(vec2 uv, vec2 res, float m) {
	vec2 px = uv * res;
	float cell = res.y / 9.;                                  // čtvercové buňky: 9 řad na výšku
	vec2 g = mod(px - res * .5 + cell * .5, cell) - cell * .5;  // mřížka vycentrovaná na střed
	float c = max(line(g.x, 1.5), line(g.y, 1.5)) * .55;
	c = max(c, max(line(px.x - res.x * .5, 4.), line(px.y - res.y * .5, 4.)));            // středový kříž
	c = max(c, line(length(px - res * .5) - res.y * .4, 3.));                               // kruh: kontrola poměru stran
	float b = min(min(px.x, res.x - px.x), min(px.y, res.y - px.y));
	c = max(c, step(b, 6.));                                                                // okraj obrazu
	vec3 col = vec3(c);
	float s = res.y * .09;                                    // barevné rohy: orientace při zrcadlení
	if (px.x < s && px.y > res.y - s) col = vec3(1., .1, .1);              // vlevo nahoře  = červená
	if (px.x > res.x - s && px.y > res.y - s) col = vec3(.1, 1., .1);      // vpravo nahoře = zelená
	if (px.x < s && px.y < s) col = vec3(.2, .4, 1.);                      // vlevo dole    = modrá
	if (px.x > res.x - s && px.y < s) col = vec3(1., .9, .1);              // vpravo dole   = žlutá
	float edge = (1. - m) * step(.001, m + .001) * .35;                     // ztmavení mimo masku
	col = mix(col, col * .25 + vec3(.6, .3, 0.) * .3, 1. - m);              // oranžově vyznačená maska
	return col;
}

void main() {
	vec2 uv = vUV.st;
	vec2 res = uTDOutputInfo.res.zw;
	vec3 c = texture(sTD2DInputs[0], uv).rgb * uM0.x;
	float k = uM0.y;
	c = max(c - k, 0.) / max(1. - k, 1e-3);                  // odříznutí černé: šum a závoj zmizí z plátna
	c += uM0.z;
	float f = max(uM2.x, 1e-4);
	float m = smoothstep(uM1.x, uM1.x + f, uv.x) * smoothstep(uM1.y, uM1.y + f, 1. - uv.x)
	        * smoothstep(uM1.w, uM1.w + f, uv.y) * smoothstep(uM1.z, uM1.z + f, 1. - uv.y);
	int tp = int(uM2.y + .5);
	if (tp == 1) { c = pattern(uv, res, m); m = 1.; }
	if (tp == 2) c = vec3(1.);
	c *= m * (1. - uM0.w);
	fragColor = TDOutputSwizzle(vec4(clamp(c, 0., 1.), 1.));
}
