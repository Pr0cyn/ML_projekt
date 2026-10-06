# 04b – Döntési fa, RandomForest, foldok és F1 (magyarázat)

A RandomForest („véletlen erdő”) sok döntési fából áll, ezért előbb a döntési fát érdemes megérteni.

## 1. Döntési fa (DecisionTree)

A döntési fa **igen/nem kérdések sorozata**, mint egy barkochba. Minden kérdés egyetlen oszlopra vonatkozik, és egy küszöbértéket vizsgál. Egy leegyszerűsített példa az adatunk alapján:

```
                 Average Packet Size ≤ 60?
                  /                    \
               igen                    nem
                /                        \
     Flow Duration ≤ 0,5 s?        Dst-oldali bájtok ≤ 1000?
        /          \                  /              \
     DoS        Information        Bruteforce        Video
              Gathering
```

**Hogyan tanul a fa?**
1. Végignézi az összes oszlopot és az összes lehetséges küszöböt, és azt a kérdést választja, amelyik a sorokat **a legtisztábban** választja szét. A cél, hogy egy-egy ágra lehetőleg egyfajta osztály kerüljön.
2. A tisztaságot a **Gini-index** méri, ez a scikit-learn alapértelmezése. Értéke 0, ha egy csoportban csak egy osztály van, és annál nagyobb, minél vegyesebb a csoport.
3. Ezt minden ágon megismétli, amíg a csoportok tiszták nem lesznek, vagy már nincs mit szétválasztani. A végpontokat **leveleknek** hívjuk, és mindegyik egy osztályt mond ki.

**Jóslás:** egy új flow a gyökértől indul, és a kérdésekre adott válaszok alapján lefelé halad, amíg egy levélbe nem ér. A levél osztálya lesz a jóslat. Ezért **értelmezhető**: minden döntéshez megadható, melyik kérdések vezettek oda.

**A `class_weight='balanced'` szerepe:** a fa a tisztaság számolásakor a ritka osztályok sorait nagyobb súllyal veszi figyelembe. Egy Background sor így körülbelül annyit számít, mint több ezer DoS sor. Enélkül a fa nem foglalkozna a 22 Background sorral.

**A gyengesége a túltanulás.** Ha hagyjuk, a fa addig kérdez, amíg minden tanító sort tökéletesen be nem sorol. A mi fánk is ezt tette: 31 kérdés mélységig ment, 926 levéllel. Ilyenkor a legalsó kérdések már nem általános szabályokat tanulnak meg, hanem egyedi sorokat. Ráadásul az adat kis változására teljesen más fa jöhet ki.

## 2. RandomForest (véletlen erdő)

A RandomForest **sok döntési fa szavazása**, nálunk 100 fáé. Két véletlen elem miatt lesznek a fák különbözők:

1. **Véletlen sorok, idegen szóval bootstrap:** minden fa egy saját mintán tanul. Ez visszatevéses húzással készül a tanító sorokból, így egyes sorok többször, mások egyszer sem kerülnek bele. Egy fa átlagosan a különböző sorok kb. 63%-át látja.
2. **Véletlen oszlopok:** minden kérdésnél a fa nem mind az 54 oszlop közül választhat, csak egy véletlen részhalmazból (osztályozásnál kb. √54 ≈ 7 oszlopból).

**Jóslás:** mind a 100 fa megmondja a saját véleményét, és a többségi döntés nyer.

**Miért jobb ez általában?** Az egyes fák hibái különbözők és egymástól nagyrészt függetlenek, ezért a szavazásban kioltják egymást. Egy fa tévedhet, 100 fa többsége ritkábban téved. Ezért stabilabb, mint egyetlen fa.

**Miért lett nálunk mégis kicsit rosszabb?** A bootstrap miatt a 22 Background sornak csak egy része jut el egy-egy fához. Ritka osztálynál így minden fa még kevesebb példát lát. A hangolásnál erre való a `class_weight='balanced_subsample'` beállítás, amely minden fa saját mintáján újraszámolja a súlyokat.

**Az ára:** 100 fa döntését nem lehet végigkövetni, ezért a RandomForest kevésbé értelmezhető. Az viszont mérhető, hogy melyik oszlop mennyire fontos neki (ML9).

| | DecisionTree | RandomForest |
|---|---|---|
| Felépítés | 1 fa, minden soron, minden oszlopon | 100 fa, véletlen sorokon és oszlopokon |
| Jóslás | Egy útvonal a gyökértől a levélig | A 100 fa többségi szavazata |
| Értelmezhetőség | Magas, végigkövethető | Közepes, csak a fontosság mérhető |
| Stabilitás | Érzékeny az adat változására | Stabilabb, a hibák kioltják egymást |

## 3. Foldok és keresztvalidáció

A keresztvalidáció kérdése: **hogyan mérjük meg egy modell teljesítményét a teszthalmaz nélkül?** A teszthalmaz zárolva van, azt csak egyszer, a legvégén használjuk. A train-halmazon belül kell tehát „tesztelni”.

A **5-fold keresztvalidáció** a train-halmazt 5 egyforma részre, úgynevezett **foldra** osztja, majd 5 kört futtat:

```
Kör 1:  [VALID] [tanít] [tanít] [tanít] [tanít]
Kör 2:  [tanít] [VALID] [tanít] [tanít] [tanít]
Kör 3:  [tanít] [tanít] [VALID] [tanít] [tanít]
Kör 4:  [tanít] [tanít] [tanít] [VALID] [tanít]
Kör 5:  [tanít] [tanít] [tanít] [tanít] [VALID]
```

- Minden körben a modell 4 folddal tanul (kb. 170 ezer sor), és az ötödiken mérjük (kb. 42 ezer sor), amelyet tanítás közben nem látott.
- **Minden sor pontosan egyszer kerül validálásra**, így az egész train-halmazt felhasználjuk a méréshez.
- Az 5 kör eredményének **átlaga** a becsült teljesítmény, a **szórása** pedig azt mutatja, mennyire stabil a mérés. Ezért szerepel „0,923 ± 0,017”.
- **Rétegzett**, idegen szóval stratified: mind az 5 foldban ugyanaz az osztályarány. A 22 Background sorból így foldonként 4–5 kerül a validációra. Ezért ilyen nagy a szórás: 1 Background sor eltévesztése már a foldban szereplő Background-sorok 20–25%-a.
- **Pipeline-ban:** a medián-imputálás és a skálázás is minden körben újra tanul, csak a 4 tanító foldon. Így a validációs fold információja egyik lépésbe sem szivárog be.

## 4. Precision, recall és F1

Egy osztályra, például a **Background**-ra, nézve három szám van:

- **Precision (pontosság):** amikor a modell azt mondja, hogy „Background”, az esetek hány százalékában igaz? *Mennyire bízhatunk a riasztásában?*
- **Recall (felidézés):** a valódi Background sorok hány százalékát találta meg? *Mennyit vett észre?*
- **F1:** a kettő **harmonikus átlaga**:

$$F1 = 2 \cdot \frac{\text{precision} \cdot \text{recall}}{\text{precision} + \text{recall}}$$

A harmonikus átlag a kisebbik érték felé húz. Ha az egyik nagyon rossz, az F1 is rossz lesz. Egy modell, amely mindenre „Background”-ot mond, 100%-os recallt ér el, de a precisionje közel 0, így az F1-e is közel 0. Csak akkor kap jó F1-et a modell, ha egyszerre pontos és alapos is.

**Példa:** ha a modell 10 sort jelöl Backgroundnak, és ebből 8 helyes (precision = 0,8), a valódi 16 Background sorból pedig 8-at talált meg (recall = 0,5), akkor F1 = 2 · 0,8 · 0,5 / 1,3 ≈ 0,62.

**Macro F1:** mind a 8 osztályra kiszámoljuk az F1-et, és **egyszerű átlagot** veszünk. Így a 22 soros Background ugyanannyit számít, mint a 138 ezer soros DoS.

**Miért nem accuracy?** Az accuracy a helyes jóslatok aránya az összes sorból. Nálunk a DoS a sorok 65%-a, a négy támadásosztály együtt pedig több mint 99%. Egy modell, amely **soha nem ismer fel egyetlen benign forgalmat sem**, így is 99% feletti accuracy-t érne el. A LogisticRegression 90,7%-os accuracy mellett 3 875 támadást benignnek minősített. Az accuracy ezt eltakarja, a macro F1 (0,58) viszont megmutatja.

**Egy mondatban a védésre:** *„5-fold rétegzett keresztvalidációval, macro F1 alapján választottunk modellt, mert a macro F1 minden osztályt egyforma súllyal vesz figyelembe, így a ritka benign osztályokon nyújtott gyenge teljesítményt nem takarhatja el a domináns DoS osztály, ahogy az accuracy esetén megtörténne.”*
