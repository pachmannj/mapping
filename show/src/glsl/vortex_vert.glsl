// VORTEX — vertex shader materiálu: každá instance obdélníku = jedna částice z textury simulace.
// Režim 0 = měkká tečka, režim 1 = stopa (čára od aktuální polohy proti směru pohybu).
uniform sampler2D sPos;
uniform sampler2D sVel;
uniform vec4 uV0;   // teplota barvy, intenzita, režim, velikost teček
uniform vec4 uV1;   // šířka a výška renderu (px), délka stopy, -
out Vertex { vec3 col; vec2 q; float b; float mode; } oVert;

void main() {
	int id = TDInstanceID();
	ivec2 ts = textureSize(sPos, 0);
	ivec2 tc = ivec2(id % ts.x, id / ts.x);
	vec4 P = texelFetch(sPos, tc, 0), V = texelFetch(sVel, tc, 0);
	vec3 q = TDPos();
	float life = P.w, speed = length(V.xyz), dist = length(P.xyz);
	mat4 cam = uTDMats[TDCameraIndex()].cam, proj = uTDMats[TDCameraIndex()].proj;
	vec4 c0 = cam * vec4(P.xyz, 1.);
	float depth = -c0.z, warm = uV0.x, inten = uV0.y;
	float layer = dist < .5 ? 0. : (dist < 1.2 ? 1. : 2.);
	vec3 cool = layer < .5 ? vec3(.4, .2, .95) : (layer < 1.5 ? vec3(.2, .15, .7) : vec3(.6, .65, .95));
	vec3 hot = layer < .5 ? vec3(1., .9, .2) : (layer < 1.5 ? vec3(1., .55, .1) : vec3(1., .85, .5));
	vec3 col = mix(cool, hot, warm);
	vec2 res = uV1.xy;
	vec4 cp;
	float b;
	if (uV0.z < .5) {
		col = mix(col, vec3(.95, .93, .9), speed * .12);
		col = mix(col, vec3(1.), inten * .25);
		float ls = layer < .5 ? 2. : (layer < 1.5 ? 1.4 : .8);
		float base = (ls + speed * .15) * (1. + inten * .35);
		float px = clamp(base * 85. / max(depth, .5), 1., 14.) * uV0.w * res.y / 900.;
		cp = proj * c0;
		cp.xy += q.xy * 2. * px / res * cp.w;
		float layerDim = layer < .5 ? .1 : (layer < 1.5 ? .18 : .3);
		b = life * (layerDim + smoothstep(0., 2., speed) * .6) / (1. + depth * .08);
	} else {
		col = mix(col, vec3(1.), inten * .2);
		vec3 tail = P.xyz - V.xyz * uV1.z;
		vec4 a = proj * c0, e = proj * cam * vec4(tail, 1.);
		float t = q.x + .5;
		cp = mix(a, e, t);
		vec2 d = (e.xy / max(e.w, 1e-3) - a.xy / max(a.w, 1e-3)) * res;
		vec2 n = normalize(vec2(-d.y, d.x) + 1e-6);
		cp.xy += n * q.y * 2. * 1.2 / res * cp.w;
		b = life * (1. - t * .6) * (.15 + smoothstep(0., 2., speed) * .5) / (1. + depth * .07);
	}
	if (life <= 0. || depth < .1) cp = vec4(2., 2., 2., 1.);
	gl_Position = cp;
	oVert.col = col; oVert.q = q.xy * 2.; oVert.b = b; oVert.mode = uV0.z;
}
