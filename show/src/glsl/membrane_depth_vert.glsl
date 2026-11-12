// MEMBRÁNA — hloubkový průchod: části těla za plátnem se vykreslí jako výška (světová souřadnice z).
// Plátno leží v z = 0, kamera kouká z publika (+z); co je před plátnem (z > 0), plátno vyboulí.
out Vertex { float z; } oVert;
void main() {
	vec4 w = TDDeform(TDPos());
	gl_Position = TDWorldToProj(w);
	oVert.z = w.z;
}
