// PTÁK — mix looků: reál (fotka + částice), slit-scan, chronofotografie, inkoust; abstraktní looky se obarví podle hudby.
// vstup 0 = reál, 1 = slit-scan, 2 = chronofoto, 3 = inkoust
uniform vec4 uL0;   // váhy: reál, slit-scan, chronofoto, inkoust
uniform vec4 uL1;   // odstín, sytost obarvení slit-scanu, celkový jas, -
out vec4 fragColor;

vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }

void main() {
	vec2 uv = vUV.st;
	vec3 real = texture(sTD2DInputs[0], uv).rgb;
	vec4 sl = texture(sTD2DInputs[1], uv);
	float l = dot(sl.rgb, vec3(.333));
	vec3 slit = mix(sl.rgb, hue(uL1.x + l * .35) * l * 1.5, uL1.y);   // slit-scan: barva podle toho, ze které doby pixel je
	vec3 chrono = texture(sTD2DInputs[2], uv).rgb;
	vec3 ink = texture(sTD2DInputs[3], uv).rgb;
	vec3 c = real * uL0.x + slit * uL0.y + chrono * uL0.z + ink * uL0.w;
	fragColor = TDOutputSwizzle(vec4(max(c, 0.) * uL1.z, 1.));
}
