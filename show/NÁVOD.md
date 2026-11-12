# DJ SHOW – návod k obsluze

Audio-reaktivní projekce na průhledné plátno. Projekt: `DJ_Show.toe` (TouchDesigner 2025.33230+, kvůli komponentě TDMCP).

## Spuštění
1. Připoj projektor (HDMI) a zvukovku s linkou z mixu.
2. Otevři `DJ_Show.toe`. Otevře se okno **DJ SHOW – ovládání**, a pokud je připojený projektor, i výstup na něj.
3. Záložka **Audio**: `Zdroj zvuku` → *Živý vstup*, `Vstupní zařízení` → tvoje zvukovka. Zelený sloupec vpravo v měřácích = je signál.
4. Hotovo, scény se samy střídají podle hudby (`Scéna` = AUTO).

## Klávesy (v okně TouchDesigneru / ovládání)
| Klávesa | Akce |
| --- | --- |
| 1–6 | Krasohled / Vortex / Echoes / Heat / Pták / Květ |
| 0 | automatické střídání |
| B | blackout (znovu = zpět) |
| F | záblesk |
| S | stroboskop na kopák zap/vyp |
| T | testovací obrazec (mřížka → bílá → rámeček projektoru → vyp) |
| N | další demo skladba |
| O | otevřít výstup na projektor |
| Esc (v okně projektoru) | zavřít výstup |

## Mapování na místě (45 min ve tmě)
1. `T` → **rámeček projektoru**: zaostři projektor, zkontroluj, kam vůbec svítí.
2. `T` → **mřížka plátna**: barevné rohy říkají orientaci (červená = vlevo nahoře, zelená = vpravo nahoře, modrá = vlevo dole, žlutá = vpravo dole).
   - Rohy prohozené zleva doprava → `Zrcadlit vodorovně` (zadní projekce). Vzhůru nohama → `Zrcadlit svisle`.
3. Záložka **Mapping** → `Roh vlevo nahoře` … `Roh vpravo dole`: posouvej, dokud rohy mřížky nesedí na rohy plátna (0–1, 0,0 = vlevo dole).
4. `Maska vlevo/vpravo/nahoře/dole` + `Měkkost okraje`: ořízni, co by svítilo mimo plátno (oranžově vyznačené).
5. `Odříznutí černé`: zvyš, pokud je na plátně vidět šedý závoj.
6. **Uložit mapování** (uloží `mapping.json` vedle projektu; při dalším spuštění se načte samo). Pro víc míst si v `Soubor mapování` nastav třeba `mapping_lucerna.json`.

## Kontrola telefonem (iPhone jako kamera)
- iPhone u Macu se stejným Apple ID, Wi-Fi a Bluetooth zapnuté, telefon zamknutý a na šířku (Continuity Camera).
- Záložka **Camera** → `Kamera` = *Kamera zařízení … iphone*, `Kamera zapnutá`. Obraz z telefonu je v pravém horním panelu.
- **Previz**: s telefonem v publiku (nebo s fotkou místa v `Previz: fotka místa`) zapni `Previz` a rohy `Previz roh …` nastav na plátno v záběru. Uvidíš, jak bude projekce vypadat, i bez projektoru.

## Když něco nejde
| Problém | Řešení |
| --- | --- |
| „TICHO / ŽÁDNÝ SIGNÁL“ | zkontroluj kabel a zařízení v `Vstupní zařízení`; vstup se sám znovu otevírá každých 5 s |
| zvukovka není v seznamu | připoj ji a přepni `Zdroj zvuku` tam a zpět (seznam se obnoví) |
| kamera je černá | vypni a zapni `Kamera zapnutá`; první spuštění chce povolení kamery v macOS |
| výstup na špatném monitoru | `Output` → `Monitor projektoru` (0 = hlavní displej, -1 = poslední připojený) → **Otevřít výstup** |
| obraz je šedivý / „mlha“ | zvyš `Odříznutí černé`, sniž `Master jas`, vypni haze v sále |

## Scéna Pták
Racek ze stock videa vyříznutý z oblohy: na každý kopák máchne křídly (rychlost mávání podle tempa),
na silný úder se rozpadne na částice a zase složí, za ním zůstávají světelné stopy (delší při plné hudbě).
Vnitřní režisér střídá looky podle hudby (klid = spíš reál, plná hudba a dropy = abstrakce):
**Reál** (fotka), **Chronofoto** (kopie ptáka v čase jako na Mareyho fotografiích), **Slit-scan** (každá část obrazu z jiného okamžiku),
**Inkoust** (obrys se rozpíjí do kouře), **Kaleidoskop** (pták zrcadlený do symetrického tvora).
Záložka **Pták**: Look (AUTO nebo ruční volba), Abstrakce (jak často sahá po abstraktních lookách), síla máchnutí, rozpad na částice,
stopy, rychlost videa, velikost částic, jas.

## Scéna Květ
Generativní 3D květ: lístky rozmístěné zlatým úhlem (jako jiřina), průsvitné a zářící na černé.
Energie hudby květ rozvine, každý kruh lístků reaguje na své frekvenční pásmo (vnější = basy, vnitřní = výšky),
kopák pošle světelnou vlnu od středu ven, virbl květ zkroutí, hihat rozechvěje špičky.
Záložka **Květ**: počet lístků, rozkvět, velikost, prohnutí lístků, otáčení, jas.

## Pro úpravy
- Zdrojáky jsou ve `src/` (Python + GLSL), TouchDesigner je čte ze souborů a změny se projeví hned.
- `src/build.py` postaví celou show znovu (zachová nastavení i mapování): Textport (Option+T) → `exec(open(project.folder + '/src/build.py').read())`.
- `_dev/` je vývojový most pro Claude Code. Na show nevadí, ale produkci ho posílat nemusíš.
- `/project1/TDMCP` je oficiální MCP server od Derivative (jen localhost, port 13316, přístup se potvrzuje v TD). Claude Code ho v této složce zná jako `touchdesigner`.

## Licence
TouchDesigner je teď ve verzi **Non-Commercial**: výstup max. 1280 px (show renderuje 1280×720, projektor si obraz zvětší) a licence **nepovoluje komerční použití**. Na placenou akci je potřeba licence Commercial.
