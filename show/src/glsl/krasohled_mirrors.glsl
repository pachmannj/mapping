// KRASOHLED 2.0 — kaskáda zrcadel (myšlenka: 5× Mirror TOP s úhly 0°, 90°, 45°, 180°, 90°, Acrylicode)
// Každé zrcadlo „přeloží“ obraz podél přímky středem pod svým úhlem; několik za sebou = kaleidoskop.
// vstup 0 = render tunelu
uniform vec4 uM0;   // úhly zrcadel 1–4 (stupně)
uniform vec4 uM1;   // úhel zrcadla 5, počet aktivních zrcadel (0–5), poměr stran, -
out vec4 fragColor;

vec2 fold(vec2 p, float deg) {
	float a = radians(deg);
	vec2 n = vec2(cos(a), sin(a));                     // normála zrcadla
	float d = dot(p, n);
	return d < 0. ? p - 2. * d * n : p;               // co je za zrcadlem, se překlopí na druhou stranu
}

void main() {
	float asp = uM1.z;
	vec2 p = (vUV.st - .5) * vec2(asp, 1.);
	float n = uM1.y;                                   // bez polí a cyklů: dynamické indexování lokálního pole shodí Vulkan na Macu
	if (n > .5) p = fold(p, uM0.x);
	if (n > 1.5) p = fold(p, uM0.y);
	if (n > 2.5) p = fold(p, uM0.z);
	if (n > 3.5) p = fold(p, uM0.w);
	if (n > 4.5) p = fold(p, uM1.x);
	vec2 uv = p / vec2(asp, 1.) + .5;
	fragColor = TDOutputSwizzle(texture(sTD2DInputs[0], uv));
}
