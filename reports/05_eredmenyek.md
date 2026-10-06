# 05 – Végső eredmények a teszthalmazon (ML8)

Mindkét projekt végső Pipeline-ja a teljes train-halmazon tanult, majd **egyszer** futott a teszthalmazon (90 956 sor). A projektenkénti részletes riportok: `projects/decision_tree/reports/02_eredmenyek.md` és `projects/random_forest/reports/02_eredmenyek.md` (benne a confusion matrix képekkel).

## 1. Összesített metrikák

| Metrika | DecisionTree | RandomForest |
|---|---|---|
| **Macro F1 (teszt)** | **0.9262** | **0.9517** |
| Macro F1, 95% bootstrap-intervallum | 0.889 – 0.953 | 0.923 – 0.971 |
| Macro F1 (train CV, hangolás) | 0.9233 | 0.9254 |
| Macro F1 a Background nélkül (7 osztály) | 0.9547 | 0.9591 |
| Balanced accuracy | 0.9349 | 0.9544 |
| Accuracy | 0.9960 | 0.9962 |
| Tanítási idő (teljes train) | 2.4 s | 2.9 s |

A 70%-os accuracy-követelményt mindkét modell teljesíti, de a 65%-os DoS-arány miatt ez önmagában nem bizonyít semmit; a fő metrika a macro F1.

## 2. Osztályonkénti F1

| Traffic Type | Tesztsorok | DT precision | DT recall | DT F1 | RF precision | RF recall | RF F1 |
|---|---|---|---|---|---|---|---|
| DoS | 59367 | 0.998 | 0.998 | 0.998 | 0.999 | 0.998 | 0.998 |
| Mirai | 15569 | 0.991 | 0.990 | 0.991 | 0.990 | 0.993 | 0.992 |
| Bruteforce | 9695 | 0.994 | 0.994 | 0.994 | 0.993 | 0.993 | 0.993 |
| Information Gathering | 5938 | 1.000 | 0.999 | 1.000 | 0.999 | 0.999 | 0.999 |
| Video | 257 | 0.925 | 0.961 | 0.943 | 0.925 | 0.965 | 0.945 |
| Text | 63 | 0.869 | 0.841 | 0.855 | 0.857 | 0.857 | 0.857 |
| Audio | 57 | 0.911 | 0.895 | 0.903 | 0.930 | 0.930 | 0.930 |
| Background | 10 | 0.667 | 0.800 | 0.727 | 0.900 | 0.900 | 0.900 |

## 3. Benign vagy Malicious

|  | DecisionTree | RandomForest |
|---|---|---|
| Benign recall | 0.9535 | 0.9561 |
| Benign precision | 0.9318 | 0.9296 |
| Malicious recall | 0.9997 | 0.9997 |
| Téves riasztás (benign → malicious) | 18 | 17 |
| Kihagyott támadás (malicious → benign) | 27 | 28 |

## 4. Mennyire biztos a különbség?

- **A macro F1 különbsége (RF − DT): +0.0255**, a páros bootstrap 95%-os intervalluma +0.0049 – +0.0556 (2000 újramintavételezés, random_state=42).
- A Background osztály nélkül a különbség +0.0045. A Background osztályból mindössze 10 tesztsor van, így egyetlen sor 0,1-et mozdít az osztály recallján, és ez a macro F1-ben 1/8-os súllyal jelenik meg.
- Hibás jóslatok: mindkét modell téved 247 sorban; csak a DT téved 114, csak az RF 97 sorban.
- A tesztértékek nem lettek modellválasztásra használva: mindkét modell a train-halmazon hangolt beállításokkal, előre rögzítve futott, és ez az összevetés csak beszámol az eredményről.
