// KVĚT — Proudy růstu: z okraje, kde lilie právě raší, se uvolňuje barva a teče ve směru, kterým květ rostl
// (gradient mapy času příchodu), za špičkami okvětních lístků pokračuje ven do prostoru jako protuberance.
// Kopák vypustí celý květ, barva cestou pomalu mění odstín.
// vstup 0 = předchozí snímek (Feedback TOP), vstup 1 = mapa času příchodu, vstup 2 = Texture 3D se všemi fázemi
uniform vec4 uG0;   // čas, rychlost proudění, útlum, síla vpouštění z okraje
uniform vec4 uG1;   // střed květu x, y, -, poměr stran
uniform vec4 uG2;   // zoom, rozkvět, váha looku, vypuštění celého květu (kopák)
uniform vec4 uG3;   // posun odstínu za snímek, -, -, -
out vec4 fragColor;

vec3 hueRot(vec3 c, float a) {
	float y = dot(c, vec3(.299, .587, .114)), i = dot(c, vec3(.596, -.274, -.322)), q = dot(c, vec3(.211, -.523, .312));
	float ca = cos(a), sa = sin(a); float i2 = i * ca - q * sa, q2 = i * sa + q * ca;
	return max(vec3(y + .956 * i2 + .621 * q2, y - .272 * i2 - .647 * q2, y - 1.106 * i2 + 1.703 * q2), 0.);
}
float arr(vec2 t) { return (t.x < 0. || t.y < 0. || t.x > 1. || t.y > 1.) ? 1. : texture(sTD2DInputs[1], t).r; }

void main() {
	if (uG2.z < .002) { fragColor = vec4(0., 0., 0., 1.); return; }
	float asp = max(uG1.w, .1), zm = max(uG2.x, .1);
	vec2 uv = vUV.st;
	vec2 t = uG1.xy + (uv - .5) * vec2(asp, 1.) / zm;
	float a = arr(t);
	const float e = .012;
	vec2 g = vec2(arr(t + vec2(e, 0.)) - arr(t - vec2(e, 0.)), arr(t + vec2(0., e)) - arr(t - vec2(0., e)));
	vec2 rad = t - uG1.xy;
	vec2 dir = normalize(rad + vec2(1e-5));
	float gl = length(g);
	if (gl > .004) dir = normalize(mix(dir, g / gl, smoothstep(.004, .03, gl)));   // směr růstu (pupen → špičky)
	float sw = sin(atan(rad.y, rad.x) * 7. + uG0.x * .9) * .35;                   // lehké vlnění proudů
	dir = normalize(dir + vec2(-dir.y, dir.x) * sw);
	vec2 duv = dir * zm / vec2(asp, 1.);
	vec2 px = 1. / max(uTDOutputInfo.res.zw, vec2(1.));
	vec2 bk = duv * uG0.y * px.y;
	vec3 prev = (texture(sTD2DInputs[0], uv - bk).rgb * .6 + texture(sTD2DInputs[0], uv - bk * 1.5).rgb * .4);
	prev = hueRot(prev, uG3.x) * clamp(uG0.z, 0., .995);
	vec3 lily = (t.x < 0. || t.y < 0. || t.x > 1. || t.y > 1.) ? vec3(0.)
		: texture(sTD3DInputs[0], vec3(t, (clamp(uG2.y, 0., 1.) * 63. + .5) / 64.)).rgb;
	float front = exp(-pow((a - uG2.y) / .05, 2.)) * step(a, .97);
	vec3 inj = lily * smoothstep(.1, .3, dot(lily, vec3(.3, .5, .2))) * (front * uG0.w + uG2.w);
	fragColor = vec4(max(prev, inj), 1.);
}
