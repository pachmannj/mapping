// INSTANCOVÁNÍ — sdílený materiál pro Krasohled a Heat: každá instance obdélníku = jeden bod z textury.
// sPos: xyz = poloha, w = násobek velikosti (0 = neviditelný) · sCol: rgba barva
uniform sampler2D sPos;
uniform sampler2D sCol;
uniform vec4 uI0;   // velikost bodu (px), šířka a výška renderu (px), referenční hloubka (0 = stálá velikost)
out Vertex { vec4 col; vec2 q; } oVert;

void main() {
	int id = TDInstanceID();
	ivec2 ts = textureSize(sPos, 0);
	ivec2 tc = ivec2(id % ts.x, id / ts.x);
	vec4 P = texelFetch(sPos, tc, 0), C = texelFetch(sCol, tc, 0);
	vec3 q = TDPos();
	mat4 cam = uTDMats[TDCameraIndex()].cam, proj = uTDMats[TDCameraIndex()].proj;
	vec4 c0 = cam * vec4(P.xyz, 1.);
	float depth = -c0.z;
	vec4 cp = proj * c0;
	float px = uI0.x * P.w * (uI0.w > 0. ? clamp(uI0.w / max(depth, .05), .3, 4.) : 1.);
	cp.xy += q.xy * 2. * max(px, .75) / max(uI0.yz, vec2(1.)) * cp.w;    // max: před nastavením uniform je rozlišení 0 → dělení nulou shodí Vulkan
	if (C.a <= .002 || P.w <= 0. || depth < .05) cp = vec4(2., 2., 2., 1.);
	gl_Position = cp;
	oVert.col = C; oVert.q = q.xy * 2.;
}
