// KYTICE — tečka: ostrá je skoro kulatá, rozostřená má plošší „bokeh“ disk s jemným okrajem
in Vertex { vec4 col; vec2 q; } iVert;
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
void main() {
	float r2 = dot(iVert.q, iVert.q);
	if (r2 > 1.) discard;
	float a = smoothstep(1., .55, r2) * (.85 + .15 * r2);
	fragColor[0] = TDOutputSwizzle(vec4(iVert.col.rgb * a * 1.6, 1.));
}
