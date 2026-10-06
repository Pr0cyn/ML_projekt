# 03 – Hiányzó adatok (ML6, döntési pont)

Minden mérés a **train-halmazon** (212 230 sor) és az ML5-ben kiválasztott **54 oszlopon** készült.

## 1. NaN és végtelen értékek

Az első lépés minden opciónál ugyanaz: a +inf és −inf értékeket NaN-ná alakítjuk (`inf_to_nan`), mert a scikit-learn modellek végtelen értékre hibát dobnak.

| Mérés | Érték |
|---|---|
| NaN cellák | 0 |
| +inf cellák | 0 |
| −inf cellák | 0 |
| Érintett sorok | 0 |
| Érintett oszlopok | 0 |

**A train-halmazban nincs hiányzó és végtelen érték** (összesen 0 érintett cella). Ez egyezik az ML2-vel, ahol a teljes 8,66 millió sort és a nyers CSV-szöveget is ellenőriztem.

## 2. A három opció, és mit érintene

| Opció | Mit csinál | Érintett sorok / osztály most | Előny | Hátrány |
|---|---|---|---|---|
| Sorok törlése | a hiányos sort eldobjuk | 0 sor, egyik osztály sem | egyszerű, nem talál ki értéket | éles használatban egy flow-t nem lehet „kihagyni”, azt is osztályozni kell; ha a hiány egy osztályhoz kötődik, azt az osztályt tizedeli meg; a Pipeline nem tud sort törölni |
| Medián-imputálás | a hiányzó értéket a train-medián pótolja (`SimpleImputer`) | 0 sor, egyik osztály sem | minden sor megmarad; a medián robusztus a kiugró értékekre (a flow-adatok erősen ferdék) | elfedi, hogy az érték hiányzott |
| Medián + hiányjelző | mint előbb, és egy 0/1 oszlop jelzi, hol volt hiány (`add_indicator=True`) | 0 sor, egyik osztály sem | ha a hiány maga is információ, a modell látja | csak azokhoz az oszlopokhoz készül jelző, ahol a train-ben volt hiány; itt egyikben sem, így most nem ad hozzá semmit |

Mivel most semmi nem hiányzik, ezen az adaton a három opció **ugyanazt az eredményt adja**. A választás arról szól, mi történjen egy új adaton, ahol már előfordulhat hiány vagy végtelen érték (pl. 0 hosszú flow → nullával osztás a /s oszlopokban).

## 3. Az egyetlen anomália: negatív `Flow IAT Min`

A `Flow IAT Min` a flow két egymást követő csomagja közötti legrövidebb idő. Fizikailag nem lehet negatív, ezért ez valószínűleg időbélyeg-hiba a felvételben (a csomagok nem időrendben érkeztek). A negatív értékek csak két benign osztályban fordulnak elő:

| Traffic Type | Sorok (train) | Negatív | Az osztály %-a | Minimum |
|---|---|---|---|---|
| DoS | 138524 | 0 | 0.0% | – |
| Mirai | 36328 | 0 | 0.0% | – |
| Bruteforce | 22620 | 0 | 0.0% | – |
| Information Gathering | 13856 | 0 | 0.0% | – |
| Video | 601 | 0 | 0.0% | – |
| Text | 146 | 20 | 13.7% | -176 |
| Audio | 133 | 31 | 23.3% | -945 |
| Background | 22 | 0 | 0.0% | – |

**Ha ezeket a sorokat törölnénk, az Audio osztály kb. negyede és a Text osztály kb. hetede elveszne.** Ez pontosan az a helyzet, amire a feladat figyelmeztetett: a hiány (itt: a hibás érték) egy osztályhoz kötődik, így a sorok törlése megtizedelné azt az osztályt.

A három kezelési mód 5-fold rétegzett keresztvalidációval, Pipeline-on belül (az imputálás foldonként csak a tanító részen illeszkedik), RandomForest modellel (100 fa, `class_weight='balanced'`). Az Audio és Text oszlop az adott osztály F1-értéke a keresztvalidált jóslatokon:

| Változat | Kezelés | Macro F1 (átlag ± szórás) | F1 Audio | F1 Text | Idő |
|---|---|---|---|---|---|
| 1 | A negatív érték marad (valós mért értékként kezeljük) | 0.9120 ± 0.0183 | 0.895 | 0.879 | 18 s |
| 2 | Negatív → NaN, medián-imputálás | 0.9117 ± 0.0184 | 0.891 | 0.879 | 19 s |
| 3 | Negatív → NaN, medián-imputálás + hiányjelző oszlop | 0.9142 ± 0.0229 | 0.894 | 0.882 | 19 s |
