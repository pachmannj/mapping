// KYTICE — převod obrazu na znaky: obraz se rozdělí na buňky (jako terminál), každá buňka dostane znak podle toho,
// kolik je v ní světla (atlas je seřazený od nejřidšího po nejhustší), a barvu květiny pod ní.
// Na beat se znaky „přeskládají“ (krátce se zamíchají), hustota mřížky se může měnit s hudbou.
// vstup 0 = vykreslená kytice, vstup 1 = atlas znaků (media/glyphs.png: 16 sloupců × 2 řádky; řádek 0 ASCII, 1 písmena)
uniform vec4 uS0;   // šířka buňky (px), styl (0 = body, 1 = ASCII, 2 = písmena), zisk jasu, kolik zůstane původních bodů
uniform vec4 uS1;   // čas, zamíchání znaků (0–1, na beat), sytost barvy, -
out vec4 fragColor;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void main() {
	vec2 res = uTDOutputInfo.res.zw;
	vec4 orig = texture(sTD2DInputs[0], vUV.st);
	if (uS0.y < .5) { fragColor = orig; return; }      // styl „body“: beze změny
	float cw = max(uS0.x, 3.), ch = cw * 1.5;           // buňka 2 : 3 jako znak písma
	vec2 px = vUV.st * res;
	vec2 cell = floor(px / vec2(cw, ch));
	vec2 lc = (px - cell * vec2(cw, ch)) / vec2(cw, ch); // místo uvnitř buňky 0–1 (y odspodu)
	// průměr a maximum světla v buňce (3 × 3 vzorky)
	vec3 sum = vec3(0.); float mx = 0.;
	for (int j = 0; j < 3; j++) for (int i = 0; i < 3; i++) {
		vec2 sp = (cell * vec2(cw, ch) + vec2(cw, ch) * (vec2(float(i), float(j)) + .5) / 3.) / res;
		vec3 c = texture(sTD2DInputs[0], sp).rgb;
		sum += c; mx = max(mx, max(c.r, max(c.g, c.b)));
	}
	vec3 avg = sum / 9.;
	float lum = clamp(((max(avg.r, max(avg.g, avg.b)) * .6 + mx * .4) * uS0.z - .035) / .965, 0., 1.);   // slabý opar → prázdná buňka
	// znak podle jasu; na beat se část buněk zamíchá (náhodný znak podobné hustoty, mění se ~12× za s)
	float g = floor(pow(lum, .75) * 15.99);
	float sh = hash(cell + floor(uS1.x * 12.));
	if (sh < uS1.y && lum > .04) g = clamp(g + floor((hash(cell * 1.7 + floor(uS1.x * 12.)) - .5) * 8.), 1., 15.);
	float row = uS0.y > 1.5 ? 1. : 0.;
	vec2 auv = vec2((g + lc.x) / 16., 1. - (row + 1. - lc.y) / 2.);
	float a = texture(sTD2DInputs[1], auv).r;
	// barva: odstín květiny v buňce, jas daný tvarem znaku
	vec3 hueCol = avg / max(max(avg.r, max(avg.g, avg.b)), 1e-4);
	hueCol = mix(vec3(dot(hueCol, vec3(.33))), hueCol, uS1.z);
	vec3 col = hueCol * a * (.35 + lum * 1.4);
	fragColor = TDOutputSwizzle(vec4(col + orig.rgb * uS0.w, 1.));
}
