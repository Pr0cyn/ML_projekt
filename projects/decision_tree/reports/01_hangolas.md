# 01 – Hiperparaméter-hangolás: DecisionTree

GridSearchCV a **train-halmazon** (212 230 sor), 5-fold rétegzett keresztvalidációval, ugyanazokon a foldokon, mint az ML7, macro F1 alapján. 28 kombináció × 5 fold = 140 tanítás, összesen 42 másodperc. A teszthalmazt nem érintettem.

## A rács

- `max_depth`: None, 25, 20, 15, 12, 10, 8
- `min_samples_leaf`: 1, 2, 5, 10

## Kiválasztási szabály

**Egy standard hiba szabály:** megkeresem a legjobb átlagos macro F1-et, és az összes olyan kombinációt, amelynek átlaga ettől legfeljebb egy standard hibával marad el (standard hiba = a legjobb kombináció foldonkénti szórása / √5). Ezek közül a **legegyszerűbb fát** választom: előbb a legkisebb `max_depth`, azonos mélységnél a legnagyobb `min_samples_leaf`. Indok: a zajon belüli különbség nem valódi különbség, a kisebb fa viszont kevésbé tanul túl, és jobban magyarázható.

## Eredmény

|  | Beállítás | Macro F1 (CV) | Szórás |
|---|---|---|---|
| Alapbeállítás (ML7) | sklearn alapértékek, class_weight=balanced | 0.9212* | – |
| Legjobb CV-átlag | max_depth=20, min_samples_leaf=1 | 0.9233 | 0.0179 |
| **Választott** | **max_depth=20, min_samples_leaf=1** | **0.9233** | 0.0179 |

\* Az alapbeállítás értéke itt az összesített keresztvalidált jóslatokon számolt macro F1, ezért kicsit eltérhet az ML7 foldonkénti átlagától.

A választott modell a teljes train-halmazon újratanítva: mélység 20, 965 levél.

## F1 osztályonként: alapbeállítás vs. hangolt (keresztvalidált jóslatok)

| Traffic Type | Sorok (train) | Alapbeállítás | Hangolt | Változás |
|---|---|---|---|---|
| DoS | 138524 | 0.998 | 0.998 | -0.000 |
| Mirai | 36328 | 0.990 | 0.989 | -0.000 |
| Bruteforce | 22620 | 0.994 | 0.994 | +0.000 |
| Information Gathering | 13856 | 0.999 | 0.999 | +0.000 |
| Video | 601 | 0.936 | 0.936 | -0.000 |
| Text | 146 | 0.856 | 0.860 | +0.004 |
| Audio | 133 | 0.902 | 0.902 | +0.000 |
| Background | 22 | 0.696 | 0.696 | +0.000 |

## Minden kombináció (rangsor szerint)

| Rang | Beállítás | Macro F1 | Szórás | Tanítás / fold |
|---|---|---|---|---|
| 1 | max_depth=20, min_samples_leaf=1 | 0.9233 | 0.0179 | 5.2 s |
| 2 | max_depth=None, min_samples_leaf=1 | 0.9229 | 0.0171 | 5.5 s |
| 3 | max_depth=25, min_samples_leaf=1 | 0.9212 | 0.0175 | 5.0 s |
| 4 | max_depth=None, min_samples_leaf=2 | 0.9136 | 0.0183 | 5.4 s |
| 5 | max_depth=20, min_samples_leaf=2 | 0.9134 | 0.0197 | 5.1 s |
| 6 | max_depth=25, min_samples_leaf=2 | 0.9129 | 0.0190 | 5.5 s |
| 7 | max_depth=15, min_samples_leaf=1 | 0.9100 | 0.0289 | 5.3 s |
| 8 | max_depth=15, min_samples_leaf=2 | 0.9083 | 0.0286 | 5.1 s |
| 9 | max_depth=12, min_samples_leaf=1 | 0.8837 | 0.0518 | 5.4 s |
| 10 | max_depth=20, min_samples_leaf=5 | 0.8804 | 0.0189 | 5.3 s |
| 11 | max_depth=12, min_samples_leaf=2 | 0.8796 | 0.0497 | 5.3 s |
| 12 | max_depth=None, min_samples_leaf=5 | 0.8789 | 0.0184 | 5.7 s |
| 13 | max_depth=25, min_samples_leaf=5 | 0.8783 | 0.0189 | 5.5 s |
| 14 | max_depth=15, min_samples_leaf=5 | 0.8764 | 0.0248 | 5.0 s |
| 15 | max_depth=12, min_samples_leaf=5 | 0.8521 | 0.0457 | 5.0 s |
| 16 | max_depth=20, min_samples_leaf=10 | 0.8332 | 0.0273 | 5.6 s |
| 17 | max_depth=None, min_samples_leaf=10 | 0.8330 | 0.0276 | 5.3 s |
| 18 | max_depth=25, min_samples_leaf=10 | 0.8330 | 0.0275 | 5.4 s |
| 19 | max_depth=15, min_samples_leaf=10 | 0.8318 | 0.0298 | 5.2 s |
| 20 | max_depth=12, min_samples_leaf=10 | 0.8121 | 0.0473 | 5.1 s |
| 21 | max_depth=10, min_samples_leaf=1 | 0.8029 | 0.0515 | 5.2 s |
| 22 | max_depth=10, min_samples_leaf=2 | 0.8027 | 0.0492 | 5.2 s |
| 23 | max_depth=10, min_samples_leaf=5 | 0.7902 | 0.0489 | 5.2 s |
| 24 | max_depth=10, min_samples_leaf=10 | 0.7662 | 0.0533 | 5.3 s |
| 25 | max_depth=8, min_samples_leaf=10 | 0.7236 | 0.0310 | 2.8 s |
| 26 | max_depth=8, min_samples_leaf=1 | 0.7128 | 0.0108 | 4.6 s |
| 27 | max_depth=8, min_samples_leaf=5 | 0.7127 | 0.0156 | 3.5 s |
| 28 | max_depth=8, min_samples_leaf=2 | 0.7120 | 0.0098 | 4.0 s |
