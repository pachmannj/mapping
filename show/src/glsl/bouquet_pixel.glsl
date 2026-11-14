// KYTICE — tečka; světlo jde do tří vrstev podle rozostření (0 ostrá, 1 středně, 2 hodně rozmazaná)
in Vertex { vec4 col; vec2 q; vec3 w; } iVert;
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
void main() {
	float r2 = dot(iVert.q, iVert.q);
	if (r2 > 1.) discard;
	vec3 c = iVert.col.rgb * smoothstep(1., .3, r2) * 1.6;
	fragColor[0] = TDOutputSwizzle(vec4(c * iVert.w.x, 1.));
	fragColor[1] = TDOutputSwizzle(vec4(c * iVert.w.y, 1.));
	fragColor[2] = TDOutputSwizzle(vec4(c * iVert.w.z, 1.));
}
