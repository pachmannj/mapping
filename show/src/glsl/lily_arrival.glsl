// KVĚT — mapa času příchodu: pro každý pixel spočítá, ve které fázi rozkvětu se tam poprvé objeví květ (0 = už v pupenu, 1 = nikdy).
// Počítá se jednou po nahrání 64 fází (vstup se pak nemění, takže se znovu nevaří). Z mapy vznikají izochrony a směr růstu.
// vstup 0 = Texture 3D se všemi fázemi
out vec4 fragColor;

void main() {
	vec2 t = vUV.st;
	float dark = 0., peak = 0.;
	for (int k = 0; k < 64; k++) {
		vec3 c = texture(sTD3DInputs[0], vec3(t, (float(k) + .5) / 64.)).rgb;
		float l = dot(c, vec3(.3, .5, .2));
		dark += 1. - smoothstep(.06, .14, l);               // kolik fází je pixel ještě tmavý = kdy do něj květ dorazí
		peak = max(peak, l);
	}
	fragColor = vec4(dark / 64., peak, 0., 1.);
}
