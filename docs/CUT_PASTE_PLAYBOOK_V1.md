# Ausmalwiese Cut & Paste — vienotais darba standarts v1

**Status (2026-10-17): SOURCE/DOCS ONLY — jaunais sikspārņa kandidāts nav publicēts.** Šis ir ilgtermiņa *authoring + QA playbook* visiem sezonu tēliem, nevis pierādījums, ka rīks autonomi izpilda katru soli. Šīs lapas autorēšana/merge nekad nepiešķir `PUBLISH`, Drive, RPi5/LIVE, DNS/Cloudflare, permissions vai secrets tiesības.

**Publikācijas gate:** globāls Cut & Paste `PUBLISH` HOLD vairs nav spēkā. Katrai precīzajai divu lapu versijai joprojām vajag obligāto art/geometry/print/physical QA, īpašnieka apstiprinājumu un pēc tam svaigu `PUBLISH` komandu, kas autorizē tikai šo exact version. Vecs QA, iepriekšējs `PUBLISH`, GitHub merge vai HTTP pieejamība nav publikācijas atļauja citai versijai.

## 1. Komandas un nepārprotamas robežas

| Komanda | Darbība | Ko tā nedod |
| --- | --- | --- |
| `CUT <subject>` | Īsā komanda **vienam** divu lapu Cut & Paste melnrakstam; ekvivalenta `MAKE Cut & Paste <subject>` | Nav izvietošanas, merge vai publikācijas |
| `MAKE Cut & Paste <subject>` | ImageGen izveido sākotnējo tēla konceptu; pēc īpašnieka SVG handoff abas A4 lapas veido tikai no šiem vektoriem | Nav garantēta fiziska izgriežamība |
| `EDIT <exact instruction>` | Maina tikai nosauktās detaļas *vienā kanoniskajā avotā* un pēc tam atjauno visus atvasinātos attēlus | Vecie validācijas rezultāti kļūst nederīgi |
| `REMAKE` | Veido jaunu kompozīciju, nevis slepeni aizvieto apstiprinātas detaļas | Nav iepriekšējā varianta apstiprinājuma |
| `VALIDATE-PRINT` | Tikai precīzā gala A4 PNG tehniskā pārbaude | Nav ģeometriskas salikšanas vai fiziska testa PASS |
| `PUBLISH` | Atsevišķa, svaiga, īpašnieka precīza publikācijas atļauja **tikai exact final divu lapu versijai pēc obligātā QA un īpašnieka apstiprinājuma** | Nav LIVE deploy, overwrite vai rollback atļaujas |

Parastais `MAKE <subject>` joprojām veido **vienu** krāsojamo lapu. `CUT` nav komanda ģenerēt vairākus tēlus vienā reizē, atvērt individuālu GitHub issue katram tēlam vai automātiski publicēt.

Piemēri: `CUT Fledermaus`, `CUT Halloween Kürbis`, `CUT Weihnachten Schneemann`. Vispirms pabeidz un apstiprini vienu tēlu, tikai pēc tam sāc nākamo. Iekšējā saruna — latviski, gala lietotāja nosaukumi un norādes — vāciski.

### Pašreizējais vienkāršotais SVG handoff

1. ChatGPT ar ImageGen izveido tikai sākotnējo krāsaino tēla konceptu.
2. Īpašnieks ārēji vektorizē attēlu un atsūta SVG failu(-us).
3. Pēc SVG handoff **ImageGen šai versijai vairs netiek lietots**. Formas, krāsas un proporcijas netiek pārzīmētas; A4 sagatavošana ir deterministiska vektoru izvietošana.
4. **1. lapa:** tikai pamatķermenis. **2. lapa:** tikai griežamās detaļas. Uz 1. lapas nav saliktā tēla paraugbildes.
5. Griešanas kontūras drīkst pievienot/normalizēt no SVG ārējā silueta. Izvietojumam vispirms lieto translāciju; ja salikuma fit to prasa, vienu uniform scale piemēro visam tēlam konsekventi.
6. Diagnostikas salikumu drīkst veidot QA vajadzībām, bet tas nav drukājamās lapas saturs.


## 2. Mākslinieciskais kvalitātes standarts

Mērķauditorija: **Familien, Kitas und Vorschulen in Deutschland**, bērni 3–6 gadi. Galvenajam tēlam jābūt bērniem pievilcīgam, skaidri atpazīstamam un oriģinālam; biezas tumšas kontūras, lielas formas, noapaļotas savienojumu vietas, konsekventas krāsas uz balta fona. **Neveidot primitīvus ovālu/trijstūru/taisnstūru salikumus**, kuros detaļas izskatās kā mehāniski bloki, nevis vienots tēls. Lai ornaments vai detaļa ir dekoratīva tikai tad, ja tā reāli parādās gatavajā tēlā.

Parasti **bez cepurēm, lieka fona un aksesuāriem**, ja tie nav tieši prasīti. Izvēlies tikai konkrētajam tēlam atbilstošās atdalāmās detaļas: ausis, spārnus, ķepas/rokas/kājas, acis, degunu/knābi, muti u.c. **Neuzspiest** visas šīs detaļas katram tēlam. Mazās uzacis, zobi, skropstas u.c. kā individuāli izgriezumi ir bērnam potenciāli sarežģīti — vajadzīga īpaša cilvēka griešanas pārbaude; ja tā nav izmantojama, pārveido izstrādājumu **kanoniskajā avotā**.

Vizuālā pieņemšana ir cilvēka solis. CI PASS pierāda tikai testētos invariantu gadījumus, nevis skaistu ilustrāciju. Gaidošs atsevišķs art-review PR (vēsturiski #239) nav jāuzskata par merged vai pieņemtu, kamēr tas nav aktuāli pārbaudīts.

## 3. Viens kanoniskais tēls: neatkarīgas kopijas ir AIZLIEGTAS

**Source of truth pēc handoff:** īpašnieka atsūtītais vektorizētais SVG fails vai SVG failu pāris. ImageGen ir tikai pirms-vektorizācijas mākslas koncepts; pēc SVG saņemšanas pieņemtajai versijai ImageGen vairs netiek lietots. No SVG drīkst atvasināt versētu salikuma manifestu/enkurus QA vajadzībām; skat. [assembly v1](CUT_PASTE_ASSEMBLY_V1.md) un `metadata/cut-paste-character-v1.schema.json`. Katram elementam vienreiz piešķir:
- stabilu unikālu `part_id` un lomu `base` / `cutout`;
- precīzu ārējo kontūru, iekšējo zīmējumu, krāsu, mērogu milimetros un orientāciju;
- salikšanas koordinātas, rotāciju, simetrijas pusi un slāņu secību;
- priekšpusē pieejamu līmēšanas mērķi, kontakta laukumu un darbību secību.

No **tā paša SVG avota** atvasini **(a)** lielo rumpi uz 1. lapas un **(b)** izgriežamos elementus uz 2. lapas. Uz 1. lapas **nav** mazā gatavā tēla parauga. Atsevišķu diagnostikas salikuma attēlu (*assembly proof*) drīkst ģenerēt tikai QA vajadzībām; tas nav drukājamās lapas saturs. Nedrīkst salikt 1. lapu no vecā PDF un 2. lapu no jauna PDF, ja salikuma versijas/hashi atšķiras, pat ja abas lapas atsevišķi ir skaistas un A4 PASS.

Katru anatomijas elementu izvēlies **vienreiz**: ja ausis/spārni/ķepas/acis ir `cutout`, tie **nedrīkst** būt jau uzzīmēti uz lielās pamatnes. Vienai detaļai ir tieši viena lietošanas vieta; bez dublikātiem vai neizmantotām detaļām. Slāņu secība un līmēšana tikai pieejamā priekšpusē; bērnam nav jācenšas iebāzt detaļu aiz gatava, neatdalāma objekta. Spārni sikspārnim jāpievieno **rumpja/vēdera sānos**, nevis sejas vai galvas vidū.

**Svarīgs izņēmums pie iepriekš esošu PNG glābšanas:** precīza izgriešana/izvietošana ar programmatūru ir pieļaujama kā pagaidu mākslas restaurācija, nevis pilnvērtīgs kanoniskā SVG pierādījums. Jāreģistrē katras daļas avots, faktiskais izmēra koeficients, jaunās līmēšanas vietas, un jāiegūst jauns kopējā salikuma un fiziskais apstiprinājums. Ja avota un parauga sakritību nav iespējams pierādīt, STOP, nevis atzīmēt `assembly PASS`.

## 3A. OBLIGĀTS ASSEMBLED_FIT vārts PIRMS divu A4 lapu veidošanas

**Kļūdas pierādījums (2026-10-17):** divos pēc kārtas ģenerētos Halloween ķirbja ar sikspārņa spārniem uzmetumos lielais ķirbis aizņēma gandrīz visu lietojamo A4 platumu, un paredzētie spārni pie tā sāniem ievērojami palielinātu saliktā tēla platumu. Abi ir **`ASSEMBLED_FIT=FAIL` vizuāli konstatēta riska dēļ**, nevis pēc izmērītiem milimetriem. Neizdomā izmērus. Divu skaistu attēlu ģenerēšana vai divu A4 PNG tehniska derīguma pārbaude nav pierādījums, ka bērna salīmētā figūra ietilpst uz papīra.

**Obligātā secība (bez apstiprināšanas no ImageGen attēla vien):**

1. Vispirms ar ImageGen izveido vienu oriģinālu gatavā tēla māksliniecisko koncepciju. Īpašnieks to vektorizē ārēji un atsūta SVG failu(-us). **No šī brīža ImageGen šai versijai vairs netiek izmantots.** No atsūtītā SVG nosaki katras fiziskās detaļas unikālo ID, ārējo siluetu, kopīgo mērogu, rotāciju un paredzēto priekšpuses līmēšanas vietu. Plakans ImageGen attēls bez SVG ģeometrijas ir tikai `ART_CONCEPT_ONLY`, nevis gatavs CUT.
2. **PIRMS** abu A4 lapu finalizācijas matemātiski atvasini visu pamatnes un salikto detaļu siluetu union/bounding box 100% fiziskajā mērogā, ņemot vērā ārējo mākslas kontūru, abu spārnu galus, ausis, ragi/cepure/kāts, asti, līmēšanas pārlaidumus un pilno slāņu secību. Reģistrē `assembled_bbox_mm=[left,top,right,bottom]`, `assembled_width_mm=right-left`, `assembled_height_mm=bottom-top`. QA diagnostikas attēla izmēri neattiecas uz šo fiziskā salikuma testu.
3. Novieto pilno salikumu **tās pašas 1. lapas lielā rumpja fiziskajās koordinātās**, kur bērns salīmēs detaļas. Atkārto precīzo `js/print.js` `fitA4InkBounds` lapas transformāciju (ieskaitot XY translāciju). Gala salikuma ārējai robežai jāiekļaujas **`x=17..193 mm`, `y=17..256 mm`**, tātad `assembled_width_mm <= 176 mm` un `assembled_height_mm <= 239 mm`, ņemot vērā 1–2 px rezerves noapaļošanai. **Nedrīkst** paļauties uz pārlūka/drukas dialoga `Fit to page` samazināšanu; abu A4 lapu normālais print `scale=1.0`.
4. Tikai `ASSEMBLED_FIT=PASS` ar izmērītiem mm un vienas SVG ģeometrijas pierādījumu atļauj atvasināt **1. lapas pamatni bez saliktā parauga** un **2. lapas griežamās detaļas**. Pēc tam joprojām atsevišķi pārbaudi abu lapu A4/PNG kvalitāti, 4 mm šķēru atstarpes, priekšpuses līmēšanas enkurus, nebrendētu oriģinālu un `js/print.js` drukas zonu.
5. Ja saliktais tēls ar spārniem iziet ārā, trūkst ģeometrijas vai nav precīzas izvietošanas pārbaudes: `ASSEMBLED_FIT=FAIL` vai `ASSEMBLED_FIT=UNVERIFIED` un **STOP pirms divu A4 CUT gala lapu apstiprināšanas**. Atgriezies pie atsūtītā SVG avota, saskaņoti maini kopīgo mērogu/enkurus, nepazaudē bērnam lietojamas griežamās zonas, atvasini abas lapas no jauna un atkārto visus testus. Aizliegts pēc SVG handoff labot fit ar jaunu ImageGen zīmējumu vai atsevišķi samazināt tikai vienu spārnu/lapu.

**Statusi un godīgs pierādījums:** `ART_CONCEPT_ONLY`, `ASSEMBLED_FIT=UNVERIFIED`, `ASSEMBLED_FIT=FAIL` vai `ASSEMBLED_FIT=PASS`, kur `PASS` vienmēr ietver full-size robežas mm, tā paša avota detaļu identitāti un izmantoto print placement. Attēla modelis **nedrīkst apgalvot** ģeometrijas PASS, ja faktiskais izmēru aprēķins nav veikts. Šis source-only noteikums vēl **neievieš jaunu automātisku checker**. A4 PASS neaizstāj fizisko 100% izgriešanu/salīmēšanu, vizuālo apstiprinājumu vai svaigu exact-version `PUBLISH` gate.

## 4. Lapu līgums un precīzi drukas aprēķini

1. **`01 Körper/Grundform`:** tikai liels rumpis/pamatne no atsūtītā SVG; **bez mazā saliktā parauga** un bez citiem dekoratīviem elementiem.
2. **`02 Ausschneideteile`:** visas un tikai detaļas, kuru vajag salikumam; katra tieši vienreiz; atsevišķa, slēgta, uz ārpusi nobīdīta **pārtraukta griešanas kontūra**. Nekad nepārtrauktā mākslas kontūra nav jāaizvieto ar pārtrauktu. Bērna šķērēm atstāj vismaz QA noteiktos **4 mm starp griešanas līniju stroke envelopes**, nevis tikai starp krāsainajiem objektiem.

Portrait A4: **210×297 mm = 2480×3508 RGB PNG**, aptuveni **300 DPI**. Precīzi balta `#FFFFFF` 15 mm josla (rastera pārbaudē 177 px). Taču `js/print.js` reālais **no-downscale visible ink** laukums ir stingrāks: `x=17..193 mm` un `y=17..256 mm`. Tātad platums **176 mm**, augstums **239 mm**, zem zīmējuma rezervēti **41 mm** (vietnes footer, atstarpe, apakšējā mala), papildus **2 mm** kontūru rezerve. Drukājamās redzamās tintes robežai jāpaliek vismaz ap **17 mm** no augšas/sāniem ar 1–2 px rezervi; 15 mm baltā josla viena pati nav pietiekama `scale=1.0` pierādījumam.

Pie rastra A4 efektīvā koordinātu pārrēķina (ievērojot attiecīgā eksporta izmēru):
- `x_mm = x_px × 210 / 2480`; `y_mm = y_px × 297 / 3508`;
- piemēram, augšējā drošā robeža ap **201 px**, apakšējā ap **3023 px** (pārbaudot *inclusive* pēdējo pikseli), bet lieto faktisko baitu rastra `visibleInkBounds` rezultātu, nevis noapaļojumu kā apliecinājumu;
- `inkWidth = (right-left+1) × 210/2480`, `inkHeight = (bottom-top+1) × 297/3508`;
- `scale = min(1, 176/inkWidth, 239/inkHeight)`. Vajadzīgs **scale = 1.0**, bez pārslēgšanās uz mazāku.

**Izkārtojuma algoritms:** nosaki rumpja un 2. lapas detaļu *redzamās tintes* bounding box no atsūtītajiem SVG. Saglabā SVG formas, krāsas un proporcijas; vispirms lieto translāciju. Ja pilns saliktais tēls neietilpst atļautajā fiziskajā zonā, drīkst lietot tikai vienu **kopīgu uniform scale** visam tēlam (pamatnei un visām atdalāmajām detaļām), tad pārrēķina enkurus un **ģenerē abas lapas no jauna**. Nekad nesamazini tikai vienu rastra lapu vai vienu detaļu neatkarīgi.

**Uzmanību:** vietnes `fitA4InkBounds` vēl arī **centrē kopējo redzamās tintes laukumu** pēc aprēķinātā `scale`. Tādēļ tikai PNG koordinātas vien nevar apliecināt precīzo **fiziskās** izdrukas redzamās tintes novietojumu. Pārbaudi pēc pilnās `js/print.js` transformācijas un vajadzības gadījumā faktiski izdrukā!

## 5. Griešanas un izmēru labošanas noteikumi

- Katra cut līnija ir atvasināta no precīza vektora ārējā silueta (derīgs, slēgts, bez self-intersection) ar ārēju offset; SVG `stroke-dasharray` kontrolē tikai svītrojumu. Skat. [QA v1](CUT_PASTE_QA_V1.md).
- Pirms samazināšanas **izmēri ar lineālu** reālā 100% A4 testā: cik mm spārna gals pārsniedz vēlamo pozīciju, pilnās samontētās figūras platums, acu/mutes/smagāko detaļu salīdzinājums pret rumpi. Telefona fotogrāfija ar perspektīvu dod tikai *aptuvenu* proporciju norādi, neprecīzu fizisku mm mērījumu; pēc tās nevar deklarēt garantētu salīmēšanu.
- Ja nepieciešama mēroga korekcija, dokumentē pirms/pēc mm un koeficientu, piemēro vienu saskaņotu mērogu visai aktivitātei, pārskati līmēšanas enkurus un visu figūras gala bbox, tad izvada abas lapas atkārtoti.
- Pēc SVG handoff nevienu lapu nelabo ar atsevišķu AI/rastera pārzīmēšanu. Izmaiņas veic SVG-derived izvietojumā vai vienotajā mērogā un pēc tam abas A4 lapas atvasina no jauna.
- Ja pēc handoff jāpievieno vai jānoņem detaļa, maina pašu SVG avotu un pēc tam atjauno atbilstošo base/cutout izvadi. Tikai skaists rastra ielāps nav ģeometriskas saderības pierādījums.
- Nākamais labojums atceļ **visus** vecos QA/print/owner apstiprinājumus attiecīgajam izvades pārim; apstiprini precīzu jaunu versiju ar SHAs.

## 6. Izvade, footer un provizoriska druka

Mākslas ģenerācijas melnraksti, kad attiecas parastais `MAKE`, saglabā projekta 1024×1536 vai 1536×1024 prasības; **galīgo A4 milimetru izvietojumu dod deterministisks SVG → PNG exporters**, nevis ImageGen minējums.

Eksportē **divus atsevišķus, bez logotipa, QR un footer**, pilnas kvalitātes PNG. Rīki: `tools/coloring-pages-cut-paste`, `tools/cut_paste_geometry.py`, Inkscape CLI, `tools/coloring-pages-print-master`, QA testi. Exports no viena SVG/JSON izveido arī atsevišķu assembly proof. `VALIDATE-PRINT` pārbauda izmēru, RGB, DPI, baltās malas, SHA/bytes, bet **nepierāda** detaļu saderību vai mākslas kvalitāti.

**Ausmalwiese logo, footer un QR pievieno vietnes `print.html` / `js/print.js`**, nevis divreiz iededzina oriģinālajā A4. Testa PDF ar vietnes stilam līdzīgu footer drīkst izveidot **tikai kā atsevišķu testa artefaktu**; tas nav publication-source PNG. Iespēju robežās pārbaudi ar **īsto** vietnes drukas priekšskatījumu, tostarp QR maršrutu un print background izvēli.

Fiziskai griešanas pārbaudei: A4 portrait, **Actual size / 100%**, nevis `Fit to page`. PDF skatītāja/printera non-printable area dažos aparātos var izraisīt apgriešanu, tādēļ reālajā testā pārbaudi izmērītu mērogu un malas, nevis paļaujies tikai uz UI režīma etiķeti.

## 7. Sikspārņa pilota vēsture: ko izdarījām un kāpēc vajag stingrus vārtus

Šis ir **sarunas darba kopsavilkums**, nevis apstiprināts production attēla avots:
1. **Pirmie rudimentārie prototipi (sikspārnis/ķirbis):** blokaini tēli, neatbilstošs stils, neatbilstošas detaļas un paraugs. Secinājums — skaists, vienots tēls **pirms** sadalīšanas un art-review pirms A4 izvades.
2. **Vienas lapas komponējumi un Figma V3:** izdevās vizuāli simpātiskāki tēli, bet dažādās lapās zīmētās vai manuāli pārvietotās detaļas varēja nesakrist. Secinājums — viena kanoniskā SVG/JSON ģeometrija, nevis trīs neatkarīgi attēli.
3. **Divu A4 lapu iterācijas:** rumpim jābūt pēc iespējas zemāk, mazajam paraugam pie 17 mm augšējā redzamās tintes limita; pilnam tēlam spārni **pie rumpja**, nevis galvas. Footer aizņem apakšējo rezervi, un oriģināls to nedrīkst saturēt.
4. **Fizisks izmēģinājums no lietotāja foto:** reāli tika izgrieztas/pielīmētas detaļas; spārni izstiepās tuvu/ārpus A4 sāniem, acis/degunu/muti vēlējās mazākus, uzacu trūka. Foto pierāda **izmēģinājumu un novērotās problēmas**, nevis pēdējā varianta PASS.
5. **Rastra labojums:** mēģināts samazināt spārnus par **11%**, acis, degunu un muti par **10%**; ausis, ķepas un rumpis netika samazināti. Pieprasītas divas uzacis. Šie skaitļi ir **veiktā rediģēšanas mēģinājuma parametri**, nevis pierādīts gatava salikuma izmērs.
6. **Nepareiza PDF kombinācija:** 1. lapa tika paņemta no vecā, apstiprinātā PDF, 2. no labotā PDF. Abas bija korekti A4 un footer bija vietā, bet mazais vecā parauga detaļu izmērs **neatbilda** jaunajiem cutout. Tas ir **assembly FAIL**, kaut PDF lapu tehniskā vienādība bija PASS.
7. **Pēdējā testa kandidāta korekcija (2026-10-17):** oriģinālais rumpis paturēts, pirmās lapas mazais paraugs aizvietots ar labotā varianta paraugu, otra lapa atstāta identiska labotā avota lapai. Tā ir **raster-only** kompozīcija: nav nostiprinātas vienas SVG part tree ID/anchor pārbaudes, nav fiziski no jauna salīmēta un nav īpašnieka pierādīta pilnīga salikšanas pieņemšana. **Neatzīmēt `PUBLISH READY`.**

Vēsturiskās lokālās sesijas testa versijas **identifikācijai, nevis GitHub bināra uzglabāšanai**:
- 1. lapa `01-siksparnis-rumpis-paraugs-A4.png`: SHA-256 `d79b4a8bb4fae0284d1d777ef7b5238ed7708ef7b2747e3a2c7ad6c1f35837be`; 1 127 519 bytes.
- 2. lapa `02-siksparnis-izgriezamas-detalas-A4.png`: SHA-256 `f2e19fbb836accd108ef8ec1b49c33049a3baa0acbac2355eef8f6d282fcd240`; 1 506 080 bytes.
- Izmērītā aptuvenā tintes robeža: 1. lapai `x=53.35..156.40, y=17.10..255.94 mm`, 2. lapai `x=28.79..180.87, y=21.34..254.75 mm`. **Tikai raster ink/safe-zone novērojums; ne pilna salikuma telpiskā pārbaude.** Session-local `/mnt/data/...` ceļš nav ilgtspējīgs repozitorija vai LIVE avots; faili jānodrošina atkārtoti, ja tos vairs nevar verificēt.
- Abu A4 failu `2480×3508` RGB/~300 DPI un baltās malas tika tehniski pārbaudītas; tas neaizstāj kanoniskā `VALIDATE-PRINT` atkārtotu palaišanu uz nākamās precīzās versijas.

## 8. QA / statusu vārdnīca

Katrai precīzajai versijai glabā pārskatu ar:
- `SOURCE` — kanoniskās SVG/JSON shēmas hash, detālām/ID, assemble anchors, izgriezumu skaitu.
- `ART_REVIEW` — `PENDING|PASS|FAIL` + īpašnieka vērtējums; figurālās kvalitātes pārbaude.
- `GEOMETRY_QA` — `PENDING|PASS|FAIL`; 1:1 part ID/izmēri, līmēšanas laukumi, pretējās puses, full-body extent, no overlap, kontūras un 4 mm scissor separation.
- `PRINT_QA` — `PENDING|PASS|FAIL`; A4, RGB, ~300 DPI, 15 mm exact-white, x/y 17..193/17..256 mm, site-render scale=1, footer/QR nav oriģinālajā PNG.
- `PHYSICAL_QA` — `PENDING|PASS|FAIL`; īsts 100% A4 izdrukāts, izgriezts, salīmēts (sikspārnis un cits tēls pirms foundation #221 slēgšanas), foto/izmēri, atbilstība paredzētajam salikumam.
- `OWNER_APPROVAL` — `PENDING|PASS|FAIL`; precīzajai divu lapu SHA identitātei, nevis abstraktai idejai.
- `PUBLISH` — `NOT_REQUESTED|STOP|PASS`. `PASS` ir iespējams tikai pēc svaigas exact-version īpašnieka `PUBLISH` komandas un visu obligāto QA gate izpildes.

**STOP noteikumi:** jebkurš `FAIL`, nezināms SHA, neatbilstošs paraugs, nesamontējamas detaļas, pārāk mazi fragmenti, kļūdaina print zone vai derīga `file_uri/source_file_ref` neesība aptur virzīšanu. Nemaini attēlus pēc apstiprinājuma bez pilnas pārvalidēšanas.

## 9. Atkārtojamais process sezonām

`#218` ir kopīgais plāns, `#219` kanoniskā shēma, `#220` exporters, `#221` QA/human gates, `#222` Halloween un `#223` Weihnachten sezonas saraksti. **Nav atsevišķa GitHub issue katram tēlam**, ja vien neparādās atsevišķa programmatūras kļūda.

Vienam tēlam: **ideja → mākslas master + detaļu inventārs → art review → kanoniska salikšana/anchor → abpusējs A4 exports + assembly proof → automātiskie geometry/print testi → 100% fiziska izgriešana/salīmēšana → exact-SHA owner review → atsevišķa svaiga PUBLISH komanda**. Tikai pēc PASS un atsevišķas exact-version atļaujas pārej pie publicēšanas; pēc tam nākamais sezonas tēls. Krāsainie Cut & Paste materiāli ir apzināti krāsaini, nevis parastās vienkrāsainās krāsojamās lapas.

Kad īpašnieks vēlāk vēlas publicēt: svaigi pārbaudi `coloring-pages/main`, `RPi5_main/main`, **instalētā** operatora un importer attēla atbilstību, LIVE katalogu/ID, precīzās galīgās *bez-footer* PNG, kanonisko A4 prepare+validate un v2 2 lapu manifestu. Pirms **jebkura** Drive mutation jau jābūt visām stabilajām upload atsaucēm; abas PNG augšupielādē manifestam **pirms**, manifests **pēdējais**. Trūkumi ⇒ STOP, pēc pirmās mutācijas nekāda retry/rollback/cleanup/surface switching.

## 10. Publiski tehniskie avoti (dizaina skaidrojumiem, ne LIVE statusam)

- MDN: [CSS `@page`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page), [Paged media](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Paged_media) un [Printing](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing).
- MDN: [SVG `stroke-dasharray`](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/stroke-dasharray) un [`stroke-linejoin`](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/stroke-linejoin).
- Inkscape: [CLI SVG → PNG export](https://wiki.inkscape.org/wiki/index.php/Using_the_Command_Line). Reālā konkrētajā hostā pieejamā CLI versija jāpārbauda, nevis jāuzmin.
- Adobe: [Print Actual size vs Fit](https://helpx.adobe.com/acrobat/desktop/print-documents/set-up-and-print-pdfs/page-size.html).

**Repo normatīvā prioritāte:** `AGENTS.md`, [Chat commands](CHAT_IMAGE_COMMANDS_V1.md), [assembly](CUT_PASTE_ASSEMBLY_V1.md), [exporter](CUT_PASTE_EXPORTER_V1.md), [QA](CUT_PASTE_QA_V1.md), [placement](CUT_PASTE_A4_PLACEMENT_V1.md), [Media standard](MEDIA_STANDARD_V1.md) un aktuālais `js/print.js`. Konfliktā ievēro stingrāko noteikumu; ārēja web dokumentācija neaizstāj vietnes implementācijas pierādījumu.
