// KRASOHLED — pixel shader
in Vertex { vec3 c; float a; } iVert;
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
void main() {
  if (iVert.a < .01) discard;
  fragColor[0] = TDOutputSwizzle(vec4(iVert.c * iVert.a, 1.));
}
