// VÝSTUP — poslední krok po corner pinu (prostor projektoru).
// Testovací obrazec „projektor“: rámeček a úhlopříčky přes celý čip projektoru,
// aby šlo zkontrolovat, kam projektor vůbec svítí (i mimo plátno).
// vstup 0 = namapovaný obraz
uniform vec4 uO0;   // režim (3 = rámeček projektoru), čas, -, -
out vec4 fragColor;

float line(float v, float w) { return 1. - smoothstep(w * .5, w * .5 + 1., abs(v)); }

void main() {
	vec2 uv = vUV.st;
	vec3 c = texture(sTD2DInputs[0], uv).rgb;
	if (int(uO0.x + .5) == 3) {
		vec2 res = uTDOutputInfo.res.zw, px = uv * res;
		float b = min(min(px.x, res.x - px.x), min(px.y, res.y - px.y));
		float l = step(b, 8.);
		l = max(l, line(px.y - px.x * res.y / res.x, 3.));
		l = max(l, line(px.y - (res.x - px.x) * res.y / res.x, 3.));
		l = max(l, max(line(px.x - res.x * .5, 3.), line(px.y - res.y * .5, 3.)));
		c = max(c * .5, vec3(0., 1., 1.) * l);
	}
	fragColor = TDOutputSwizzle(vec4(c, 1.));
}
