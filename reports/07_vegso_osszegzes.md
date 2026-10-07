# 07 – Végső összegzés

**Feladat:** a TII-SSRC-23 hálózati flow-k osztályozása 8 Traffic Type osztályba (4 támadás, 4 benign), klasszikus supervised ML-lel, scikit-learnnel. A fő metrika a **macro F1**, mert az adat extrém kiegyensúlyozatlan: a teljes adat 86,5%-a DoS, a benign forgalom csak 0,015%.

**Röviden:** mindkét végső modell 99,6%-os accuracy-t és 0,93–0,95-ös macro F1-et ért el a teszthalmazon (90 956 flow). A támadásokat 99%-nál pontosabban ismerik fel, a hibák szinte mind a ritka benign osztályokban vannak. A **RandomForest** a teszten jobb (macro F1 0,952 vs 0,926). A különbség nagy része azonban a 10 soros Background osztályból jön, egy-egy sor eltéréséből, ezért a két modell a gyakorlatban közel egyenértékű.

## 1. Végső eredmények a teszthalmazon

| | DecisionTree | RandomForest |
|---|---|---|
| **Macro F1** | **0,926** | **0,952** |
| Macro F1 95%-os bootstrap-intervallum | 0,889 – 0,953 | 0,923 – 0,971 |
| Balanced accuracy (osztályonkénti találati arány átlaga) | 0,935 | 0,954 |
| **Accuracy (találati arány)** | **99,60%** | **99,62%** |
| Helyes / hibás jóslat (90 956-ból) | 90 595 / 361 | 90 612 / 344 |
| Macro F1 a train-halmazon (5-fold CV, hangolás után) | 0,923 | 0,925 |

A tárgy 70%-os accuracy-követelményét mindkét modell bőven teljesíti. Ez a szám önmagában mégsem bizonyító erejű: egy modell, amely mindenre „támadás”-t mond, 99,6% körüli accuracy-t érne el, miközben egyetlen benign flow-t sem ismerne fel.

A teszten mért macro F1 egyezik a train-halmazon keresztvalidációval becsült értékkel, sőt kicsit jobb is. **A modellek nem tanultak túl, a modellválasztás becslése megbízható volt.**

## 2. Találati arány osztályonként (recall a teszthalmazon)

| Traffic Type | Tesztsorok | DecisionTree | RandomForest |
|---|---|---|---|
| DoS | 59 367 | 99,8% (59 241) | 99,8% (59 225) |
| Mirai | 15 569 | 99,0% (15 421) | 99,3% (15 465) |
| Bruteforce | 9 695 | 99,4% (9 639) | 99,3% (9 625) |
| Information Gathering | 5 938 | 99,9% (5 935) | 99,9% (5 933) |
| Video | 257 | 96,1% (247) | 96,5% (248) |
| Text | 63 | 84,1% (53) | 85,7% (54) |
| Audio | 57 | 89,5% (51) | 93,0% (53) |
| Background | 10 | 80,0% (8) | 90,0% (9) |

- **A négy támadásosztály** recallja mindkét modellnél 99% feletti.
- **A leggyakoribb tévesztés a DoS és a Mirai között** van, ami érthető, mert a Mirai is DDoS-forgalmat generál.
- **A benign osztályok gyengébbek,** különösen a Text és a Background. Ezekből kevés a tanítóadat: 146, illetve 22 sor.

## 3. Benign vagy Malicious

A modell a Traffic Type-ot jósolja, ebből vezetjük le a Label-t (Audio, Background, Text, Video → Benign).

| | DecisionTree | RandomForest |
|---|---|---|
| Benign találati arány (recall) | 95,3% (369 / 387) | 95,6% (370 / 387) |
| Benign precision | 93,2% | 93,0% |
| Malicious találati arány (recall) | 99,97% (90 542 / 90 569) | 99,97% (90 541 / 90 569) |
| Téves riasztás (benign → támadás) | 18 | 17 |
| Kihagyott támadás (támadás → benign) | 27 | 28 |

Ezen a szinten a két modell gyakorlatilag egyforma.

## 4. Idők és erőforrások

A mérések egy 24 szálas Intel Core Ultra 9 285K processzoron, 128 GB RAM mellett készültek.

| | DecisionTree | RandomForest |
|---|---|---|
| **Végső tanítás** (212 230 sor, 54 oszlop) | **2,4 s** (1 szál) | **2,9 s** (24 szálon párhuzamosan) |
| **Jóslás a teljes teszthalmazra** (90 956 flow) | **0,06 s** | **0,17 s** |
| Áteresztőképesség | kb. 1,6 millió flow / s | kb. 0,5 millió flow / s |
| Tanítás egy CV-foldon (ML7, alapbeállítás) | 1,9 s | 1,7 s |
| GridSearchCV (hangolás) | 28 kombináció × 5 fold, 42 s | 12 kombináció × 5 fold, 133 s |
| Modellméret (mentett Pipeline) | 0,26 MB | 25,7 MB |
| Modell felépítése | 1 fa, mélység 20, 965 levél | 100 fa, 200 574 csomópont |

Mindkét modell gyors. A RandomForest kb. 3-szor lassabban jósol, és 100-szor nagyobb, de így is valós idejű forgalomfeldolgozásra alkalmas.

## 5. Az összes kipróbált modell (ML7, 5-fold CV a train-halmazon, alapbeállítások)

| Modell | Macro F1 | Accuracy | Tanítás / fold | Eredmény |
|---|---|---|---|---|
| DecisionTree | 0,923 ± 0,017 | 99,56% | 1,9 s | továbbment, hangolva |
| RandomForest | 0,912 ± 0,018 | 99,49% | 1,7 s | továbbment, hangolva |
| HistGradientBoosting | 0,878 ± 0,041 | 99,48% | 12,5 s | kiesett: instabil foldonként |
| LogisticRegression | 0,581 ± 0,007 | 90,70% | 38,0 s | kiesett: 3 875 támadást benignnek vélt |

A LogisticRegression 90,7%-os accuracy mellett is alkalmatlan, mert a benign precisionje csak 18%. Ez a legjobb példa arra, miért nem az accuracy a fő metrika.

## 6. A teljes folyamat futási ideje (kb.)

| Lépés | Idő |
|---|---|
| ML2 – felmérés, CSV → Parquet konverzió (8,66 millió sor, 4,7 GB) | 70 s |
| ML3 – mintavétel és duplikátumszűrés | 10 s |
| ML4 – split | 5 s alatt |
| ML5 – oszlopelemzés + 3 opció CV-je | 40 s |
| ML6 – hiányzó adatok, 3 változat CV-je | 60 s |
| ML7 – 4 modell × 5 fold | 4,7 perc |
| Hangolás (GridSearchCV, két projekt) | 3,5 perc |
| ML8 – végső tanítás + teszt (két projekt) + bootstrap-összevetés | 6 perc |
| ML9 – permutation importance + top-k ellenőrzés | 5 perc |

A teljes folyamat a nyers CSV-ből kb. **25 perc** alatt újrafuttatható.

## 7. Melyik modell a jobb?

| Szempont | Nyertes |
|---|---|
| Macro F1 a teszten | RandomForest (0,952 vs 0,926) |
| Macro F1 a Background nélkül | gyakorlatilag döntetlen (0,959 vs 0,955) |
| Benign / Malicious szint | döntetlen |
| Stabilitás (permutation importance, ML9) | RandomForest: egyetlen oszlop sem nélkülözhetetlen |
| Sebesség és modellméret | DecisionTree |
| Értelmezhetőség | DecisionTree: egy fa, végigkövethető döntések |

**Összegezve:** ha a pontosság és a stabilitás a fontosabb, a **RandomForest** a jobb választás. Ha a magyarázhatóság és az erőforrásigény, a **DecisionTree**. A teszteredmények nem változtatnak ezen a mérlegelésen, mert a különbség nagy része 1–2 Background sorból jön.
