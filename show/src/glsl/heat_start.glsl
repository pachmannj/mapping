// HEAT 2.0 — výchozí polohy: milion bodů rozložených do cihlové mřížky (každý pixel = jeden bod)
// (myšlenka: ramp → reorder → mřížka bodů + malý náhodný šum, supermarket sallad)
uniform vec4 uH0;   // počet řad cihel, poměr stran, mezera mezi cihlami (0–1), -
layout(location = 0) out vec4 oStart;

uvec3 pcg3d(uvec3 v) {
	v = v * 1664525u + 1013904223u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	v ^= v >> 16u;
	v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
	return v;
}
vec3 rnd3(uvec3 v) { return vec3(pcg3d(v)) * (1. / 4294967295.); }

void main() {
	vec3 r = rnd3(uvec3(gl_FragCoord.xy, 5u));
	float asp = uH0.y, rows = uH0.x, bs = 2. / rows;
	vec2 p = vec2(vUV.s * 2. - 1., vUV.t * 2. - 1.);           // čtverec −1…1
	p.x *= asp;
	float row = floor((p.y + 1.) / bs);
	float off = mod(row, 2.) > .5 ? bs * .5 : 0.;
	vec2 cell = vec2(floor((p.x + asp + off) / bs), row);
	vec2 local = fract(vec2((p.x + asp + off) / bs, (p.y + 1.) / bs));
	local = (local - .5) * (1. - uH0.z) + .5;                    // mezera mezi cihlami (spára)
	vec2 q = vec2((cell.x + local.x) * bs - asp - off, (cell.y + local.y) * bs - 1.);
	q += (r.xy - .5) * .002;
	oStart = vec4(q, (r.z - .5) * .02, r.z);                     // w = náhodné číslo bodu
}
