// KYTICE — body jako malé měkké tečky. Hloubka ostrosti se dělá ve vrstvách: podle rozostření (kroužek rozostření v px)
// se světlo bodu rozdělí do tří vrstev (ostrá / středně / hodně rozmazaná), které se potom rozmažou jako celé obrázky.
// Body tak zůstávají malé → stálých 60 fps (velké rozmazané tečky přetěžovaly grafiku a obraz se trhal).
// sPos: xyz = poloha, w = násobek velikosti · sCol: rgb = barva (předem vynásobená jasem)
uniform sampler2D sPos;
uniform sampler2D sCol;
uniform vec4 uI0;   // velikost bodu (px), šířka a výška renderu (px), -
uniform vec4 uD0;   // vzdálenost ostrosti, clona (px rozostření na jednotku), rozostření střední vrstvy (px), hodně rozmazané vrstvy (px)
out Vertex { vec4 col; vec2 q; vec3 w; } oVert;

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
	float px = max(uI0.x * P.w * clamp(3.5 / max(depth, .2), .4, 3.), .75);
	float coc = abs(depth - uD0.x) / max(depth, .2) * uD0.y;
	float m1 = max(uD0.z, 1.), m2 = max(uD0.w, m1 + 1.);
	// váhy vrstev: lineárně mezi 0 → m1 → m2
	float w0 = clamp(1. - coc / m1, 0., 1.);
	float w2 = clamp((coc - m1) / (m2 - m1), 0., 1.);
	float w1 = 1. - w0 - w2;
	cp.xy += q.xy * 2. * px / max(uI0.yz, vec2(1.)) * cp.w;   // max: před nastavením uniform je rozlišení 0
	if (max(C.r, max(C.g, C.b)) < .0008 || depth < .1) cp = vec4(2., 2., 2., 1.);
	gl_Position = cp;
	oVert.col = vec4(C.rgb, 1.); oVert.q = q.xy * 2.; oVert.w = vec3(w0, w1, w2);
}
