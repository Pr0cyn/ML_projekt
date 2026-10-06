# 02 – Végső eredmények a teszthalmazon: RandomForest (ML8)

A végső Pipeline a teljes train-halmazon tanult (212 230 sor, 2.9 s), majd **egyszer** futott a teszthalmazon (90 956 sor, jóslás 0.17 s). A teszthalmazt ezt megelőzően egyik lépés sem használta.

## 1. Összesített metrikák

| Metrika | Teszt | Train CV (hangolás) |
|---|---|---|
| **Macro F1** | **0.9517** | 0.9254 |
| Balanced accuracy | 0.9544 | – |
| Accuracy | 0.9962 | – |

A tárgy 70%-os accuracy-követelményét a modell teljesíti (99.62%), de ez önmagában nem bizonyító erejű: a teszthalmaz 65%-a DoS, a négy támadásosztály együtt 99% feletti. A fő metrika a macro F1, amely mind a 8 osztályt egyforma súllyal veszi figyelembe.

## 2. Osztályonkénti eredmények (Traffic Type)

| Traffic Type | Tesztsorok | Precision | Recall | F1 |
|---|---|---|---|---|
| DoS | 59367 | 0.999 | 0.998 | 0.998 |
| Mirai | 15569 | 0.990 | 0.993 | 0.992 |
| Bruteforce | 9695 | 0.993 | 0.993 | 0.993 |
| Information Gathering | 5938 | 0.999 | 0.999 | 0.999 |
| Video | 257 | 0.925 | 0.965 | 0.945 |
| Text | 63 | 0.857 | 0.857 | 0.857 |
| Audio | 57 | 0.930 | 0.930 | 0.930 |
| Background | 10 | 0.900 | 0.900 | 0.900 |

![Confusion matrix](confusion_matrix.png)

A cellák a valódi osztály (sor) hány százalékát mutatják az adott jósolt osztályban; az átló a recall.

### A leggyakoribb tévesztések

| Valódi | Jósolt | Sorok |
|---|---|---|
| DoS | Mirai | 99 |
| Mirai | DoS | 61 |
| Bruteforce | Mirai | 46 |
| DoS | Bruteforce | 34 |
| Mirai | Bruteforce | 27 |
| Bruteforce | DoS | 23 |
| Mirai | Video | 8 |
| DoS | Video | 5 |
| Information Gathering | Video | 5 |
| Video | Mirai | 5 |

## 3. Benign vagy Malicious

A jósolt Traffic Type-ból levezetve (Audio, Background, Text, Video → Benign; a többi → Malicious).

| Label | Tesztsorok | Precision | Recall | F1 |
|---|---|---|---|---|
| Benign | 387 | 0.9296 | 0.9561 | 0.9427 |
| Malicious | 90569 | 0.9998 | 0.9997 | 0.9998 |

- Benign flow, amelyet támadásnak minősített (téves riasztás): **17**
- Támadás, amelyet benignnek minősített (kihagyott támadás): **28**

![Confusion matrix (binary)](confusion_matrix_binary.png)
