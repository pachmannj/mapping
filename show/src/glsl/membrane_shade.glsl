// MEMBRÁNA — osvětlení napnuté látky. Rovné plátno je černé (na průhledném plátně neviditelné),
// svítí jen místa, kde se látka napíná přes ruce, obličej a chodidla. Barva se mění podle hudby.
// vstup 0 = ostrý otisk těla, vstup 1 = široký „stan“ (rozmazaný otisk), vstup 2 = vlnění
uniform vec4 uS0;   // síla reliéfu, poměr stanu, síla vlnění, jas
uniform vec4 uS1;   // odstín, sytost, úhel světla, záblesk kopáku
uniform vec4 uS2;   // basy, středy, výšky, energie
out vec4 fragColor;

vec3 hsv(float h, float s, float v) {
	vec3 k = clamp(abs(mod(h * 6. + vec3(0., 4., 2.), 6.) - 3.) - 1., 0., 1.);
	return v * mix(vec3(1.), k, s);
}
float H(vec2 uv) {
	float sharp = texture(sTD2DInputs[0], uv).r, tent = texture(sTD2DInputs[1], uv).r;
	float wave = texture(sTD2DInputs[2], uv).r;
	return max(sharp * .55 + tent * uS0.y, tent * uS0.y * 1.6) + wave * uS0.z;
}

void main() {
	vec2 res = uTDOutputInfo.res.zw, px = 1.5 / max(res, vec2(1.));
	vec2 uv = vUV.st;
	float h = H(uv);
	float dx = H(uv + vec2(px.x, 0.)) - H(uv - vec2(px.x, 0.));
	float dy = H(uv + vec2(0., px.y)) - H(uv - vec2(0., px.y));
	vec3 n = normalize(vec3(-dx * uS0.x * 60., -dy * uS0.x * 60., 1.));
	float stretch = clamp(length(vec2(dx, dy)) * uS0.x * 40., 0., 1.);
	vec3 L = normalize(vec3(cos(uS1.z), sin(uS1.z), .55));
	float diff = max(dot(n, L), 0.);
	float rim = pow(1. - n.z, 1.5);                    // hrany otisku (kde se látka láme)
	float spec = pow(max(dot(reflect(-L, n), vec3(0., 0., 1.)), 0.), 24.);   // lesk lycry
	float lift = smoothstep(.002, .04, h);             // jak moc je látka vyboulená
	// barva podle hudby: basy teplé, výšky studené, odstín se posouvá s výškou otisku
	float hue = uS1.x + h * .35 + uS2.x * .08 - uS2.z * .12;
	vec3 base = hsv(hue, uS1.y, 1.);
	vec3 c = base * (diff * .9 + rim * .5) * (lift * .8 + stretch) + vec3(1.) * spec * lift * (.5 + uS2.z);
	c += hsv(hue + .5, .6, 1.) * rim * stretch * uS2.y * .6;
	c *= uS0.w * (1. + uS1.w);
	fragColor = TDOutputSwizzle(vec4(max(c, 0.), 1.));
}
