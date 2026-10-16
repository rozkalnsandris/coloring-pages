# Ausmalwiese Cut & Paste — vienotais darba standarts v1

**Status (2026-10-17): SOURCE/DOCS ONLY — jaunais sikspārņa kandidāts nav publicēts.** Šis ir ilgtermiņa *authoring + QA playbook* visiem sezonu tēliem, nevis pierādījums, ka rīks autonomi izpilda katru soli. Šīs lapas autorēšana/merge nekad nepiešķir `PUBLISH`, Drive, RPi5/LIVE, DNS/Cloudflare, permissions vai secrets tiesības.

**Aktīvs īpašnieka HOLD:** šajā darba posmā Cut & Paste publicēšanu atliek līdz pilnīgai pārejai uz **ausmalwiese.de** un atsevišķai precīzā komplekta apstiprināšanai. Šis HOLD nav pielīdzināms pastāvīgai tehniskai iespējošanas pazīmei; vēlāk īpašnieka jauna `PUBLISH` komanda, svaiga operatīvās drošības pārbaude un visu kvalitātes vārtu PASS ir obligāti. Nepieņemt, ka domēna pāreja ir pabeigta no GitHub merge, vecas sarunas vai HTTP pieejamības vien.

## 1. Komandas un nepārprotamas robežas

| Komanda | Darbība | Ko tā nedod |
| --- | --- | --- |
| `CUT <subject>` | Īsā komanda **vienam** divu lapu Cut & Paste melnrakstam; ekvivalenta `MAKE Cut & Paste <subject>` | Nav izvietošanas, merge vai publikācijas |
| `MAKE Cut & Paste <subject>` | Izveido sākotnējo tēlu un abas savstarpēji saskaņotās lapas saskaņā ar šo līgumu | Nav garantēta fiziska izgriežamība |
| `EDIT <exact instruction>` | Maina tikai nosauktās detaļas *vienā kanoniskajā avotā* un pēc tam atjauno visus atvasinātos attēlus | Vecie validācijas rezultāti kļūst nederīgi |
| `REMAKE` | Veido jaunu kompozīciju, nevis slepeni aizvieto apstiprinātas detaļas | Nav iepriekšējā varianta apstiprinājuma |
| `VALIDATE-PRINT` | Tikai precīzā gala A4 PNG tehniskā pārbaude | Nav ģeometriskas salikšanas vai fiziska testa PASS |
| `PUBLISH` | Atsevišķa, svaiga, īpašnieka precīza publikācijas atļauja, **tikai pēc HOLD atcelšanas un jaunā satura apstiprināšanas** | Nav LIVE deploy, overwrite vai rollback atļaujas |

Parastais `MAKE <subject>` joprojām veido **vienu** krāsojamo lapu. `CUT` nav komanda ģenerēt vairākus tēlus vienā reizē, atvērt individuālu GitHub issue katram tēlam vai automātiski publicēt.

Piemēri: `CUT Fledermaus`, `CUT Halloween Kürbis`, `CUT Weihnachten Schneemann`. Vispirms pabeidz un apstiprini vienu tēlu, tikai pēc tam sāc nākamo. Iekšējā saruna — latviski, gala lietotāja nosaukumi un norādes — vāciski.

## 2. Mākslinieciskais kvalitātes standarts

Mērķauditorija: **Familien, Kitas und Vorschulen in Deutschland**, bērni 3–6 gadi. Galvenajam tēlam jābūt bērniem pievilcīgam, skaidri atpazīstamam un oriģinālam; biezas tumšas kontūras, lielas formas, noapaļotas savienojumu vietas, konsekventas krāsas uz balta fona. **Neveidot primitīvus ovālu/trijstūru/taisnstūru salikumus**, kuros detaļas izskatās kā mehāniski bloki, nevis vienots tēls. Lai ornaments vai detaļa ir dekoratīva tikai tad, ja tā reāli parādās gatavajā tēlā.

Parasti **bez cepurēm, lieka fona un aksesuāriem**, ja tie nav tieši prasīti. Izvēlies tikai konkrētajam tēlam atbilstošās atdalāmās detaļas: ausis, spārnus, ķepas/rokas/kājas, acis, degunu/knābi, muti u.c. **Neuzspiest** visas šīs detaļas katram tēlam. Mazās uzacis, zobi, skropstas u.c. kā individuāli izgriezumi ir bērnam potenciāli sarežģīti — vajadzīga īpaša cilvēka griešanas pārbaude; ja tā nav izmantojama, pārveido izstrādājumu **kanoniskajā avotā**.

Vizuālā pieņemšana ir cilvēka solis. CI PASS pierāda tikai testētos invariantu gadījumus, nevis skaistu ilustrāciju. Gaidošs atsevišķs art-review PR (vēsturiski #239) nav jāuzskata par merged vai pieņemtu, kamēr tas nav aktuāli pārbaudīts.

## 3. Viens kanoniskais tēls: neatkarīgas kopijas ir AIZLIEGTAS

**Source of truth:** rediģējams SVG part tree + versēts JSON salikuma manifests; skat. [assembly v1](CUT_PASTE_ASSEMBLY_V1.md) un `metadata/cut-paste-character-v1.schema.json`. Katram elementam vienreiz piešķir:
- stabilu unikālu `part_id` un lomu `base` / `cutout`;
- precīzu ārējo kontūru, iekšējo zīmējumu, krāsu, mērogu milimetros un orientāciju;
- salikšanas koordinātas, rotāciju, simetrijas pusi un slāņu secību;
- priekšpusē pieejamu līmēšanas mērķi, kontakta laukumu un darbību secību.

No **tā paša** ieraksta atvasini **(a)** lielo rumpi uz 1. lapas, **(b)** izgriežamos elementus uz 2. lapas, **(c)** mazo gatavā tēla paraugu uz 1. lapas, **(d)** diagnostikas salikuma attēlu (*assembly proof*). Parauga detaļu skaits, forma un proporcijas obligāti sakrīt ar faktiski izgriežamajām detaļām pēc vienas globālas parauga mērogošanas. Nedrīkst salikt 1. lapu no vecā PDF un 2. lapu no jauna PDF, ja salikuma versijas/hashi atšķiras, pat ja abas lapas atsevišķi ir skaistas un A4 PASS.

Katru anatomijas elementu izvēlies **vienreiz**: ja ausis/spārni/ķepas/acis ir `cutout`, tie **nedrīkst** būt jau uzzīmēti uz lielās pamatnes. Vienai detaļai ir tieši viena lietošanas vieta; bez dublikātiem vai neizmantotām detaļām. Slāņu secība un līmēšana tikai pieejamā priekšpusē; bērnam nav jācenšas iebāzt detaļu aiz gatava, neatdalāma objekta. Spārni sikspārnim jāpievieno **rumpja/vēdera sānos**, nevis sejas vai galvas vidū.

**Svarīgs izņēmums pie iepriekš esošu PNG glābšanas:** precīza izgriešana/izvietošana ar programmatūru ir pieļaujama kā pagaidu mākslas restaurācija, nevis pilnvērtīgs kanoniskā SVG pierādījums. Jāreģistrē katras daļas avots, faktiskais izmēra koeficients, jaunās līmēšanas vietas, un jāiegūst jauns kopējā salikuma un fiziskais apstiprinājums. Ja avota un parauga sakritību nav iespējams pierādīt, STOP, nevis atzīmēt `assembly PASS`.

## 4. Lapu līgums un precīzi drukas aprēķini

1. **`01 Körper/Grundform`:** tikai liels rumpis, pareizā vietā un nemainīgā mērogā; **mazs saliktais paraugs pašā augšā**. Paraugs neaizskar ne rumpja izgriešanas kontūru, ne potenciālo saliktā tēla ar spārniem/ausīm pilno aizņemto laukumu.
2. **`02 Ausschneideteile`:** visas un tikai detaļas, kuru vajag salikumam; katra tieši vienreiz; atsevišķa, slēgta, uz ārpusi nobīdīta **pārtraukta griešanas kontūra**. Nekad nepārtrauktā mākslas kontūra nav jāaizvieto ar pārtrauktu. Bērna šķērēm atstāj vismaz QA noteiktos **4 mm starp griešanas līniju stroke envelopes**, nevis tikai starp krāsainajiem objektiem.

Portrait A4: **210×297 mm = 2480×3508 RGB PNG**, aptuveni **300 DPI**. Precīzi balta `#FFFFFF` 15 mm josla (rastera pārbaudē 177 px). Taču `js/print.js` reālais **no-downscale visible ink** laukums ir stingrāks: `x=17..193 mm` un `y=17..256 mm`. Tātad platums **176 mm**, augstums **239 mm**, zem zīmējuma rezervēti **41 mm** (vietnes footer, atstarpe, apakšējā mala), papildus **2 mm** kontūru rezerve. `15 mm` nav pareizs mērķis mazā parauga redzamajai augšmalai; jābūt ap **17 mm** ar 1–2 px rezervi.

Pie rastra A4 efektīvā koordinātu pārrēķina (ievērojot attiecīgā eksporta izmēru):
- `x_mm = x_px × 210 / 2480`; `y_mm = y_px × 297 / 3508`;
- piemēram, augšējā drošā robeža ap **201 px**, apakšējā ap **3023 px** (pārbaudot *inclusive* pēdējo pikseli), bet lieto faktisko baitu rastra `visibleInkBounds` rezultātu, nevis noapaļojumu kā apliecinājumu;
- `inkWidth = (right-left+1) × 210/2480`, `inkHeight = (bottom-top+1) × 297/3508`;
- `scale = min(1, 176/inkWidth, 239/inkHeight)`. Vajadzīgs **scale = 1.0**, bez pārslēgšanās uz mazāku.

**Izkārtojuma algoritms:** nosaki atsevišķi mazā parauga un rumpja *redzamās tintes* bounding box; pārvieto paraugu augšup līdz ~17 mm, rumpi lejup, līdz tā griešanas līnijas pēdējais punkts ir droši pirms 256 mm; pārvieto kā atsevišķus slāņus, nevis visu PNG kopā. Pārbaudi **pilno lielo salikumu** ar spārniem/ausīm, ne tikai rumpi — horizontāli nekas nedrīkst iziet no atļautās zonas vai aizskart blakus esošus objektus. Ja pilns tēls neietilpst, to pārprojektē kanoniskajā mēroga/transformāciju kokā un **ģenerē abas lapas no jauna**, nevis slepeni samazina vienu rastra lapu.

**Uzmanību:** vietnes `fitA4InkBounds` vēl arī **centrē kopējo redzamās tintes laukumu** pēc aprēķinātā `scale`. Tādēļ tikai PNG koordinātas vien nevar apliecināt, ka uz **fiziskās** izdrukas paraugs būs tieši 17 mm un rumpis tieši 256 mm. Pārbaudi pēc pilnās `js/print.js` transformācijas un vajadzības gadījumā faktiski izdrukā!

## 5. Griešanas un izmēru labošanas noteikumi

- Katra cut līnija ir atvasināta no precīza vektora ārējā silueta (derīgs, slēgts, bez self-intersection) ar ārēju offset; SVG `stroke-dasharray` kontrolē tikai svītrojumu. Skat. [QA v1](CUT_PASTE_QA_V1.md).
- Pirms samazināšanas **izmēri ar lineālu** reālā 100% A4 testā: cik mm spārna gals pārsniedz vēlamo pozīciju, pilnās samontētās figūras platums, acu/mutes/smagāko detaļu salīdzinājums pret rumpi. Telefona fotogrāfija ar perspektīvu dod tikai *aptuvenu* proporciju norādi, neprecīzu fizisku mm mērījumu; pēc tās nevar deklarēt garantētu salīmēšanu.
- Ja 10–12% samazināti spārni, 10% acis, deguns vai mute: dokumentē **katru pirms/pēc mm un koeficientu**, atjaunini tieši tās pašas detaļas arī mazajā paraugā **no kanoniskās ģeometrijas**, pārskati līmēšanas enkurus un visu figūras gala bbox, izvada abas lapas atkārtoti.
- Ja pirmā lapa ir iesaldēta, saglabā visu rumpja reģionu bitu/pikseļu identisku un maini tikai iepriekš skaidri norādīto parauga slāni. Ja paraugu nav iespējams labot tā, lai tas sakristu ar 2. lapu, **STOP**, nelieto veco paraugu kā gatavas jaunās lapas apliecinājumu.
- Uzacis vai citas no jauna pievienotas detaļas ir jāparāda **abās** atvasinātajās vietās (paraugs un cutout), ar cut kontūru un reāli lietojamu līmēšanas vietu. Tikai skaists rastra ielāps nav ģeometriskas saderības pierādījums.
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
- `PHYSICAL_QA` — `PENDING|PASS|FAIL`; īsts 100% A4 izdrukāts, izgriezts, salīmēts (sikspārnis un cits tēls pirms foundation #221 slēgšanas), foto/izmēri, atbilstība mazajam paraugam.
- `OWNER_APPROVAL` — `PENDING|PASS|FAIL`; precīzajai divu lapu SHA identitātei, nevis abstraktai idejai.
- `PUBLISH` — `HOLD|NOT_REQUESTED|STOP|PASS`. Šajā brīdī **HOLD**, nevis PASS.

**STOP noteikumi:** jebkurš `FAIL`, nezināms SHA, neatbilstošs paraugs, nesamontējamas detaļas, pārāk mazi fragmenti, kļūdaina print zone vai derīga `file_uri/source_file_ref` neesība aptur virzīšanu. Nemaini attēlus pēc apstiprinājuma bez pilnas pārvalidēšanas.

## 9. Atkārtojamais process sezonām

`#218` ir kopīgais plāns, `#219` kanoniskā shēma, `#220` exporters, `#221` QA/human gates, `#222` Halloween un `#223` Weihnachten sezonas saraksti. **Nav atsevišķa GitHub issue katram tēlam**, ja vien neparādās atsevišķa programmatūras kļūda.

Vienam tēlam: **ideja → mākslas master + detaļu inventārs → art review → kanoniska salikšana/anchor → abpusējs A4 exports + assembly proof → automātiskie geometry/print testi → 100% fiziska izgriešana/salīmēšana → exact-SHA owner review → HOLD vai atsevišķa PUBLISH komanda**. Tikai pēc PASS un atsevišķas atļaujas pārej pie publicēšanas; pēc tam nākamais sezonas tēls. Krāsainie Cut & Paste materiāli ir apzināti krāsaini, nevis parastās vienkrāsainās krāsojamās lapas.

Kad īpašnieks vēlāk vēlas publicēt: svaigi pārbaudi `coloring-pages/main`, `RPi5_main/main`, **instalētā** operatora un importer attēla atbilstību, LIVE katalogu/ID, precīzās galīgās *bez-footer* PNG, kanonisko A4 prepare+validate un v2 2 lapu manifestu. Pirms **jebkura** Drive mutation jau jābūt visām stabilajām upload atsaucēm; abas PNG augšupielādē manifestam **pirms**, manifests **pēdējais**. Trūkumi ⇒ STOP, pēc pirmās mutācijas nekāda retry/rollback/cleanup/surface switching.

## 10. Publiski tehniskie avoti (dizaina skaidrojumiem, ne LIVE statusam)

- MDN: [CSS `@page`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40page), [Paged media](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Paged_media) un [Printing](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing).
- MDN: [SVG `stroke-dasharray`](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/stroke-dasharray) un [`stroke-linejoin`](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/stroke-linejoin).
- Inkscape: [CLI SVG → PNG export](https://wiki.inkscape.org/wiki/index.php/Using_the_Command_Line). Reālā konkrētajā hostā pieejamā CLI versija jāpārbauda, nevis jāuzmin.
- Adobe: [Print Actual size vs Fit](https://helpx.adobe.com/acrobat/desktop/print-documents/set-up-and-print-pdfs/page-size.html).

**Repo normatīvā prioritāte:** `AGENTS.md`, [Chat commands](CHAT_IMAGE_COMMANDS_V1.md), [assembly](CUT_PASTE_ASSEMBLY_V1.md), [exporter](CUT_PASTE_EXPORTER_V1.md), [QA](CUT_PASTE_QA_V1.md), [placement](CUT_PASTE_A4_PLACEMENT_V1.md), [Media standard](MEDIA_STANDARD_V1.md) un aktuālais `js/print.js`. Konfliktā ievēro stingrāko noteikumu; ārēja web dokumentācija neaizstāj vietnes implementācijas pierādījumu.
