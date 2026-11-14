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
| 1–7 | Krasohled / Vortex / Echoes / Heat / Pták / Květ / Kytice |
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

## Spotify (nebo jakýkoli zvuk z Macu)
Spotify zvuk nikomu jinému nepustí ven přímo, takže se zachytává to, co Mac hraje, přes virtuální kabel **BlackHole** (zdarma).
1. Nainstaluj ho (jednou, zeptá se na heslo k Macu): v Terminálu `brew install blackhole-2ch`, pak Mac restartuj.
2. Otevři **Nastavení Audio MIDI** → vlevo dole **+** → **Vytvořit zařízení s více výstupy** → zaškrtni **BlackHole 2ch**
   a svoje reproduktory / sluchátka (u reproduktorů zapni *Opravu posunu*).
3. V liště nahoře (ikona zvuku) vyber jako výstup to nové **Zařízení s více výstupy** — Spotify pak hraje do reproduktorů i do TD.
4. V TD záložka **Audio** → `Zdroj zvuku` → **Zvuk z Macu (Spotify přes BlackHole)**. Zařízení BlackHole se vybere samo.
Bez instalace jde nouzově `Živý vstup` + mikrofon MacBooku (zachytí reproduktory, ale reaguje hůř).

## 3D okno (Pták a Květ)
Anamorfní iluze jako na billboardech v New Yorku: obraz na zdi je přesně ta perspektiva, kterou by divák viděl skrz skutečný
výklenek ve zdi. Objekt v něm má stín na podlaze a stěnách, odlesk na podlaze a svítí na stěny; když vyleze před zeď,
přeroste svítící rám otvoru a osvítí zeď kolem. Iluze je nejsilnější z místa, kde stojí publikum — nastav v záložce **3D okno**
`Výška očí diváka` (0 = oči ve výšce středu obrazu, záporné = níž) a `Vzdálenost diváka` (v násobcích výšky obrazu na zdi).
Dále hloubka a velikost výklenku, jak moc objekt vylézá, svítící hrany, mřížka, stín, odlesk a světlo objektu na zeď.
Výklenek (krychle s mřížkou) je ve výchozím stavu vypnutý: objekt pak visí před zdí, zeď za ním je jemně osvětlená a nese jeho stín,
který se s hloubkou vzdaluje a měkne. Zapíná se přepínačem `Výklenek`.
Žádný automatický režisér — scény vypadají pořád stejně a reagují jen na hudbu.

## Scéna Pták
Racek ze stock videa vyříznutý z oblohy krouží ve 3D okně a s energií hudby z něj vylétá před zeď.
Styl ze čtyř vrstev: šedé tělo s bílým obrysem, tyrkysové světelné stopy za pohybem, červeno-oranžový barevný lem a rastr z teček.
Kopák = máchnutí křídly, záblesk obrysu a postrčení z okna; virbl a hi-haty = rastr z teček a lem.
Výsledek se převádí **na znaky jako Kytice a Květ** (styl a velikost znaků podle hlasitosti ze záložky Kytice; ve stylu Body je pták jako dřív).
Záložka **Pták**: síla máchnutí, světelné stopy, barevný lem, rastr z teček, rychlost videa, velikost ptáka, jas.

## Scéna Květ
Velká **lilie** ze svítících bodů (a za ní šest menších lilií ve stejném úhlu, rozmazané do hloubky; na každou dobu se rozsvítí jedna z nich, střídavě vlevo a vpravo, jako světla na DJ decku) ve stylu Kytice (znaky / písmena / body, barvy podle hudby; posuvníky v záložce Kytice
platí i tady), ale **plave plynule jako Vortex**: měkké mávnutí na rány, znaky dýchají bez cukání a nemíchají se.
- **Dlouhý tón / zpěv**: dokud tón drží (hlasité stálé středy, které vyčnívají nad průměr písničky), lilie se nafukuje, rozevírá
  a kolem ní houstne svítící atmosféra; čím déle tón trvá, tím víc (plno za ~3 s). Když tón skončí, pomalu se stáhne.
- **Náklon v rytmu**: celá rostlina se kolébá od paty stonku jako ve větru (po taktech, silněji s výrazným rytmem).
- **Rozjezd písničky**: lilie se začne točit rychleji a zvětší se.
- Kamera zůstává zepředu a jen se mírně kolébá.
Záložka **Květ**: nafouknutí dlouhým tónem, náklon v rytmu, otáčení květu (a rychlost přepínání druhů — jen když se v
`src/sc_flower.py` do ORDER přidají další druhy).

## Scéna Kytice
**Plave jako Vortex (stejně jako Květ):** měkká dlouhá mávnutí na rány, znaky se nemíchají, kamera se na doby necuká.
Dlouhý tón / zpěv kytici rozvine, mírně nafoukne a zhustí kolem ní atmosféru (pak se stáhne); celá kytice se kolébá v rytmu
od paty jako ve větru; když se písnička rozjede, pomalu se otáčí rychleji a o kus zvětší.
Posuvníky v záložce Kytice: Nafouknutí dlouhým tónem, Náklon v rytmu, Otáčení kytice.

Kytice se zobrazuje **ve znacích**: obraz se rozdělí na buňky jako terminál a každá buňka dostane znak podle toho, kolik je v ní
světla, v barvě květiny pod ní. Styly: **ASCII znaky**, **Písmena**, nebo původní **Body** (záložka Kytice → Styl, Velikost znaku).
Velikost znaků se řídí **jen hlasitostí**: čím hlasitější zvuk, tím větší znaky (okamžitě, bez zpoždění; posuvník Velikost znaků podle hlasitosti). Na dobu se část znaků krátce zamíchá. Kamera **létá okolo kytice** rychlostí podle tempa (1 oběh za 16 taktů, při rozjezdu a dropu rychleji),
výška se vlní po 2 taktech a na každou dobu se nadechne dopředu. Atlas znaků (`media/glyphs.png`) vyrábí `tools/make_glyphs.py`.

Kytice z 327 tisíc svítících bodů: pět růžových lilií, tři chryzantémy, dvě pivoňky, stonky, listy a pyl ve vzduchu.
Květiny jsou procedurální, takže opravdu rozkvétají. Kamera se pomalu kývá před kyticí s malou hloubkou ostrosti:
co je mimo ostrost, rozpije se do měkkých světelných skvrn.
Pohyb je organický a plynulý jako u Vortexu: vítr kývá květy na stoncích (stonky jsou dole ukotvené a ohýbají se),
po lístcích běží vlny a mlha proudí polem. Hudba mění rychlost a sílu tohoto proudění, nic neskáče.
**Rytmus:** kytice „hraje“ písničku. Rytmické hodiny se chytí tempa (BPM z kopáků) a na každý kopák se jemně doladí.
Lilie se rozevřou a rozzáří na 1. a 3. dobu (vlna přeběhne přes lilie jednu po druhé), chryzantémy na 2. a 4. (virbl),
pivoňky na osminy (hi-haty); s každým úderem proběhne lístky vlna od středu ke špičkám, kytice se kolébá v taktu
a kamera se na dobu nadechne. Když kopák zmizí (break), pulz během pár sekund vyprchá a kytice jen pluje, s návratem beatu naskočí.
**Každá květina poslouchá jiné frekvenční pásmo** (od basů po výšky): podle změn ve svém pásmu se rozvíjí, vlní a září.
Kopák pošle měkkou vlnu po lístcích a lilie se rozzáří, virbl občas přeostří kameru na jinou květinu (nejvýš jednou za 4 s),
hutnost a výšky rozpouštějí části květů do mlhy.
Růžové lilie mění barvy podle hudby (korálová ↔ růžová ↔ fialová, každá lilie podle svého pásma jinak).
Když se písnička rozjede, kytice se postupně víc rozpohybuje, rozvine a rozzáří; na dropu přijde vlna, která všechno
rozvlní, rozbarví a rozpustí do mlhy a pomalu dozní.
Záložka **Kytice**: citlivost rozkvětu, rozpad do mlhy, vlna kopáku, hloubka ostrosti, pohyb kamery, velikost bodů, jas, sytost barev, měnění barev lilií.

## Pro úpravy
- Zdrojáky jsou ve `src/` (Python + GLSL), TouchDesigner je čte ze souborů a změny se projeví hned.
- `src/build.py` postaví celou show znovu (zachová nastavení i mapování): Textport (Option+T) → `exec(open(project.folder + '/src/build.py').read())`.
- `_dev/` je vývojový most pro Claude Code. Na show nevadí, ale produkci ho posílat nemusíš.
- `/project1/TDMCP` je oficiální MCP server od Derivative (jen localhost, port 13316, přístup se potvrzuje v TD). Claude Code ho v této složce zná jako `touchdesigner`.

## Licence
TouchDesigner je teď ve verzi **Non-Commercial**: výstup max. 1280 px (show renderuje 1280×720, projektor si obraz zvětší) a licence **nepovoluje komerční použití**. Na placenou akci je potřeba licence Commercial.
