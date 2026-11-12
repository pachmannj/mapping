// MEMBRÁNA — hloubkový průchod: výška = z nejbližšího povrchu (hloubkový test nechá vyhrát to, co je nejblíž plátnu)
in Vertex { float z; } iVert;
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
void main() {
	fragColor[0] = vec4(max(iVert.z, 0.), 0., 0., 1.);
}
