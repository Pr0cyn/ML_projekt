# 01 – Hiperparaméter-hangolás: RandomForest

GridSearchCV a **train-halmazon** (212 230 sor)  5-fold rétegzett keresztvalidációval, ugyanazokon a foldokon, mint az ML7, macro F1 alapján. 12 kombináció × 5 fold = 60 tanítás, összesen 133 másodperc. A teszthalmazt nem érintettem.

## A rács

- `class_weight`: balanced, balanced_subsample
- `min_samples_leaf`: 1, 2, 5
- `max_features`: sqrt, 0.3

## Kiválasztási szabály

**Legjobb átlagos macro F1.** A RandomForestnél a rács elemei (`class_weight`, `min_samples_leaf`, `max_features`) az értelmezhetőséget nem változtatják érdemben, mert száz fa szavazata így is, úgy is fekete doboz. Ezért itt nincs „egyszerűbb” jelölt, amelyet a zajon belül előnyben kellene részesíteni. `class_weight='balanced_subsample'`: a súlyokat minden fa a saját bootstrap-mintáján számolja újra. `max_features`: kérdésenként hány oszlop közül választhat a fa (sqrt ≈ 7, 0.3 ≈ 16).

## Eredmény

|  | Beállítás | Macro F1 (CV) | Szórás |
|---|---|---|---|
| Alapbeállítás (ML7) | sklearn alapértékek, class_weight=balanced | 0.9120* | – |
| Legjobb CV-átlag | class_weight=balanced_subsample, max_features=sqrt, min_samples_leaf=2 | 0.9254 | 0.0223 |
| **Választott** | **class_weight=balanced_subsample, max_features=sqrt, min_samples_leaf=2** | **0.9254** | 0.0223 |

\* Az alapbeállítás értéke itt az összesített keresztvalidált jóslatokon számolt macro F1, ezért kicsit eltérhet az ML7 foldonkénti átlagától.

A választott modell a teljes train-halmazon újratanítva: 100 fa, összesen 200 574 csomópont, legmélyebb fa: 41.

## F1 osztályonként: alapbeállítás vs. hangolt (keresztvalidált jóslatok)

| Traffic Type | Sorok (train) | Alapbeállítás | Hangolt | Változás |
|---|---|---|---|---|
| DoS | 138524 | 0.997 | 0.998 | +0.000 |
| Mirai | 36328 | 0.988 | 0.990 | +0.002 |
| Bruteforce | 22620 | 0.992 | 0.994 | +0.001 |
| Information Gathering | 13856 | 0.999 | 0.999 | -0.000 |
| Video | 601 | 0.927 | 0.932 | +0.005 |
| Text | 146 | 0.879 | 0.884 | +0.005 |
| Audio | 133 | 0.895 | 0.891 | -0.004 |
| Background | 22 | 0.619 | 0.714 | +0.095 |

## Minden kombináció (rangsor szerint)

| Rang | Beállítás | Macro F1 | Szórás | Tanítás / fold |
|---|---|---|---|---|
| 1 | class_weight=balanced_subsample, max_features=sqrt, min_samples_leaf=2 | 0.9254 | 0.0223 | 36.2 s |
| 2 | class_weight=balanced_subsample, max_features=sqrt, min_samples_leaf=1 | 0.9229 | 0.0159 | 36.1 s |
| 3 | class_weight=balanced_subsample, max_features=0.3, min_samples_leaf=2 | 0.9216 | 0.0206 | 47.2 s |
| 4 | class_weight=balanced_subsample, max_features=0.3, min_samples_leaf=1 | 0.9212 | 0.0176 | 51.7 s |
| 5 | class_weight=balanced, max_features=0.3, min_samples_leaf=1 | 0.9160 | 0.0350 | 36.9 s |
| 6 | class_weight=balanced, max_features=sqrt, min_samples_leaf=1 | 0.9120 | 0.0183 | 22.2 s |
| 7 | class_weight=balanced, max_features=0.3, min_samples_leaf=2 | 0.9048 | 0.0258 | 35.3 s |
| 8 | class_weight=balanced_subsample, max_features=0.3, min_samples_leaf=5 | 0.8974 | 0.0252 | 45.7 s |
| 9 | class_weight=balanced, max_features=sqrt, min_samples_leaf=2 | 0.8947 | 0.0252 | 22.1 s |
| 10 | class_weight=balanced_subsample, max_features=sqrt, min_samples_leaf=5 | 0.8912 | 0.0323 | 33.9 s |
| 11 | class_weight=balanced, max_features=0.3, min_samples_leaf=5 | 0.8675 | 0.0255 | 35.4 s |
| 12 | class_weight=balanced, max_features=sqrt, min_samples_leaf=5 | 0.8532 | 0.0218 | 21.6 s |
