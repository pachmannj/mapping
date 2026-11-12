// PTÁK — vyříznutí racka z modré oblohy (video Mixkit 45246): obloha je výrazně modrá, pták bílý až šedý.
// výstup: rgb = pták (předem vynásobený maskou), a = maska
uniform vec4 uK0;   // práh modré (od, do), jas, -
out vec4 fragColor;
void main() {
	vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
	float blue = c.b - (c.r + c.g) * .5;                 // jak moc je pixel „obloha“
	float a = 1. - smoothstep(uK0.x, max(uK0.y, uK0.x + .01), blue);
	a *= smoothstep(.0, .02, vUV.s) * smoothstep(1., .98, vUV.s) * smoothstep(.0, .02, vUV.t) * smoothstep(1., .98, vUV.t);
	fragColor = TDOutputSwizzle(vec4(c * a * uK0.z, a));
}
