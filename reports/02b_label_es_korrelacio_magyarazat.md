# 02b – Label és korreláló párok (magyarázat)

## 1. A Label megmarad, csak nem bemenetként

A Label-t nem töröljük az adatból. Csak abból a listából hagyjuk ki, amit a modell **bemenetként** lát. Különbség van aközött, ami a modellbe bemegy (X), és ami kijön belőle (y):

- **Bemenet (X):** a flow mért tulajdonságai, például a csomagméretek és az időzítések. Ezek egy új, ismeretlen forgalomnál is rendelkezésre állnak.
- **Kimenet (y):** amit meg akarunk tudni, vagyis a Traffic Type.

Ha a Label bemenet lenne, a modellnek megmondanánk, hogy a sor kártékony-e, holott épp ezt kellene kitalálnia. Egy éles hálózaton egy új flow mellett nincs ott a „Malicious” felirat.

**Hogyan mondja meg a modell mégis, hogy jó- vagy rosszindulatú-e a forgalom?** A Traffic Type-ból ez egyértelműen következik. Az ML5 mérése szerint minden Traffic Type-hoz pontosan egy Label tartozik:

| Traffic Type (a modell ezt jósolja) | → Label (ebből következik) |
|---|---|
| Audio, Background, Text, Video | Benign |
| DoS, Information Gathering, Mirai, Bruteforce | Malicious |

A modell tehát a 8 osztály egyikét jósolja, és ebből egy egyszerű táblázat megadja a Label-t. Ez a **hierarchikus osztályozás**: ha a modell tudja, hogy DoS, akkor azt is tudja, hogy kártékony.

Az ML8-ban ezért **mindkét szinten kiértékelünk**:
- 8 osztályos eredmény: accuracy, macro F1 és confusion matrix a Traffic Type-ra;
- kétosztályos eredmény: benign vagy malicious. Ehhez a valódi és a jósolt típust is átalakítjuk Label-lé, és arra is kiszámoljuk a metrikákat és a 2×2-es confusion matrixot.

Ez külön modell nélkül megoldható. Ráadásul a két szint sosem mond ellent egymásnak, ami két külön modellnél előfordulhatna.

## 2. Miért szűrjük a korreláló párokat?

Itt egy apró félreértés lehet a háttérben: **nem szükségünk van** a korreláló párokra, hanem **megszabadulunk** tőlük. A modell valóban a jellemzőkből tanul, és ez elég. A kérdés csak az, hogy ugyanazt a jellemzőt kétszer is odaadjuk-e neki.

**Mit jelent a korreláció?** Az r szám −1 és +1 között azt méri, mennyire mozog együtt két oszlop. Az |r| = 1 azt jelenti, hogy az egyikből pontosan kiszámolható a másik.

**Példa az adatból:** az `Fwd Packet Length Mean` és az `Fwd Segment Size Avg` korrelációja r = 1,000. A CICFlowMeter ugyanazt az átlagot két néven írja ki. A második oszlop **semmi új információt nem ad**, csak ismétlés.

**Miért érdemes kiszűrni az ilyen ismétléseket, ha a pontosságot alig befolyásolják?**

1. **Magyarázhatóság:** a védésen könnyebb 54 oszlopot megindokolni, mint 72-t, amiből 18 másolat.
2. **Lineáris modell (ML7):** ha két oszlop ugyanaz, a LogisticRegression tetszőlegesen oszthatja el köztük a súlyt. Az együtthatók instabillá és értelmezhetetlenné válnak, ezt hívják **multikollinearitásnak**.
3. **Feature importance (ML9):** ha egy fontos jellemző kétszer szerepel, a fontossága megoszlik a két példány között. Így mindkettő kevésbé fontosnak látszik, mint amilyen valójában.
4. **Futási idő:** kevesebb oszlop gyorsabb tanítást jelent. Ennél az adatméretnél ez elhanyagolható.

**Amit a mérés mutat:** a döntési fák (RandomForest) pontosságát az ismétlés alig zavarja. Ezért van az A (72 oszlop) és a B (54 oszlop) eredménye egy szóráson belül. A korrelációs szűrés tehát **nem a pontosságért** van, hanem az egyszerűségért, a magyarázhatóságért és a lineáris modell miatt. Ezért döntési pont: el is hagyhatnánk, csak akkor a fenti előnyök elvesznek.

**Egy mondatban a védésre:** *„A korreláló párok egyik tagját azért hagytuk el, mert a második oszlop ugyanazt mérte (|r| > 0,95), így új információt nem adott, viszont nehezebben értelmezhetővé tette volna a modellt. A mérés szerint ez a pontosságon nem rontott.”*
