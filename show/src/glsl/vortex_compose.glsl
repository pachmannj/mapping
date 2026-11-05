// VORTEX — kompozice: jas, jemné vnitřní žilky v nejjasnějších místech, vinětace, filmové tónování.
// Oproti webu bez zrna a bez barevného podkladu: na průhledném plátně musí černá zůstat černá.
// vstup 0 = render částic
uniform vec4 uC0;   // jas, teplota barvy, čas, intenzita
out vec4 fragColor;

float hash21(vec2 p) { p = fract(p * vec2(234.34, 435.345)); p += dot(p, p + 34.23); return fract(p.x * p.y); }
float noise2(vec2 p) {
	vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
	return mix(mix(hash21(i), hash21(i + vec2(1, 0)), f.x), mix(hash21(i + vec2(0, 1)), hash21(i + vec2(1, 1)), f.x), f.y);
}
float fbm(vec2 p) { float v = 0., a = .5; for (int i = 0; i < 4; i++) { v += noise2(p) * a; p *= 2.1; a *= .5; } return v; }

void main() {
	vec2 res = uTDOutputInfo.res.zw;
	vec3 c = texture(sTD2DInputs[0], vUV.st).rgb * uC0.x;
	float lum = dot(c, vec3(.299, .587, .114));
	float t = uC0.z * .04;
	vec2 uv = vUV.st * vec2(res.x / res.y, 1.);
	float a1 = fbm(uv * 3. + t * .15) * 6.2832;
	float s1 = fbm(uv * 6. + vec2(cos(a1), sin(a1)) * 2. + t * .08);
	c *= 1. - smoothstep(.46, .54, s1) * smoothstep(.25, .5, lum) * (1. - smoothstep(.8, 1.3, lum)) * .2;
	c *= 1. - smoothstep(.25, .9, distance(vUV.st, vec2(.5))) * .7;
	c = c * (1. + c * .5) / (1. + c);
	fragColor = TDOutputSwizzle(vec4(max(c, 0.), 1.));
}
