// KŘÍDLA — z videa hejna špačků: jak moc je pixel „tmavý pták na obloze“ (0–1). Stromy jsou taky tmavé, ty se odfiltrují
// v dalším kroku podle velikosti (wings_flock.glsl). vstup 0 = video
out vec4 fragColor;
void main() {
	vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
	float lum = dot(c, vec3(.3, .59, .11));
	float d = smoothstep(.5, .22, lum);                    // obloha ~0,65, ptáci a stromy pod 0,3
	fragColor = vec4(d, d, d, 1.);
}
