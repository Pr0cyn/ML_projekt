# 04d – A hangolás eredménye és a két projekt (magyarázat)

## A két projekt felépítése

- `projects/decision_tree/` és `projects/random_forest/`: mindkettőben van egy saját `tune.py` (ebben a rács és a kiválasztási szabály), egy `best_params.json`, egy `cv_results.csv` az összes kombinációval, és egy riport a `reports/01_hangolas.md` fájlban.
- A GridSearchCV-logika közös, a `src/tuning.py` fájlban van. Így a két hangolás garantáltan ugyanúgy fut, ugyanazon az 5 foldon, mint az ML7.

## Eredmények (train-halmaz, 5-fold CV, macro F1)

| | DecisionTree | RandomForest |
|---|---|---|
| Alapbeállítás (ML7) | 0,921 | 0,912 |
| **Hangolt** | **0,923** | **0,925** |
| Választott beállítás | `max_depth=20`, `min_samples_leaf=1` | `class_weight='balanced_subsample'`, `min_samples_leaf=2` |
| Background F1 | 0,696 → 0,696 | **0,619 → 0,714** |
| Méret | 1 fa, mélység 20, 965 levél | 100 fa, 200 574 csomópont |

- **DecisionTree:** a hangolás nem javított érdemben. A kisebb fák (12-es vagy kisebb mélység) és a nagyobb levelek kifejezetten rontottak a ritka osztályokon. Egy 8 mély fa macro F1-e például csak 0,71. **A ritka osztályokhoz részletes fa kell.** Ez a mérés önmagában is jó érv a védésen.
- **RandomForest:** a `balanced_subsample` beállítás érdemben javított, mert minden fa a saját mintáján súlyozza a ritka osztályokat. A Background F1-e 0,62-ről 0,71-re nőtt. **A hangolás után a két modell gyakorlatilag egyforma.**

## Javítás menet közben

Az első DT-futtatásnál az „egy standard hiba” szabályt tévesen a **szórással** számoltam, nem a **standard hibával** (szórás / √5). A túl engedékeny küszöb miatt a szabály egy 15 mély, mérhetően gyengébb fát választott (macro F1 0,908, a Text osztály F1-e 0,86 helyett 0,78). Kijavítottam, és újrafuttattam.
