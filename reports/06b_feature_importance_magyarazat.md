# 06b – Feature importance: mit mutat? (magyarázat)

## Hogyan mértük

A permutation importance-t **a train-halmazon** mértük, az ML7-tel azonos 5 folddal. Minden foldban a projekt végső, hangolt Pipeline-ja 4 folddal tanult. Utána az ötödiken, amelyet nem látott, egyenként összekevertük az oszlopokat, és megmértük, mennyit esik a macro F1. A teszthalmazhoz így nem kellett újra nyúlni. Ha viszont a saját tanítóadatán mérnénk, a „bemagolt” összefüggések is fontosnak látszanának. Ezután ellenőriztük, hogy csak a legfontosabb k oszloppal mennyit veszítenek a modellek.

## A fő megállapítások

1. **A két modell nagyon másképp használja az oszlopokat.**
   - A **DecisionTree** néhány oszlopra erősen támaszkodik. A `Flow IAT Min` összekeverése 0,37-tel, a `Fwd Packet Length Max` és a `FWD Init Win Bytes` összekeverése kb. 0,35-tel rontja a macro F1-et. Egyetlen fánál minden döntési útvonal konkrét oszlopokra épül.
   - A **RandomForestnél** egyetlen oszlop sem nélkülözhetetlen: a legnagyobb esés is csak 0,058 (`FWD Init Win Bytes`). A 100 fa ugyanazt az információt több oszlopból is kiolvassa, ezért ha egy oszlopot elrontunk, a többi pótolja. **Ez a redundancia az RF stabilitásának oka.**

2. **A `Flow IAT Min` egészen máshol áll a két rangsorban: a DT-nél az 1., az RF-nél az 54., vagyis az utolsó.** Ennek az oszlopnak a negatív értékei csak az Audio és a Text osztályban fordulnak elő (ML6). Az RF ezek szerint biztosan nem erre a felvételi hibára építi az eredményét.

3. **Az ML5 döntéseit a mérés alátámasztja.** A korreláló párokból megtartott oszlopok több esetben a rangsor elején állnak (`Fwd Packet Length Max`, `Average Packet Size`, `Flow Duration`). A kidobott másolatokkal tehát nem veszett el információ. Az azonosító oszlopok (IP, port, Timestamp) nincsenek a modellben, így a modellek tényleg a forgalom viselkedéséből tanulnak.

4. **Kb. 20 oszlop is elég lenne:**

| Modell | Top 5 | Top 10 | Top 20 | Mind az 54 |
|---|---|---|---|---|
| DecisionTree | 0,749 | 0,820 | 0,918 | 0,924 |
| RandomForest | 0,760 | 0,902 | 0,932 | 0,918 |

20 oszloppal mindkét modell a zajon belül ugyanazt hozza, mint 54-gyel. Ezt a végső modelleken már nem változtattuk meg, de a „mit csinálnék másként” része.

## Menet közben

- **Korrelációs láncok:** a korreláló párok visszakeresésénél kiderült, hogy vannak láncok. A `Total Fwd Packet` például a `Subflow Fwd Packets` miatt esett ki, az pedig később a `Total Bwd packets` miatt. A riport ezért a láncot is mutatja.
- **A zaj nagysága:** ugyanaz az RF csak az oszlopok sorrendje miatt 0,918 helyett 0,925-öt is adhat. Ez kb. ±0,01 macro F1, ezért az ennél kisebb különbségeket zajnak kell tekinteni.
