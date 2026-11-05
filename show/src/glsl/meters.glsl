// UI — měřáky zvuku: 6 pásem (sub, kopák, basy, středy, výšky, vzduch) + kopák/virbl/hihat + energie, hustota, vstup
uniform vec4 uA0;
uniform vec4 uA1;
uniform vec4 uA2;
out vec4 fragColor;
void main() {
	float vals[12] = float[12](uA0.x, uA0.y, uA0.z, uA0.w, uA1.x, uA1.y, uA1.z, uA1.w, uA2.x, uA2.y, uA2.z, uA2.w);
	vec2 uv = vUV.st;
	int i = int(floor(uv.x * 12.));
	float fx = fract(uv.x * 12.);
	float v = clamp(vals[min(i, 11)], 0., 1.);
	vec3 col = i < 6 ? vec3(.35, .75, 1.) : (i < 9 ? vec3(1., .55, .2) : vec3(.6, 1., .5));
	if (i == 11) col = v > .5 ? vec3(.3, 1., .3) : vec3(1., .2, .2);   // vstup: zelená = je signál
	float bar = step(.12, fx) * step(fx, .88) * step(uv.y, v);
	float bg = step(.12, fx) * step(fx, .88) * .08;
	fragColor = TDOutputSwizzle(vec4(col * bar + vec3(bg), 1.));
}
