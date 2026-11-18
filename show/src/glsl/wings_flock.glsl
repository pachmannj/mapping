// KŘÍDLA — hejno: ptáci = malé tmavé tečky (tmavost mínus její rozmazaná verze → velké tmavé plochy stromů zmizí),
// k tomu stopa pohybu, která chladne: R = pták teď, G = stopa (doznívá), B = hustota hejna (rozmazaná, pro křídla).
// vstup 0 = tmavost, vstup 1 = rozmazaná tmavost, vstup 2 = předchozí stav (Feedback TOP)
uniform vec4 uF0;   // útlum stopy, citlivost na ptáky, -, -
out vec4 fragColor;
void main() {
	vec2 uv = vUV.st;
	float d = texture(sTD2DInputs[0], uv).r, b = texture(sTD2DInputs[1], uv).r;
	float bird = clamp((d - b * 1.7) * 3. * uF0.y, 0., 1.);
	bird *= smoothstep(.0, .04, uv.x) * smoothstep(1., .96, uv.x) * smoothstep(.0, .04, uv.y) * smoothstep(1., .96, uv.y);
	vec4 prev = texture(sTD2DInputs[2], uv);
	float trail = max(prev.g * clamp(uF0.x, 0., .99), bird);
	float dens = mix(prev.b, bird, .08);                  // pomalu se měnící hustota hejna
	fragColor = vec4(bird, trail, dens, 1.);
}
