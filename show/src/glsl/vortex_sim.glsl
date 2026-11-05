// VORTEX — simulace částic na GPU (port SIM_VS z index (kopie 3).html, místo transform feedbacku ping-pong textury)
// každý pixel = jedna částice; vstup 0 = poloha (xyz, život), vstup 1 = rychlost (xyz, seed)
// výstup: barevný buffer 0 = poloha, buffer 1 = rychlost
uniform vec4 uS0;   // čas, dt, energie, transient
uniform vec4 uS1;   // kopák, virbl, hihat, činel
uniform vec4 uS2;   // vokál, sub-basa, držený tón, rytmus
uniform vec4 uS3;   // nástup kopáku, nástup virblu, nástup hihatu, auto intenzita
uniform vec4 uS4;   // turbulence, hustota, reaktivita, síla komprese
uniform vec4 uS5;   // klid, napětí, výbuch, kolaps
uniform vec4 uS6;   // obnova, počítadlo snímků, -, -
uniform vec4 uS7;   // vír 0 (xyz)
uniform vec4 uS8;   // vír 1
uniform vec4 uS9;   // vír 2
uniform vec4 uS10;  // střed komprese
layout(location = 0) out vec4 oPos;
layout(location = 1) out vec4 oVel;

vec3 hash33(vec3 p) {
	p = vec3(dot(p, vec3(127.1, 311.7, 74.7)), dot(p, vec3(269.5, 183.3, 246.1)), dot(p, vec3(113.5, 271.9, 124.6)));
	return fract(sin(p) * 43758.5453) * 2. - 1.;
}
// celočíselný hash (PCG3D) — sin()-hash s rostoucím časem na GPU ztrácí přesnost a částice by se rodily na stejných místech
uvec3 pcg3d(uvec3 v) {
	v = v * 1664525u + 1013904223u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	v ^= v >> 16u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	return v;
}
vec3 rnd3(uvec3 v) { return vec3(pcg3d(v)) * (2. / 4294967295.) - 1.; }
vec3 sn(vec3 v) { return v / max(length(v), 1e-5); }     // bezpečná normalizace (nulový vektor → 0, ne NaN)
float noise3(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	f = f * f * (3. - 2. * f);
	float a = dot(hash33(i), f), b = dot(hash33(i + vec3(1, 0, 0)), f - vec3(1, 0, 0));
	float c = dot(hash33(i + vec3(0, 1, 0)), f - vec3(0, 1, 0)), d = dot(hash33(i + vec3(1, 1, 0)), f - vec3(1, 1, 0));
	float e = dot(hash33(i + vec3(0, 0, 1)), f - vec3(0, 0, 1)), g = dot(hash33(i + vec3(1, 0, 1)), f - vec3(1, 0, 1));
	float h = dot(hash33(i + vec3(0, 1, 1)), f - vec3(0, 1, 1)), j = dot(hash33(i + vec3(1, 1, 1)), f - vec3(1, 1, 1));
	return mix(mix(mix(a, b, f.x), mix(c, d, f.x), f.y), mix(mix(e, g, f.x), mix(h, j, f.x), f.y), f.z);
}
vec3 curlNoise(vec3 p) {
	const float e = .1;
	float dz_dy = (noise3(p + vec3(0, e, 0)) - noise3(p - vec3(0, e, 0))) / (2. * e);
	float dy_dz = (noise3(p + vec3(0, 0, e)) - noise3(p - vec3(0, 0, e))) / (2. * e);
	float dx_dz = dy_dz;
	float dz_dx = (noise3(p + vec3(e, 0, 0)) - noise3(p - vec3(e, 0, 0))) / (2. * e);
	float dy_dx = dz_dx, dx_dy = dz_dy;
	return vec3(dz_dy - dy_dz, dx_dz - dz_dx, dy_dx - dx_dy);
}
vec3 fbmCurl(vec3 p, float t) {
	vec3 c = vec3(0.); float amp = 1., freq = 1.;
	for (int i = 0; i < 3; i++) { c += curlNoise(p * freq + vec3(t * .1 * float(i + 1))) * amp; freq *= 2.; amp *= .5; }
	return c;
}

void main() {
	vec4 P0 = texture(sTD2DInputs[0], vUV.st), V0 = texture(sTD2DInputs[1], vUV.st);
	vec3 p = P0.xyz, v = V0.xyz;
	float life = P0.w;
	uvec2 pid = uvec2(gl_FragCoord.xy);
	float seed = rnd3(uvec3(pid, 7u)).x * .5 + .5;
	float uTime = uS0.x, dt = min(uS0.y, .033), uEnergy = uS0.z, uTransient = uS0.w;
	float uKick = uS1.x, uSnare = uS1.y, uHihat = uS1.z, uCymbal = uS1.w;
	float uVocal = uS2.x, uSubBass = uS2.y, uSustained = uS2.z, uRhythm = uS2.w;
	float uKickTrans = uS3.x, uSnareTrans = uS3.y, uHihatTrans = uS3.z, uAutoIntensity = uS3.w;
	float uTurbulence = uS4.x, uDensity = uS4.y, react = uS4.z, uCompressStrength = uS4.w;
	float uCalm = uS5.x, uBurst = uS5.z, uCollapse = uS5.w, uRegen = uS6.x;
	float dist = length(p);
	float intensity = max(uAutoIntensity, clamp(uEnergy * 4., 0., 1.));

	// 1. víry
	float rotSpeed = .35 + uCalm * .3 + uAutoIntensity * .4 + uKick * react * 1.5 + uVocal * react * .4 + uSubBass * react * .8 + uBurst * .5;
	vec3 vortex = vec3(0.);
	vec3 ctrs[3]; ctrs[0] = uS7.xyz; ctrs[1] = uS8.xyz; ctrs[2] = uS9.xyz;
	float wts[3]; wts[0] = 1.; wts[1] = .7; wts[2] = .5;
	for (int i = 0; i < 3; i++) {
		vec3 toC = p - ctrs[i];
		float dC = length(toC), infl = 1. / (1. + dC * dC * .8);
		vec3 t1 = sn(cross(toC + vec3(.001), vec3(0., 1., .1 * float(i))));
		vec3 t2 = sn(cross(toC + vec3(.001), vec3(.3, .7, -.2)));
		float bl = sin(uTime * (.15 + float(i) * .07) + dC * 1.5) * .5 + .5;
		vortex += mix(t1, t2, bl) * rotSpeed * infl * wts[i];
	}
	// 2. soudržnost — kopák rozfoukne tvar
	float radial = -.6 * uDensity * (1. - intensity * .2) + uKickTrans * react * 1.5 - uCollapse * .8 - uSustained * react * .3;
	radial += smoothstep(1., 2., dist) * (-1.2) * uDensity;
	radial -= smoothstep(0., .15, dist) * (-.1);
	radial += (1. - smoothstep(0., .7, dist)) * 1.1 * uDensity;          // TD verze: tlak u středu, ať se tvar v tichu nezhroutí do bodu
	vec3 radialF = sn(p + .001) * radial;
	// 2b. komprese
	vec3 toCo = uS10.xyz - p;
	float cd = length(toCo);
	float cf = uCompressStrength * 1.5 / (1. + cd * .5) + uKick * react * 2. / (1. + cd * .3) + uSubBass * react;
	vec3 compression = sn(toCo + vec3(.001)) * cf * .7 + sn(cross(toCo + vec3(.001), vec3(0, 1, 0))) * cf * .3;
	// 3. turbulence
	float nScale = .35 + uHihat * react * .8 + uCymbal * react;
	float nTime = uTime * (.1 + uVocal * react * .4 + uHihat * react * .5);
	float curlStr = .25 * uTurbulence + uAutoIntensity * .3 * uTurbulence + uKick * react * .8 * uTurbulence
	              + uSnare * react * 1.2 + uHihat * react * .8 + uCymbal * react + uBurst * .5;
	curlStr += .3;                                                       // TD verze: i v klidu jemně víří
	vec3 curl = fbmCurl(p * nScale, nTime) * curlStr;
	// 3b. deformace kopákem, 3c. střih virblem
	float kd = uKick * react * 2.5, rp = uRhythm * 6.2832;
	vec3 kickShape = vec3(p.x * sin(rp) * kd * .3, -p.y * kd * .7, p.z * cos(rp) * kd * .3);
	vec3 snareForce = sn(cross(p, vec3(sin(uTime * 2.3), cos(uTime * 1.7), 0.))) * uSnareTrans * react * 3.;
	// 4. vokál / držené tóny
	float breathe = sin(uTime * .3) * .08 * uCalm;
	float vocalWave = sin(dist * 3. - uTime * .6) * uVocal * react * .8;
	float ss = uSustained * react * .5;
	vec3 vertical = vec3(p.x * ss * .3, vocalWave + breathe, p.z * ss * .3);
	// 4b. kroucení
	float tw = uKick * react * 1.2 + uKickTrans * react * 1.5;
	vec3 twist = vec3(-p.z * sin(rp), 0., p.x * sin(rp)) * tw * (1. - smoothstep(0., 2., dist));
	twist += vec3(p.z * cos(rp * 2.), 0., -p.x * cos(rp * 2.)) * uSnareTrans * react * (1. - smoothstep(0., 1.5, dist));
	// 5.–6. nástupy a třpyt
	float shell = smoothstep(.2, .8, dist);
	vec3 kickBurst = sn(p + .001) * uKickTrans * react * 4.;
	vec3 snareBurst = hash33(p * 15. + fract(uTime * .37) * 50.) * uSnareTrans * react * 3.5;
	vec3 hihatCrackle = hash33(p * 80. + fract(uTime * .11) * 60.) * uHihatTrans * react * 1.5 * shell;
	vec3 cymbalShimmer = hash33(p * 100. + fract(uTime * .13) * 70.) * uCymbal * react * .6 * shell;
	vec3 cymbalSpin = sn(cross(p, vec3(0, 1, 0)) + 1e-5) * uCymbal * react * .4 * shell;
	// 7.–8. kolaps a obnova
	vec3 implosion = -sn(p + .001) * uCollapse * dist;
	float ra = atan(p.z, p.x) + uTime * .3;
	vec3 regen = vec3(cos(ra), sin(dist * 3. - uTime) * .3, sin(ra)) * uRegen * .5 * (1. - smoothstep(0., 2., dist));

	v += (vortex + radialF + compression + kickShape + snareForce + curl + vertical + twist
	      + kickBurst + snareBurst + hihatCrackle + cymbalShimmer + cymbalSpin + implosion + regen) * dt;
	float damping = .96 - uAutoIntensity * .008 - intensity * .01 - uBurst * .008 + uSustained * .008;
	v *= pow(damping, dt * 60.);
	float speed = length(v), maxSpeed = 1.2 + intensity * 3. + uBurst * 3. + uTransient * react * 2.5;
	if (speed > maxSpeed) v *= maxSpeed / speed;
	p += v * dt;
	life -= dt * (.03 + uBurst * .04);

	float boundary = 2.8 + uBurst * 1.2;
	bool broken = any(isnan(p)) || any(isinf(p)) || any(isnan(v));
	if (broken || dist > boundary || life <= 0.) {
		vec3 h = rnd3(uvec3(pid, uint(uS6.y) + 101u));
		float layer = fract(seed * 7.37);
		if (layer < .5) p = h * .5 * uDensity;
		else if (layer < .85) { float a = h.x * 6.2832, r = (.5 + h.y * .5) * uDensity; p = vec3(cos(a) * r, h.z * .3, sin(a) * r); }
		else { float a = h.x * 6.2832, ph = acos(h.y), r = (.8 + h.z * .7) * uDensity; p = vec3(sin(ph) * cos(a), cos(ph), sin(ph) * sin(a)) * r; }
		if (uRegen > .3) { float sa = seed * 18.85 + uTime * .5, sr = seed * 2. * uDensity; p = vec3(cos(sa) * sr, (seed - .5) * 1.5, sin(sa) * sr); }
		life = .5 + fract(seed * 13.37) * .5;
		v = broken ? vec3(0.) : v * .1;
	}
	oPos = vec4(p, life);
	oVel = vec4(v, seed);
}
