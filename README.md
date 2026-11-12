# DJ show – audio-reaktivní projekce na průhledné plátno

Živé vizuály pro DJ set, které reagují na hudbu z mixu a promítají se na průhledné plátno (holo gauze). Běží v TouchDesigneru na MacBooku.

**Technické požadavky pro produkci** (projektor, plátno, kabely, zvuk, harmonogram): [DJ show – technické podklady pro produkci](https://claude.ai/artifact/C8WobxiSUR8veyzv2kot9a)

## Obsah

| Cesta | Co to je |
| --- | --- |
| `show/DJ_Show.toe` | show: otevřít v TouchDesigneru **2025.33230 nebo novějším** |
| `show/NÁVOD.md` | obsluha: spuštění, klávesy, mapování na místě, řešení problémů |
| `show/src/` | zdrojáky (Python + GLSL), show je čte ze souborů |
| `show/src/build.py` | postaví celou show znovu ze zdrojáků |
| `music/` | demo hudba pro test bez mixu (není v gitu) |
| `*.html`, `Krasohled.1.toe` | původní webové vizuály a první verze Krasohledu |

## Rychlý start

```bash
git clone https://github.com/pachmannj/mapping.git
```

1. Nainstaluj [TouchDesigner](https://derivative.ca/download) 2025.33230+.
2. Otevři `show/DJ_Show.toe`. Otevře se okno **DJ SHOW – ovládání**.
3. Bez zvuku z mixu: nahraj pár skladeb do `music/`, show je přehraje a vizuály na ně reagují.
4. Výstup na projektor: klávesa **O**. Mapování: klávesa **T** a záložka Mapping (viz `show/NÁVOD.md`).

## 3D modely (scéna Membrána)
- Ruka a chodidlo: [MakeHuman](https://github.com/makehumancommunity/makehuman) base mesh, CC0.
- Obličej: *Infinite, 3D Head Scan* by Lee Perry-Smith, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/), based on a work at www.triplegangers.com (soubor z repozitáře [three.js](https://github.com/mrdoob/three.js)).
- Díly v `show/assets` vyrábí `show/src/tools/make_body_parts.py` ze zdrojů v `show/assets/src`.

## Poznámky
- Výstup je 1280×720 (omezení licence Non-Commercial), projektor si obraz zvětší.
- Projekt obsahuje komponentu TDMCP (MCP server pro AI asistenty). Funguje jen na localhostu a na show nemá vliv.
