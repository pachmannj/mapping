// VORTEX 2.0 — síly organismu jako GLSL POP uvnitř smyčky Particle POP (myšlenka: POP částice, nicholaspjm)
// Particle POP rodí částice ze zvukové vlny a integruje P += PartVel; tady se počítá zrychlení, barva a velikost.
// Logika sil je z webové verze Vortex Organism (víry, soudržnost, komprese, curl turbulence, nástupy nástrojů).
uniform vec4 uS0;   // čas, dt, energie, transient
uniform vec4 uS1;   // kopák, virbl, hihat, činel
uniform vec4 uS2;   // vokál, sub-basa, držený tón, rytmus
uniform vec4 uS3;   // nástup kopáku, nástup virblu, nástup hihatu, auto intenzita
uniform vec4 uS4;   // turbulence, hustota, reaktivita, síla komprese
uniform vec4 uS5;   // klid, napětí, výbuch, kolaps
uniform vec4 uS6;   // obnova, teplota barvy, intenzita, jas
uniform vec4 uS7;   // vír 0 (xyz), velikost částic
uniform vec4 uS8;   // vír 1
uniform vec4 uS9;   // vír 2
uniform vec4 uS10;  // střed komprese
uniform vec4 uL0; uniform vec4 uL1; uniform vec4 uL2;   // 12 frekvenčních pásem (jako laloky Krasohledu)

uvec3 pcg3d(uvec3 v) {
	v = v * 1664525u + 1013904223u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	v ^= v >> 16u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	return v;
}
vec3 rnd3(uvec3 v) { return vec3(pcg3d(v)) * (2. / 4294967295.) - 1.; }
float band(float i) {                                  // jen desetinná čísla (int z NaN shodí Vulkan na Macu)
	i = mod(clamp(i, 0., 11.99), 12.);
	vec4 v = i < 3.5 ? uL0 : (i < 7.5 ? uL1 : uL2);
	float j = mod(floor(i), 4.);
	return j < .5 ? v.x : (j < 1.5 ? v.y : (j < 2.5 ? v.z : v.w));
}
vec3 sn(vec3 v) { return v / max(length(v), 1e-5); }
vec3 hash33(vec3 p) {
	p = vec3(dot(p, vec3(127.1, 311.7, 74.7)), dot(p, vec3(269.5, 183.3, 246.1)), dot(p, vec3(113.5, 271.9, 124.6)));
	return fract(sin(p) * 43758.5453) * 2. - 1.;
}
float noise3(vec3 p) {
	vec3 i = floor(p), f = fract(p);
	f = f * f * (3. - 2. * f);
	float a = dot(hash33(i), f), b = dot(hash33(i + vec3(1, 0, 0)), f - vec3(1, 0, 0));
	float c = dot(hash33(i + vec3(0, 1, 0)), f - vec3(0, 1, 0)), d = dot(hash33(i + vec3(1, 1, 0)), f - vec3(1, 1, 0));
	float e = dot(hash33(i + vec3(0, 0, 1)), f - vec3(0, 0, 1)), g = dot(hash33(i + vec3(1, 0, 1)), f - vec3(1, 0, 1));
	float h = dot(hash33(i + vec3(0, 1, 1)), f - vec3(0, 1, 1)), j = dot(hash33(i + vec3(1, 1, 1)), f - vec3(1, 1, 1));
	return mix(mix(mix(a, b, f.x), mix(c, d, f.x), f.y), mix(mix(e, g, f.x), mix(h, j, f.x), f.y), f.z);
}
vec3 curl(vec3 p) {
	const float e = .1;
	float dy = (noise3(p + vec3(0, e, 0)) - noise3(p - vec3(0, e, 0))) / (2. * e);
	float dz = (noise3(p + vec3(0, 0, e)) - noise3(p - vec3(0, 0, e))) / (2. * e);
	float dx = (noise3(p + vec3(e, 0, 0)) - noise3(p - vec3(e, 0, 0))) / (2. * e);
	return vec3(dy - dz, dz - dx, dx - dy);
}
vec3 fbmCurl(vec3 p, float t) {
	vec3 c = vec3(0.); float amp = 1., freq = 1.;
	for (int i = 0; i < 3; i++) { c += curl(p * freq + vec3(t * .1 * float(i + 1))) * amp; freq *= 2.; amp *= .5; }
	return c;
}

void main() {
	const uint id = TDIndex();
	if (id >= TDNumElements()) return;
	vec3 p = TDIn_P(), v = TDIn_PartVel();
	float age = TDIn_PartAge(), life = max(TDIn_PartLifeSpan(), .001);
	uint pid = uint(TDIn_PartId());
	float seed = rnd3(uvec3(pid, 7u, 3u)).x * .5 + .5;
	float uTime = uS0.x, dt = min(uS0.y, .033), uEnergy = uS0.z, uTransient = uS0.w;
	float uKick = uS1.x, uSnare = uS1.y, uHihat = uS1.z, uCymbal = uS1.w;
	float uVocal = uS2.x, uSubBass = uS2.y, uSustained = uS2.z, uRhythm = uS2.w;
	float uKickTrans = uS3.x, uSnareTrans = uS3.y, uHihatTrans = uS3.z, uAuto = uS3.w;
	float uTurb = uS4.x, uDensity = uS4.y, react = uS4.z, uComp = uS4.w;
	float uCalm = uS5.x, uBurst = uS5.z, uCollapse = uS5.w, uRegen = uS6.x;
	float dist = length(p);
	float intensity = max(uAuto, clamp(uEnergy * 4., 0., 1.));

	float rotSpeed = .35 + uCalm * .3 + uAuto * .4 + uKick * react * 1.5 + uVocal * react * .4 + uSubBass * react * .8 + uBurst * .5;
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
	float radial = -.6 * uDensity * (1. - intensity * .2) + uKickTrans * react * 1.5 - uCollapse * .8 - uSustained * react * .3;
	radial += smoothstep(1., 2., dist) * (-1.2) * uDensity;
	radial += (1. - smoothstep(0., .7, dist)) * 1.1 * uDensity;
	// spektrum: každé z 12 pásem tlačí plášť organismu ve svém směru (úhel kolem svislé osy) → tvar se mění s každou změnou v hudbě
	float sec = (atan(p.z, p.x) / 6.2831853 + .5) * 12.;
	float bnd = mix(band(floor(sec)), band(mod(floor(sec) + 1., 12.)), smoothstep(0., 1., fract(sec)));
	radial += (bnd - .4) * 2.2 * react * smoothstep(.25, 1., dist);
	vec3 radialF = sn(p + .001) * radial;
	vec3 toCo = uS10.xyz - p;
	float cd = length(toCo);
	float cf = uComp * 1.5 / (1. + cd * .5) + uKick * react * 2. / (1. + cd * .3) + uSubBass * react;
	vec3 compression = sn(toCo + vec3(.001)) * cf * .7 + sn(cross(toCo + vec3(.001), vec3(0, 1, 0))) * cf * .3;
	float nScale = .35 + uHihat * react * .8 + uCymbal * react;
	float nTime = uTime * (.1 + uVocal * react * .4 + uHihat * react * .5);
	float curlStr = .3 + .25 * uTurb + uAuto * .3 * uTurb + uKick * react * .8 * uTurb + uSnare * react * 1.2 + uHihat * react * .8 + uCymbal * react + uBurst * .5;
	vec3 turb = fbmCurl(p * nScale, nTime) * curlStr;
	float kd = uKick * react * 2.5, rp = uRhythm * 6.2832;
	vec3 kickShape = vec3(p.x * sin(rp) * kd * .3, -p.y * kd * .7, p.z * cos(rp) * kd * .3);
	vec3 snareForce = sn(cross(p, vec3(sin(uTime * 2.3), cos(uTime * 1.7), 0.))) * uSnareTrans * react * 3.;
	float vocalWave = sin(dist * 3. - uTime * .6) * uVocal * react * .8 + sin(uTime * .3) * .08 * uCalm;
	float ss = uSustained * react * .5;
	vec3 vertical = vec3(p.x * ss * .3, vocalWave, p.z * ss * .3);
	float tw = uKick * react * 1.2 + uKickTrans * react * 1.5;
	vec3 twist = vec3(-p.z * sin(rp), 0., p.x * sin(rp)) * tw * (1. - smoothstep(0., 2., dist));
	twist += vec3(p.z * cos(rp * 2.), 0., -p.x * cos(rp * 2.)) * uSnareTrans * react * (1. - smoothstep(0., 1.5, dist));
	float shell = smoothstep(.2, .8, dist);
	vec3 kickBurst = sn(p + .001) * uKickTrans * react * 4.;
	vec3 snareBurst = rnd3(uvec3(pid, uint(uTime * 60.), 11u)) * uSnareTrans * react * 3.5;
	vec3 crackle = rnd3(uvec3(pid, uint(uTime * 60.), 23u)) * (uHihatTrans * 1.5 + uCymbal * .6) * react * shell;
	vec3 cymbalSpin = sn(cross(p, vec3(0, 1, 0)) + 1e-5) * uCymbal * react * .4 * shell;
	vec3 implosion = -sn(p + .001) * uCollapse * dist;
	float ra = atan(p.z, p.x) + uTime * .3;
	vec3 regen = vec3(cos(ra), sin(dist * 3. - uTime) * .3, sin(ra)) * uRegen * .5 * (1. - smoothstep(0., 2., dist));

	v += (vortex + radialF + compression + kickShape + snareForce + turb + vertical + twist
	      + kickBurst + snareBurst + crackle + cymbalSpin + implosion + regen) * dt;
	float damping = .96 - uAuto * .008 - intensity * .01 - uBurst * .008 + uSustained * .008;
	v *= pow(damping, dt * 60.);
	float speed = length(v), maxSpeed = 1.2 + intensity * 3. + uBurst * 3. + uTransient * react * 2.5;
	if (speed > maxSpeed) v *= maxSpeed / speed;
	if (any(isnan(v))) v = vec3(0.);

	float layer = dist < .5 ? 0. : (dist < 1.2 ? 1. : 2.);
	vec3 cool = layer < .5 ? vec3(.4, .2, .95) : (layer < 1.5 ? vec3(.2, .15, .7) : vec3(.6, .65, .95));
	vec3 hot = layer < .5 ? vec3(1., .9, .2) : (layer < 1.5 ? vec3(1., .55, .1) : vec3(1., .85, .5));
	vec3 col = mix(cool, hot, uS6.y);
	col = mix(col, vec3(.95, .93, .9), clamp(speed * .12, 0., 1.));
	col = mix(col, vec3(1.), uS6.z * .25);
	float fade = smoothstep(0., .25, age) * smoothstep(life, life * .6, age);
	float bright = fade * ((layer < .5 ? .25 : (layer < 1.5 ? .35 : .5)) + smoothstep(0., 2., speed) * .7) * uS6.w;
	PartVel[id] = v;
	Color[id] = vec4(col * bright * bright * .025, 1.);                 // jako na webu: jas² (aditivně sečteno přes statisíce částic)
	PointScale[id] = (layer < .5 ? 1.4 : (layer < 1.5 ? 1. : .7)) * (1. + speed * .1) * (1. + intensity * .35) * uS7.w;
}
