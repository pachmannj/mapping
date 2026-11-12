// PTÁK — máchnutí křídly deformací obrazu: za rameny se křídla ohnou nahoru/dolů a zkrátí (natočení k divákovi).
// Střed těla a osu rozpětí spočítá sc_bird.py z masky. Pohled je zespodu, takže máchnutí = posun konců křídel kolmo na rozpětí.
// vstup 0 = vyříznutý pták (rgb, a = maska)
uniform vec4 uF0;   // střed těla x, y (0–1), osa rozpětí x, y (jednotkový vektor v prostoru obrazu s poměrem stran)
uniform vec4 uF1;   // úhel máchnutí (rad, + nahoru), vzdálenost ramene od středu, poloviční rozpětí, poměr stran
out vec4 fragColor;

void main() {
	float asp = max(uF1.w, .1);
	vec2 p = (vUV.st - uF0.xy) * vec2(asp, 1.);           // pixel vůči středu těla (izotropně)
	vec2 u = normalize(uF0.zw + vec2(1e-5, 0.)), n = vec2(-u.y, u.x);
	float x = dot(p, u), y = dot(p, n);
	float s = uF1.y, ax = abs(x);
	vec2 q = p;
	if (ax > s) {
		float t = ax - s;                                  // vzdálenost od ramene po křídle
		float ang = uF1.x;
		float fore = max(cos(ang), .35);                   // křídlo natočené k divákovi se zkrátí
		float xs = s + t / fore;                           // zpětné mapování: kam v původním obraze tenhle pixel patří
		float ys = y + t * sin(ang) * .9;                  // konec křídla se posune kolmo na rozpětí
		q = u * sign(x) * xs + n * ys;
	}
	vec2 uv = q / vec2(asp, 1.) + uF0.xy;
	vec4 c = (uv.x < 0. || uv.y < 0. || uv.x > 1. || uv.y > 1.) ? vec4(0.) : texture(sTD2DInputs[0], uv);
	fragColor = TDOutputSwizzle(c);
}
