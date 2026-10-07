# 04 – Modellválasztás (ML7, döntési pont)

Minden mérés a **train-halmazon** (212 230 sor) készült, 5-fold rétegzett keresztvalidációval (`StratifiedKFold`, shuffle, random_state=42). Mind a négy modell ugyanazokon a foldokon fut. Minden jelölt egy teljes Pipeline: az ML5–ML6 előfeldolgozás (54 oszlop, inf → NaN, medián-imputálás) + a modell, így az imputálás és a skálázás foldonként csak a tanító részen illeszkedik. A teszthalmazt nem érintettem.

A modellek alapbeállításokkal futnak (hiperparaméter-hangolás nélkül), mindegyik `class_weight='balanced'`-del, hogy a ritka osztályok hibája nagyobb súllyal számítson. A feladat a DecisionTree, RandomForest és LogisticRegression összevetését kéri; a HistGradientBoosting a scikit-learn gradient boosting modellje, összehasonlításként szerepel.

## 1. Fő eredmények (foldok átlaga ± szórása)

| Modell | Macro F1 | Accuracy | Balanced accuracy | Tanítási idő / fold | Jóslási idő / fold |
|---|---|---|---|---|---|
| DecisionTree | 0.9229 ± 0.0171 | 0.9956 ± 0.0002 | 0.9265 ± 0.0195 | 1.9 s | 0.05 s |
| RandomForest | 0.9120 ± 0.0183 | 0.9949 ± 0.0002 | 0.9164 ± 0.0255 | 1.7 s | 0.12 s |
| LogisticRegression | 0.5814 ± 0.0072 | 0.9070 ± 0.0024 | 0.8767 ± 0.0283 | 38.0 s | 0.06 s |
| HistGradientBoosting | 0.8778 ± 0.0409 | 0.9948 ± 0.0008 | 0.9305 ± 0.0248 | 12.5 s | 0.07 s |

A balanced accuracy az osztályonkénti recall átlaga, ezért a ritka osztályokat ugyanúgy súlyozza, mint a nagyokat. Az accuracy itt félrevezető, mert a DoS a sorok 65%-a.

## 2. Macro F1 foldonként

| Modell | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 |
|---|---|---|---|---|---|
| DecisionTree | 0.9219 | 0.9333 | 0.9397 | 0.8908 | 0.9289 |
| RandomForest | 0.8989 | 0.9302 | 0.9245 | 0.8823 | 0.9238 |
| LogisticRegression | 0.5770 | 0.5727 | 0.5834 | 0.5940 | 0.5800 |
| HistGradientBoosting | 0.8587 | 0.9292 | 0.8722 | 0.8144 | 0.9141 |

## 3. F1 osztályonként (a keresztvalidált jóslatokon)

| Traffic Type | Sorok (train) | DecisionTree | RandomForest | LogisticRegression | HistGradientBoosting |
|---|---|---|---|---|---|
| DoS | 138524 | 0.998 | 0.997 | 0.948 | 0.997 |
| Mirai | 36328 | 0.990 | 0.988 | 0.825 | 0.989 |
| Bruteforce | 22620 | 0.994 | 0.992 | 0.927 | 0.994 |
| Information Gathering | 13856 | 0.999 | 0.999 | 0.841 | 0.999 |
| Video | 601 | 0.936 | 0.927 | 0.251 | 0.858 |
| Text | 146 | 0.856 | 0.879 | 0.249 | 0.787 |
| Audio | 133 | 0.902 | 0.895 | 0.382 | 0.792 |
| Background | 22 | 0.696 | 0.619 | 0.177 | 0.556 |

## 4. Benign vagy Malicious (a jósolt Traffic Type-ból levezetve)

A modell nem jósol külön Label-t: a jósolt Traffic Type-ot alakítjuk át (Audio, Background, Text, Video → Benign; a többi → Malicious). A „kihagyott benign” azt jelenti, hogy egy benign flow-t támadásnak minősített (téves riasztás); a „benignnek vélt támadás” a veszélyesebb hiba.

| Modell | Benign recall | Benign precision | Benign F1 | Kihagyott benign | Benignnek vélt támadás |
|---|---|---|---|---|---|
| DecisionTree | 0.9468 | 0.9344 | 0.9405 | 48 | 60 |
| RandomForest | 0.9479 | 0.9213 | 0.9344 | 47 | 73 |
| LogisticRegression | 0.9490 | 0.1809 | 0.3039 | 46 | 3875 |
| HistGradientBoosting | 0.9612 | 0.7652 | 0.8521 | 35 | 266 |

## 5. Értelmezhetőség és méret

| Modell | Méret (1. fold) | Értelmezhetőség |
|---|---|---|
| DecisionTree | 1 fa, mélység 31, 926 levél | Magas: egyetlen fa, a döntési szabályok kiolvashatók és lerajzolhatók (ha a fa nem túl mély). |
| RandomForest | 100 fa, összesen 175 672 csomópont | Közepes: sok fa szavaz, egy döntés nem követhető végig, de a jellemzők fontossága (impurity és permutation importance) jól mérhető. |
| LogisticRegression | 432 együttható (8 osztály × 54 jellemző) | Magas: osztályonként egy-egy súly minden jellemzőhöz, előjellel és nagysággal (skálázott adaton összevethetők). |
| HistGradientBoosting | 27 iteráció × 8 osztály = 216 fa | Alacsony–közepes: sok, egymásra épülő kis fa; csak permutation importance-szel értelmezhető. |

## 6. Értékelés

- **DecisionTree és RandomForest gyakorlatilag fej fej mellett van.** Átlagban a DecisionTree jobb (0,923 vs 0,912), és mind az 5 foldban magasabb a macro F1-e. A különbség azonban egy szóráson belül van, és szinte teljesen a legkisebb osztályokból jön. A Background osztályból foldonként kb. 4–5 sor jut a validációra, így egy-két sor eltérése már látszik a macro F1-ben. A nagy osztályokon a két modell egyforma (F1 ≥ 0,99).
- **A LogisticRegression ennél az adatnál alkalmatlan** (macro F1 0,58). A forgalmi jellemzők erősen ferde eloszlásúak, az osztályok határa pedig nem lineáris. A benign osztály precisionje 0,18: 3 875 támadást minősített benignnek, ami egy IDS-ben a legsúlyosabb hiba. Alapvonalnak viszont hasznos, mert megmutatja, hogy a feladathoz nemlineáris modell kell.
- **A HistGradientBoosting instabil** (foldonként 0,81–0,93). Alapbeállításban 10%-ot félretesz a korai leállításhoz, így a ritka osztályokból még kevesebb tanítósor marad, és már 27 iteráció után leáll. Hangolással javulna, de alapbeállításban nem versenyképes a fákkal.
- **Gyorsaság:** a DecisionTree és a RandomForest foldonként kb. 2 másodperc alatt tanul, a LogisticRegression 38, a HistGradientBoosting 12 másodperc alatt.
- **Értelmezhetőség:** a DecisionTree egyetlen fa, a döntési útvonala végigkövethető. Ez a fa azonban 31 mély és 926 levelű, ezért egészében nem rajzolható le olvashatóan. A RandomForest fekete dobozabb, de mindkettő jellemzőfontossága mérhető (ML9).

## Döntés

**Mindkét fa alapú modellt továbbvisszük, két külön projektként: `projects/decision_tree/` és `projects/random_forest/`.** A LogisticRegression (macro F1 0,58, 3 875 benignnek vélt támadás) és a HistGradientBoosting (foldonként 0,81–0,93, instabil) kiesett. Mindkét projektben előbb GridSearchCV-vel hangoljuk a hiperparamétereket a train-halmazon, majd mindkét végső modell egyszer fut a teszthalmazon. A végén a két projekt eredményét összevetjük, de a teszteredmény alapján már nem hangolunk.
