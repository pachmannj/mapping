// INSTANCOVÁNÍ — měkká tečka, aditivní míchání
in Vertex { vec4 col; vec2 q; } iVert;
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
void main() {
	float r2 = dot(iVert.q, iVert.q);
	if (r2 > 1.) discard;
	float a = exp(-r2 * 3.) * iVert.col.a;
	fragColor[0] = TDOutputSwizzle(vec4(iVert.col.rgb * a, 1.));
}
