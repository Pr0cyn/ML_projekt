# 01c – Mit jelent a 20 000-es mintavétel? (magyarázat)

Igen, jól érted. Egy pontosítással: az ML3 már valódi adatdöntés, mert ott dől el, milyen adaton tanul majd a modell. Csak még nem tanul semmit az adatból.

## Hol tartunk

| Lépés | Mi történt | Tanult-e az adatból? |
|---|---|---|
| ML1 | Környezet és adat előkészítése | Nem |
| ML2 | Felmérés: mi van az adatban, van-e hiány, hogyan oszlanak meg az osztályok | Nem, csak számolás |
| ML3 | A munkaadat elkészítése: mintavétel és duplikátumszűrés | Nem, ezek mechanikus szabályok |
| **ML4-től** | Split, oszlopválasztás, hiányzó adatok kezelése, modell | **Igen, itt kezdődik a gépi tanulás** |

## Mit jelent a 20 000

**Nem 20 000 sor összesen, hanem legfeljebb 20 000 sor alosztályonként.** A 32 Traffic Subtype mindegyikére külön ezt a szabályt alkalmaztuk:

- **Ha egy alosztálynak 20 000-nél több sora van,** véletlenszerűen kiválasztunk belőle 20 000-et, a többit nem használjuk.
  - Példa: a DoS RST 1 072 504 sorából 20 000 került a mintába.
- **Ha kevesebb van,** mind bekerül.
  - Példa: a Bruteforce HTTP mind a 628 sora, a DoS ICMP mind a 9 sora.
- **A benign sorok mind bekerülnek,** mind az 1301.

Ebből lett **310 139 sor**, a duplikátumszűrés után pedig **303 186**. A 8,66 millió sorból kb. 3,5%-ot tartottunk meg.

## Miért van erre szükség

1. **A DoS elnyomná a többi osztályt.** A teljes adat 86,5%-a DoS. Ha mindent megtartanánk, a modell szinte csak DoS-t látna, és az 1301 benign sor elveszne a tömegben.
2. **A nagy osztályok nagyon ismétlődőek.** Csak a DoS-ban 1,1 millió jellemző szerint azonos sor van. A millió sor nem hordoz milliónyi új információt, a 20 000 véletlen sor jól lefedi ugyanazt.
3. **Gyorsaság.** 303 ezer soron az 5-fold keresztvalidáció percek alatt lefut, 8,6 millión órákig tartana.
4. **Minden támadásváltozat bekerül.** Az alosztályonkénti szabály miatt a ritka változatok, például a DoS ICMP, sem vesznek el, ahogy az előző válaszban láttuk.

## Miért pont 20 000, és miért nem 10 000 vagy 50 000

Ez mérlegelés, nincs egyetlen helyes szám. A riport táblázata megmutatja, mi történne más értékeknél:

- **10 000-nél** kb. 176 ezer sor lenne a minta. Ez is működne, csak a nagy osztályokból kevesebb példa jutna.
- **50 000-nél** kb. 672 ezer sor lenne. Ez lassabb, és csak a DoS és az Information Gathering nőne, a ritka osztályok nem, így az aránytalanság romlana.
- **A 20 000 a kettő közötti egyensúly:** elég példa a nagy osztályokból, de gyors marad.

**Egy mondatban a védésre:** *„Alosztályonként legfeljebb 20 000 véletlen sort vettünk, így a domináns DoS nem nyomta el a ritka osztályokat, minden támadásváltozat bekerült, és a modellválasztás gyorsan lefuthatott.”*
