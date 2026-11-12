// PTÁK — rozpad na částice: každý pixel ptáka je bod, který na úder vystřelí ven a pružinou se vrátí domů.
// vstup 0 = předchozí stav (rg = posun, ba = rychlost), vstup 1 = pták s máchnutím (barva + maska)
// výstup: buffer 0 = stav, buffer 1 = poloha k vykreslení (xyz, velikost), buffer 2 = barva
uniform vec4 uP0;   // čas, dt, síla výbuchu (jen v jednom snímku), tuhost pružiny
uniform vec4 uP1;   // střed výbuchu x, y (svět), turbulence, poměr stran
uniform vec4 uP2;   // viditelnost částic (0–1), jas, -, -
layout(location = 0) out vec4 oState;
layout(location = 1) out vec4 oPos;
layout(location = 2) out vec4 oCol;

uvec3 pcg3d(uvec3 v) {
	v = v * 1664525u + 1013904223u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	v ^= v >> 16u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	return v;
}
vec3 rnd3(uvec3 v) { return vec3(pcg3d(v)) * (1. / 4294967295.); }

void main() {
	vec2 uv = vUV.st;
	float asp = max(uP1.w, .1);
	vec4 st = texture(sTD2DInputs[0], uv);
	vec2 off = st.rg, vel = st.ba;
	if (any(isnan(st))) { off = vec2(0.); vel = vec2(0.); }
	float dt = clamp(uP0.y, 0., .05);
	vec2 home = vec2((uv.x - .5) * 2. * asp, (uv.y - .5) * 2.);
	vec3 r = rnd3(uvec3(gl_FragCoord.xy, 9u));
	if (uP0.z > 0.) {                                      // úder: rozprsknutí od středu ptáka
		vec2 d = home - uP1.xy;
		vec2 dir = d / max(length(d), .02);
		float ang = (r.y - .5) * 1.4;
		dir = mat2(cos(ang), -sin(ang), sin(ang), cos(ang)) * dir;
		vel += dir * uP0.z * (.4 + r.x * 1.2);
	}
	vec3 rt = rnd3(uvec3(gl_FragCoord.xy, uint(uP0.x * 30.)));
	vec2 acc = -off * uP0.w - vel * 2.2 + (rt.xy - .5) * uP1.z;     // pružina domů, tlumení, chvění
	vel += acc * dt;
	off += vel * dt;
	oState = vec4(off, vel);
	vec4 c = texture(sTD2DInputs[1], uv);
	float spread = clamp(length(off) * 3., 0., 1.);
	oPos = vec4(home + off, .1, 1. + spread);
	oCol = vec4(c.rgb / max(c.a, .001), c.a * uP2.x * uP2.y * (1. - spread * .4));
}
