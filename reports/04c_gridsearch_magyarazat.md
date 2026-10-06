# 04c – Mi a GridSearchCV, és miért használjuk? (magyarázat)

## Paraméter és hiperparaméter

- **Paraméter:** amit a modell maga tanul meg az adatból. A döntési fánál ilyenek a kérdések és a küszöbök (például „Average Packet Size ≤ 60?”).
- **Hiperparaméter:** amit **mi állítunk be a tanítás előtt**, és ami meghatározza, *hogyan* tanuljon a modell. Például:
  - `max_depth`: legfeljebb hány kérdés mélységig mehet a fa;
  - `min_samples_leaf`: legalább hány sor kell egy levélbe. Ha ez 5, a fa nem hozhat létre olyan levelet, ami egyetlen sorra „emlékszik”;
  - `class_weight`: hogyan súlyozza a ritka osztályokat.

Eddig minden modell az sklearn alapbeállításaival futott. Ezek általános célú értékek, nem a mi adatunkra szabottak.

## Mit csinál a GridSearchCV?

A neve két részből áll:
- **Grid (rács):** megadunk néhány értéket minden hiperparaméterre, és a függvény **minden kombinációt** kipróbál.
- **CV:** minden kombinációt **5-fold keresztvalidációval** mér, ugyanúgy, ahogy az ML7-ben a modelleket.

Példa a döntési fára:

| | `min_samples_leaf` = 1 | = 2 | = 5 | = 10 |
|---|---|---|---|---|
| `max_depth` = nincs korlát | 0,923 | ? | ? | ? |
| = 20 | ? | ? | ? | ? |
| = 15 | ? | ? | ? | ? |
| = 10 | ? | ? | ? | ? |

Ez 16 kombináció × 5 fold = **80 tanítás**. A bal felső cella a mostani alapbeállítás, a 0,923-at már ismerjük. A végén a legjobb átlagos macro F1-et elérő kombináció nyer, és a GridSearchCV ezzel automatikusan újratanítja a modellt a teljes train-halmazon.

## Miért hasznos nálunk?

1. **A DecisionTree túltanul.** A 31-es mélység és a 926 levél azt jelzi, hogy a fa egyedi sorokat is megjegyzett. Ha kiderül, hogy például egy 12 mély fa ugyanolyan jó, az **kisebb, általánosabb és sokkal jobban magyarázható** modell. A védésen az is erős érv, hogy „mértük, és a kisebb fa nem rosszabb”.
2. **A RandomForest ritka osztályainak segíthet.** A `class_weight='balanced_subsample'` minden fa saját mintáján számolja újra a súlyokat. Ez épp a Background osztály gyengeségére válasz lehet (alapbeállításban 0,62-es F1).
3. **Igazságosabb összehasonlítás.** Ha a két projektet a végén összevetjük, mindkét modell a saját legjobb formájában szerepeljen, ne alapbeállításban.

## Mennyire bonyolult megmagyarázni?

**Nem bonyolult.** Lényegében ennyi: *„A modell beállításainak néhány lehetséges értékét szisztematikusan, minden kombinációban kipróbáltuk, mindegyiket 5-fold keresztvalidációval mértük a train-halmazon, és a legjobb macro F1-et adó beállítást választottuk.”*

Két finomság, amire a védésen rákérdezhetnek:

- **„Nem túl optimista a legjobb CV-eredmény?”** De, kicsit az. Ha sok kombináció közül a legjobbat választjuk, az részben szerencse is lehet. **Ezért van a zárolt teszthalmaz**: az ad tisztességes, független becslést.
- **„Miért nem a legjobb, hanem egy egyszerűbb fa?”** Ha több beállítás eredménye is a zajon belül van, a **legegyszerűbbet** választjuk: ez az **„egy standard hiba” szabály**. Így a DT valószínűleg kisebb és jobban megvédhető lesz.

## A két külön projekt

Az ML1–ML7 közös marad (adat, split, oszlopok, hiányzó adatok, keresztvalidáció), mert ezek mindkét modellre ugyanazok. Innen ágazik szét a két projekt, saját mappában:

```
projects/
├── decision_tree/     ← GridSearchCV → végső tanítás → teszt → permutation importance → mentett Pipeline
└── random_forest/     ← ugyanez RandomForesttel
reports/06_osszehasonlitas.md   ← a legvégén: a két projekt eredménye egymás mellett
```

A tesztre vonatkozó szabály így is érvényes marad. Mindkét projekt egyszer, a saját végső modelljével fut a teszthalmazon, a hangolás pedig kizárólag a train-halmazon történik. A végső összehasonlítás beszámol a két eredményről, a teszteredmény alapján nem hangolunk utólag.
