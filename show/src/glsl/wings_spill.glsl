// KŘÍDLA — stíny, které se rozlévají do krajů: předchozí snímek se posune od středu ven (proudem s jemným vířením),
// zchladne v paletě (ztmavne a zfialoví) a pomalu zhasne; nový obraz křídel se do něj přidá.
// vstup 0 = předchozí snímek (Feedback TOP), vstup 1 = křídla + hejno
uniform vec4 uS0;   // útlum stínů, rychlost rozlévání, čas, poměr stran
out vec4 fragColor;
vec3 noise3(vec3 p) {
	return vec3(sin(p.y * 1.7 + p.z * 1.3 + sin(p.x * 2.1)), sin(p.z * 1.9 + p.x * 1.1 + sin(p.y * 1.7)), 0.);
}
void main() {
	vec2 uv = vUV.st, c = uv - .5;
	vec2 flow = c * uS0.y + noise3(vec3(c * 4., uS0.z * .2)).xy * .0015;
	vec3 prev = texture(sTD2DInputs[0], uv - flow).rgb;
	// chladnutí: jas klesá, barva sklouzne k fialové (jako chladnoucí stopa na termokameře)
	float l = max(prev.r, max(prev.g, prev.b));
	prev = mix(prev, vec3(.35, .05, .6) * l, .06) * clamp(uS0.x, 0., .99);
	vec3 cur = texture(sTD2DInputs[1], uv).rgb;
	fragColor = TDOutputSwizzle(vec4(max(cur, prev * .97) + prev * .03, 1.));
}
