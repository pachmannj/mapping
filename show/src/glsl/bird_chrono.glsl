// PTÁK — chronofotografie (jako Étienne-Jules Marey): 6 kopií ptáka z různých okamžiků v jednom obraze.
// vstup 0 = teď, vstupy 1–5 = postupně starší snímky (Time Machine TOP s konstantním posunem)
uniform vec4 uC0;   // počet kopií (1–6), útlum starších, rozptyl odstínu mezi kopiemi, sytost
uniform vec4 uC1;   // základní odstín, záblesk nejnovější kopie (kopák), -, -
out vec4 fragColor;

vec3 hue(float h) { return clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.); }
vec3 tint(vec4 c, float h, float sat) {
	float l = dot(c.rgb, vec3(.333));
	return mix(c.rgb, hue(h) * l * 1.4, sat);
}

void main() {
	vec2 uv = vUV.st;
	float n = uC0.x, dec = uC0.y, spread = uC0.z, sat = uC0.w, h0 = uC1.x;
	vec3 c = tint(texture(sTD2DInputs[0], uv), h0, sat * .4) * (1. + uC1.y);
	float w = 1.;
	if (n > 1.5) { w *= dec; c = max(c, tint(texture(sTD2DInputs[1], uv), h0 + spread, sat) * w); }
	if (n > 2.5) { w *= dec; c = max(c, tint(texture(sTD2DInputs[2], uv), h0 + spread * 2., sat) * w); }
	if (n > 3.5) { w *= dec; c = max(c, tint(texture(sTD2DInputs[3], uv), h0 + spread * 3., sat) * w); }
	if (n > 4.5) { w *= dec; c = max(c, tint(texture(sTD2DInputs[4], uv), h0 + spread * 4., sat) * w); }
	if (n > 5.5) { w *= dec; c = max(c, tint(texture(sTD2DInputs[5], uv), h0 + spread * 5., sat) * w); }
	fragColor = TDOutputSwizzle(vec4(c, 1.));
}
