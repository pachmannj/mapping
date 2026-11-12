// KVĚT — složení looků: lilie (reál + mapa času) + časová socha + proudy růstu
// vstup 0 = lilie, 1 = socha, 2 = proudy
uniform vec4 uX0;   // váha proudů, jas, -, -
out vec4 fragColor;

void main() {
	vec2 uv = vUV.st;
	vec3 c = texture(sTD2DInputs[0], uv).rgb + texture(sTD2DInputs[1], uv).rgb + texture(sTD2DInputs[2], uv).rgb * uX0.x * uX0.y;
	fragColor = TDOutputSwizzle(vec4(max(c, 0.), 1.));
}
