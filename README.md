# Hálózati forgalom osztályozása klasszikus gépi tanulással

**AI-Based Solutions for Cyber Defence – 1. rész.** A TII-SSRC-23 adathalmaz hálózati flow-it (CICFlowMeter-kimenet, 8,66 millió sor) osztályozzuk 8 forgalomtípusba: 4 támadás (DoS, Mirai, Bruteforce, Information Gathering) és 4 benign (Video, Text, Audio, Background). A megoldás kizárólag scikit-learnt használ (mellette pandas, numpy, matplotlib, DuckDB). Két végső modell készült, egy **DecisionTree** és egy **RandomForest**, két külön projektként.

## Eredmények röviden

| Teszthalmaz (90 956 flow) | DecisionTree | RandomForest |
|---|---|---|
| **Macro F1** (fő metrika) | **0,926** | **0,952** |
| Accuracy | 99,60% | 99,62% |
| Balanced accuracy | 0,935 | 0,954 |
| Benign találati arány | 95,3% | 95,6% |
| Kihagyott támadás (a 90 569-ből) | 27 | 28 |
| Tanítási idő / jóslás a teljes teszthalmazra | 2,4 s / 0,06 s | 2,9 s / 0,17 s |

**Miért macro F1, és nem accuracy?** Az adat extrém kiegyensúlyozatlan: a teljes adat 86,5%-a DoS, és csak 1 301 benign sor van (0,015%). Egy modell, amely mindenre azt mondja, hogy „támadás”, 99% fölötti accuracy-t érne el, miközben egyetlen benign flow-t sem ismerne fel. A tárgy 70%-os accuracy-követelményét ezért teljesítjük ugyan, de ez önmagában nem bizonyít semmit. A macro F1 mind a 8 osztályt egyforma súllyal veszi figyelembe.

A RandomForest a teszten jobb. A különbség nagy része azonban a 10 soros Background osztályból jön (9/10 vs 8/10 találat). Background nélkül a macro F1 0,959 vs 0,955, a benign/malicious szinten pedig a két modell egyforma. Részletek: [reports/07_vegso_osszegzes.md](reports/07_vegso_osszegzes.md).

## A három döntés

### 1. Mely oszlopokat vettük ki, és miért? (86 → 54 jellemző)

Minden mérés csak a train-halmazon készült ([reports/02_oszlopok.md](reports/02_oszlopok.md)).

| Kategória | Db | Indok és mért bizonyíték |
|---|---|---|
| Azonosító és hálózati cím (Flow ID, Src/Dst IP, Src/Dst Port, Timestamp) | 6 | A tesztkörnyezet felépítését kódolják, nem a forgalom viselkedését. A 12–14 különböző IP-cím a sorok 82%-ában önmagában megmondja az osztályt. A Timestamp a Mirai osztálynál 2023-as, a többinél hibás, 1970-es dátum, így az évszám elárulja az osztályt. |
| Címkeoszlop (Label, Traffic Subtype) | 2 | A célváltozóból származnak. A Subtype 100%-ban meghatározza a Traffic Type-ot, a Label pedig a Traffic Type-ból következik. A Label-t a modell kimenetéből vezetjük le, nem bemenet. |
| Konstans | 5 | Egyetlen értéket vesznek fel, a varianciájuk 0 (pl. `Fwd Bulk Rate Avg`, `Bwd PSH Flags`). |
| Erősen korreláló pár gyengébb tagja | 18 | \|r\| > 0,95 egy megmaradó oszloppal, tehát gyakorlatilag ugyanazt mérik. Például az `Fwd Packet Length Mean` és az `Fwd Segment Size Avg` között r = 1,000. A párból az marad, amelyik több információt hordoz a célról (kölcsönös információ). |

**Alátámasztás:** a 72, 54 és 15 oszlopos változat 5-fold CV macro F1-e egy szóráson belül volt (0,915 / 0,912 / 0,907). A szűkítés tehát nem rontott, viszont minden kidobott oszlop mögött egy mért szám áll. Az ML9 permutation importance-e utólag megerősítette, hogy a korreláló párok megtartott tagjai fontosak, vagyis a másolatokkal nem veszett el információ.

### 2. Hogyan kezeltük a hiányzó adatokat?

([reports/03_hianyzo_adatok.md](reports/03_hianyzo_adatok.md))

- **Mérés:** a teljes adatban **nincs NaN és ±inf érték**, ezt a nyers CSV szövegén is ellenőriztük. A `Flow Duration` sehol sem 0, így nullával osztásból sem keletkezhetett végtelen érték.
- **Döntés:** a Pipeline-ban `inf → NaN` átalakítás és a train-halmazon illesztett **medián-imputálás** szerepel. Ez a mostani adaton semmit nem változtat, védőhálóként szolgál az új adatokhoz. A medián azért jobb az átlagnál, mert a flow-adatok erősen ferde eloszlásúak.
- **Sorok törlése nem jöhetett szóba.** Éles használatban minden flow-t osztályozni kell. Az egyetlen anomália, a negatív `Flow IAT Min`, ráadásul csak az Audio (23%) és a Text (14%) osztályban fordul elő, így a törlés ezt a két ritka osztályt tizedelte volna meg.
- **A negatív értékek változatlanok maradtak,** mert a keresztvalidáció szerint az átírásuk nem javított (macro F1 0,9120 vs 0,9117 vs 0,9142, zajon belül).

### 3. Miért ezt a tanítási módszert választottuk?

([reports/04_modellvalasztas.md](reports/04_modellvalasztas.md), [reports/04c_gridsearch_magyarazat.md](reports/04c_gridsearch_magyarazat.md))

**Modellválasztás** 5-fold rétegzett keresztvalidációval, a train-halmazon, macro F1 alapján, négy modellel:

| Modell (alapbeállítás) | CV macro F1 | Döntés |
|---|---|---|
| DecisionTree | 0,923 ± 0,017 | tovább, hangolva |
| RandomForest (`class_weight='balanced'`) | 0,912 ± 0,018 | tovább, hangolva |
| HistGradientBoosting | 0,878 ± 0,041 | kiesett: foldonként instabil (0,81–0,93) |
| LogisticRegression (skálázással) | 0,581 ± 0,007 | kiesett: 3 875 támadást benignnek vélt |

- **Miért fa alapú modell?** Az osztályhatárok nem lineárisak, a jellemzők erősen ferdék. A lineáris alapvonal ezt bizonyítja.
- **Miért `class_weight='balanced'`?** Így egy 22 soros Background osztály hibája ugyanannyit nyom a latba, mint a 138 ezer soros DoS-é.
- **Miért mindkét fa?** A DecisionTree és a RandomForest a zajon belül azonos volt, és két eltérő erősséget képviselnek. A DT értelmezhető és gyors, az RF stabilabb. Ezért két külön projektként vittük tovább, és a végén összevetettük őket.
- **Hangolás:** GridSearchCV a train-halmazon.
  - DT: `max_depth=20`, `min_samples_leaf=1` (egy standard hiba szabály alapján).
  - RF: `class_weight='balanced_subsample'`, `min_samples_leaf=2`. Ez a Background osztály F1-ét 0,62-ről 0,71-re emelte.

## Módszertani elvek

- **Korai split, nincs adatszivárgás.** A 70/30-as rétegzett split előtt csak két lépés történt, és egyik sem tanul az adatból: a rétegzett mintavétel (alosztályonként legfeljebb 20 000 sor, az összes benign sor) és a pontos duplikátumok kiszűrése. Minden, ami tanul az adatból (oszlopválasztás, imputálás, skálázás, hangolás), csak a train-halmazon történt.
- **Duplikátumok:** a szűrés a 77 jellemző és a 3 címke alapján történt, így a train és a test között **0 azonos jellemzővektor** van.
- **Minden tanuló lépés egy sklearn Pipeline-ban fut,** így a teszthalmazon pontosan ugyanaz hajtódik végre, és a keresztvalidáció minden foldjában újra illeszkedik.
- **A teszthalmazt projektenként egyszer használtuk.** Ezt a kódban egy zár is kikényszeríti (`test_evaluated.json`). A teszteredmény alapján nem hangoltunk utólag.
- **Reprodukálhatóság:** mindenhol `random_state=42`, a függőségek verzióit az `uv.lock` rögzíti.

## Mit csinálnék másként?

1. **Kevesebb oszlop.** Az ML9 szerint kb. 20 oszlop a zajon belül ugyanazt az eredményt adja, mint 54 ([reports/06_feature_importance.md](reports/06_feature_importance.md)). Egy ilyen második, modellalapú szűkítést a Pipeline-ba építenék (pl. `RFECV`), hogy foldonként tanuljon.
2. **Szigorúbb általánosítási teszt.** A véletlen split ugyanazon felvételek flow-it osztja szét train és test között, ezért a 0,95 körüli macro F1 azt mutatja, mennyire ismeri fel a modell *ezt* a tesztkörnyezetet. Egy új hálózatra való átvitelt felvételenként szétválasztott adattal vagy egy másik adathalmazzal mérnék. Időalapú split itt nem lehetséges, mert a Timestamp hibás.
3. **Több benign adat, főleg Background.** A 10 tesztsor miatt ennek az osztálynak minden metrikája bizonytalan, egyetlen sor 10 százalékpontot jelent. Ismételt keresztvalidációval vagy több adattal pontosabb becslést kapnánk.
4. **Költségérzékeny döntés.** Egy IDS-ben a kihagyott támadás drágább, mint a téves riasztás. A `predict_proba` kimenetén a benign döntési küszöböt erre hangolnám.
5. **Tisztességesebb alapvonalak.** A LogisticRegressiont log-transzformált jellemzőkkel, a HistGradientBoostingot korai leállítás nélkül is lefuttatnám, hogy az összevetés ne az alapbeállításokon múljon.
6. **A DecisionTree erősen támaszkodik a `Flow IAT Min` oszlopra,** amelynek negatív értékei felvételi hibák. Ennek a hatását külön megvizsgálnám. Az RF-et ez nem érinti, nála ez az oszlop az utolsó a fontossági sorrendben.

## Projektstruktúra

```
data/raw/data.csv                 nyers adat (Kaggle: daniaherzalla/tii-ssrc-23), nincs a repóban
data/processed/                   Parquet-fájlok: raw, sample, train, test (nincs a repóban)
src/                              közös kód és az ML2–ML10 lépések szkriptjei
  preprocessing.py                a Pipeline előfeldolgozó lépései (oszlopválasztás, inf → NaN, medián)
  selected_columns.json           az ML5-ben kiválasztott 54 oszlop
  tuning.py, evaluation.py        közös GridSearchCV- és kiértékelő logika
  predict.py                      jóslás egy mentett Pipeline-nal
projects/decision_tree/           DT-projekt: tune.py, evaluate.py, eredmények, riportok
projects/random_forest/           RF-projekt: ugyanez
  models/pipeline.joblib          a mentett végső Pipeline (DT: 0,26 MB, RF: 25,7 MB)
  models/metadata.json            verziók, paraméterek, oszlopok, eredmények
reports/                          riportok magyarul (01–07) és magyarázatok (b, c, d)
NOTES.md                          munkanapló lépésenként
```

## Futtatás

```bash
uv sync
```

A nyers CSV-t a `data/raw/data.csv` helyre kell tenni (Kaggle: `daniaherzalla/tii-ssrc-23`, csak a CSV kell, a PCAP-ok nem). Utána a lépések sorrendben:

```bash
uv run python src/ml2_survey.py
uv run python src/ml3_sample.py
uv run python src/ml4_split.py
uv run python src/ml5_columns.py
uv run python src/ml6_missing.py
uv run python src/ml7_model_selection.py
uv run python projects/decision_tree/tune.py
uv run python projects/random_forest/tune.py
uv run python projects/decision_tree/evaluate.py
uv run python projects/random_forest/evaluate.py
uv run python src/ml8_compare.py
uv run python src/ml9_importance.py
uv run python src/ml10_package.py
```

Az `evaluate.py` csak akkor fut le, ha a projekt `test_evaluated.json` fájlja még nem létezik (a teszthalmaz egyszeri használata). Teljes újrafuttatás előtt ezt törölni kell. A teljes folyamat kb. 25 perc egy 24 szálas gépen.

Jóslás új flow-kra egy mentett Pipeline-nal:

```bash
uv run python src/predict.py random_forest flows.csv predictions.csv
```

## Riportok

| Riport | Tartalom |
|---|---|
| [01_felmeres.md](reports/01_felmeres.md) | ML2: oszlopok, címkeeloszlás, hiányzó és végtelen értékek |
| [01b_mintavetel.md](reports/01b_mintavetel.md) | ML3: rétegzett minta, duplikátumok |
| [01d_split.md](reports/01d_split.md) | ML4: train/test split, osztályarányok |
| [02_oszlopok.md](reports/02_oszlopok.md) | ML5: oszlopválasztás, minden oszlop bizonyítékkal |
| [03_hianyzo_adatok.md](reports/03_hianyzo_adatok.md) | ML6: hiányzó adatok |
| [04_modellvalasztas.md](reports/04_modellvalasztas.md) | ML7: modellválasztás |
| [05_eredmenyek.md](reports/05_eredmenyek.md) | ML8: teszteredmények, a két modell összevetése |
| [06_feature_importance.md](reports/06_feature_importance.md) | ML9: permutation importance |
| [07_vegso_osszegzes.md](reports/07_vegso_osszegzes.md) | Végső összegzés: eredmények, idők, erőforrások |
