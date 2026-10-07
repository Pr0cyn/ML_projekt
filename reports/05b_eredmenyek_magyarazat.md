# 05b – A teszteredmények értelmezése (magyarázat)

## Eredmények a teszthalmazon (90 956 sor)

| | DecisionTree | RandomForest |
|---|---|---|
| **Macro F1** | **0,926** | **0,952** |
| Macro F1, train CV (a hangolásból) | 0,923 | 0,925 |
| Macro F1 a Background nélkül | 0,955 | 0,959 |
| Balanced accuracy | 0,935 | 0,954 |
| Accuracy | 99,60% | 99,62% |
| Téves riasztás (benign → malicious) | 18 | 17 |
| Kihagyott támadás (malicious → benign) | 27 | 28 |

**Osztályonkénti F1:** a négy támadásosztályon mindkét modell 0,99 fölött van. A különbség a Background osztályon jön ki, ahol a DT 0,73-at, az RF 0,90-et ért el.

## Mit jelentenek ezek a számok

- **A teszteredmény egyezik a keresztvalidációval,** sőt kicsit jobb is. A modellek tehát nem tanultak túl, a train-halmazon mért becslés megbízható volt.
- **A 70%-os accuracy-követelményt mindkét modell bőven teljesíti (99,6%).** Ez önmagában nem bizonyít semmit, ezért a riport a macro F1-et, az osztályonkénti eredményeket és a confusion matrixot helyezi előtérbe.
- **Az RF jobbnak tűnik, de a különbség szinte teljesen a 10 soros Background osztályból jön.** Ott az RF 9 sort talált el a 10-ből, a DT 8-at. Background nélkül a különbség csak 0,004. A teljes különbség (+0,026) 95%-os bootstrap-intervalluma +0,005 és +0,056 között van. Ez nem nulla, de a bizonytalanság nagy, mert mindössze 10 Background tesztsorra épül.
- **A benign/malicious szinten a két modell gyakorlatilag egyforma.** Mindkettő a 387 benign sorból kb. 18-at riaszt tévesen, és a 90 569 támadásból 27–28-at hagy ki.
- **Mire figyelni a confusion matrixon:** a leggyakoribb tévesztés a DoS és a Mirai között történik. Ez érthető, hiszen a Mirai is DDoS-forgalmat generál. A benign osztályok közül a Text-et keveri leginkább a támadásokkal.

## Hogyan készült

- **Közös kiértékelő modul:** `src/evaluation.py`. Mindkét projekt ugyanígy tanít a teljes train-halmazon, egyszer fut a teszten, elmenti a modellt (`models/pipeline.joblib`), és megírja a riportot két confusion matrix képpel.
- **Zár a kódban:** az első futás létrehoz egy `test_evaluated.json` fájlt, és ha ez már létezik, a szkript leáll. Így a „csak egyszer” szabály a kódban is érvényesül.
- **Összehasonlító riport:** `reports/05_eredmenyek.md`, benne a bootstrap-intervallum és az, hogy melyik modell mely sorokban téved.
