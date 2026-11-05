// VORTEX — pixel shader materiálu: měkká tečka / stopa, aditivní míchání (jako blendFunc SRC_ALPHA, ONE)
in Vertex { vec3 col; vec2 q; float b; float mode; } iVert;
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
void main() {
	float b = iVert.b;
	if (iVert.mode < .5) {
		float r = length(iVert.q) * .5;
		if (r > .5) discard;
		b *= exp(-r * r * 18.);
	}
	fragColor[0] = TDOutputSwizzle(vec4(iVert.col * b * b, 1.));
}
