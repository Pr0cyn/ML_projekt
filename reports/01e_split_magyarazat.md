# 01e – Mintavétel és split: a függvények és paraméterek pontosan (magyarázat)

Az összefoglaló nagy része stimmel, három ponton viszont pontosítani kell.

## 1. A mintavétel: alosztályonként, nem típusonként

Nem Traffic Type-onként vettünk 20 000 sort, hanem **Traffic Subtype-onként legfeljebb 20 000-et**, a benign sorokat pedig mind megtartottuk. Ezért lett a DoS-ból kb. 200 000 sor: 12 alosztálya van, és mindegyikből legfeljebb 20 000 került be. Az Information Gatheringből viszont csak kb. 20 000, mert annak egyetlen alosztálya van.

**A függvény:** ez nem egy kész sklearn-függvény. A szkriptben saját függvény végzi, a `sample_index` (`src/ml3_sample.py`), ami két pandas-műveletre épül:

- **`groupby("Traffic Subtype")`:** alosztályonként csoportosítja a sorokat.
- **`DataFrame.sample(n=20000, random_state=42)`:** egy csoportból véletlenszerűen 20 000 sort választ. Csak akkor fut le, ha a csoport ennél nagyobb, különben az egész csoport bekerül.

A kiválasztott sorokat ezután a DuckDB olvassa ki a Parquet-fájlból, sorszám alapján.

## 2. A `TARGET` nem sklearn-paraméter

Ezért nem található a dokumentációban: a `TARGET = "Traffic Type"` **a mi saját konstansunk** a szkript elején. Csak arra való, hogy az oszlop nevét ne kelljen többször leírni. A valódi sklearn-paraméter ez:

```python
train_test_split(df, test_size=0.30, stratify=df[TARGET], random_state=42)
```

A **`stratify`** paraméter azt mondja meg, melyik oszlop szerint maradjanak meg az arányok. Ha a mintában a Video 0,283%, akkor a trainben és a testben is 0,283% legyen. A függvény ezért nem az egész táblát keveri össze egyben. Osztályonként veszi az egyes osztályok 30%-át a tesztbe, a 70%-át a trainbe.

Maga a split nem tudja, mi a célváltozó. Csak sorokat oszt két részre, a `Traffic Type` oszlop mindkét halmazban ott marad. Hogy a modell ezt tanulja meg, az a későbbi lépésekben dől el, amikor szétválasztjuk a bemenetet (X) és a célt (y).

## 3. A `random_state=42` nem a keverések száma

Az adatot **egyszer** keveri meg. A 42 a véletlenszám-generátor kezdőértéke, angolul *seed*.

- A számítógép „véletlenje” valójában egy determinisztikus számsorozat, amelyet a seed indít el.
- **Ugyanazzal a seeddel mindig pontosan ugyanaz a keverés jön ki.** Ezért futtatható akár holnap, akár egy másik gépen, ugyanaz a 212 230 sor kerül a trainbe. Ezt hívják reprodukálhatóságnak.
- Ha 43-at írnánk, egy másik, de ugyanolyan véletlenszerű felosztást kapnánk. A 42 önmagában semmit nem jelent, csak egy hagyományosan használt szám: a *Galaxis útikalauz stopposoknak* utalása.

Keverés nélkül a fájl elejéből és végéből vágna a függvény. A keverést a `shuffle=True` paraméter kapcsolja be, ez az alapértelmezés. A `random_state` csak azt rögzíti, **melyik** véletlen keverés legyen.

## Összefoglaló

> A 8,66 millió sorból alosztályonként legfeljebb 20 000 véletlen sort vettünk (pandas `sample`, `random_state=42`), a benign sorokat mind megtartottuk, majd kiszűrtük a duplikátumokat. Így 303 186 sor maradt. Ezt az sklearn `train_test_split` függvényével 70/30 arányban bontottuk fel. A `stratify` paraméterrel a Traffic Type osztályarányait mindkét halmazban megtartottuk, a `random_state=42` pedig biztosítja, hogy a véletlen felosztás minden futtatáskor ugyanaz legyen.
