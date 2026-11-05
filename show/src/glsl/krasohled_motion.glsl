// KRASOHLED — pohyb z kamery: rozdíl dvou snímků, zesílený a vyhlazený
// vstup 0 = aktuální snímek, vstup 1 = předchozí snímek
out vec4 fragColor;
void main() {
  vec3 a = texture(sTD2DInputs[0], vUV.st).rgb, b = texture(sTD2DInputs[1], vUV.st).rgb;
  float d = length(a - b);
  float m = smoothstep(.06, .35, d);
  fragColor = TDOutputSwizzle(vec4(vec3(m), 1.));
}
