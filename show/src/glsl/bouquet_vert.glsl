// KYTICE — body jako měkké tečky s hloubkou ostrosti: mimo rovinu ostrosti se tečka zvětší (kroužek rozostření)
// a úměrně zeslábne (stejná energie světla) → rozmazané světelné skvrny jako z objektivu.
// sPos: xyz = poloha, w = násobek velikosti · sCol: rgb = barva (předem vynásobená jasem)
uniform sampler2D sPos;
uniform sampler2D sCol;
uniform vec4 uI0;   // velikost bodu (px), šířka a výška renderu (px), -
uniform vec4 uD0;   // vzdálenost ostrosti, clona (px rozostření na jednotku), max. rozostření (px), -
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
	float base = uI0.x * P.w * clamp(3.5 / max(depth, .2), .4, 3.);
	float coc = min(abs(depth - uD0.x) / max(depth, .2) * uD0.y, max(uD0.z, 0.));
	float px = max(base + coc, .75);
	float k = pow(base / px, 1.3);                       // skoro zachování energie: větší skvrna = slabší (ne úplně, ať obraz netmavne)
	cp.xy += q.xy * 2. * px / max(uI0.yz, vec2(1.)) * cp.w;   // max: před nastavením uniform je rozlišení 0
	float lum = max(C.r, max(C.g, C.b)) * k;
	if (lum < .0008 || depth < .1) cp = vec4(2., 2., 2., 1.);
	gl_Position = cp;
	oVert.col = vec4(C.rgb * k, 1.); oVert.q = q.xy * 2.;
}
