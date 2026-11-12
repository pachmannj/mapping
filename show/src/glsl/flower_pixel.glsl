// KVĚT — průsvitný zářící lístek: světlejší okraj, žilky podél lístku, aditivně (na černém pozadí jako světlo)
in Vertex { vec3 col; vec2 uv; float a; float mode; } iVert;
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
void main() {
	vec2 uv = iVert.uv;
	float a;
	if (iVert.mode < .5) {
		float edge = smoothstep(.55, 1., abs(uv.x));                      // okraj lístku září
		float vein = pow(.5 + .5 * cos(uv.x * 22.), 6.) * .35 * (1. - uv.y * .5);
		float mid = (1. - smoothstep(0., .08, abs(uv.x))) * .5;          // střední žilka
		a = iVert.a * (.18 + edge * .9 + vein + mid);
	} else {
		float r = length(uv);
		if (r > 1.) discard;
		a = iVert.a * exp(-r * r * 2.5);
	}
	fragColor[0] = TDOutputSwizzle(vec4(iVert.col * a, 1.));
}
