# 01b – Rétegzett minta és duplikátumszűrés (ML3)

## 1. Az N megválasztása

A minta az összes benign sorból és Traffic Subtype-onként legfeljebb N véletlenszerűen választott malicious sorból áll (`random_state=42`). Ha egy alosztálynak N-nél kevesebb sora van, mind bekerül. A táblázat a minta méretét mutatja Traffic Type szerint a duplikátumszűrés előtt, néhány lehetséges N-re.

| Traffic Type | Teljes adat | N = 10 000 | N = 20 000 | N = 50 000 | N = 100 000 |
|---|---|---|---|---|---|
| DoS | 7 490 929 | 100 039 | 200 039 | 500 039 | 982 390 |
| Information Gathering | 1 038 363 | 10 000 | 20 000 | 50 000 | 100 000 |
| Mirai | 91 002 | 41 596 | 55 806 | 85 806 | 91 002 |
| Bruteforce | 35 172 | 22 993 | 32 993 | 35 172 | 35 172 |
| Video | 870 | 870 | 870 | 870 | 870 |
| Text | 209 | 209 | 209 | 209 | 209 |
| Audio | 190 | 190 | 190 | 190 | 190 |
| Background | 32 | 32 | 32 | 32 | 32 |
| **Összesen** | 8 656 767 | 175 929 | 310 139 | 672 318 | 1 209 865 |

**Választott: N = 20 000**. Indokok:
- A 32 Traffic Subtype közül 13 alosztálynak van N-nél több sora. A többi 19 teljes egészében bekerül, köztük a DoS ICMP (9), a DoS MAC (30), a Mirai GREETH (43) és mind a 6 benign alosztály.
- A kb. 310 ezer soros minta 77 jellemzővel elég ahhoz, hogy a legnagyobb osztályokat is jól lefedje. Ugyanakkor elég kicsi ahhoz, hogy az 5-fold keresztvalidáció a lassabb modellekkel (LogisticRegression, RandomForest) is percek alatt lefusson.
- Nagyobb N főleg a DoS-t és az Information Gatheringet növelné. A ritka osztályok mérete nem változna, így a kiegyensúlyozatlanság csak romlana.
- Mellékhatás: az alosztályonkénti plafon miatt a mintában a Traffic Type arányok eltérnek a teljes adatétól. A DoS (12 alosztály) aránya 64.5%, az egyetlen alosztályú Information Gatheringé 6.4% (a duplikátumszűrés előtt). Ez szándékos, mert így a ritkább osztályok nagyobb súlyt kapnak.

## 2. Pontos duplikátumok

Mintavétel után: **310 139** sor.

| Duplikátum-kulcs | Duplikátum sorok a mintában |
|---|---|
| mind a 86 oszlop | 1 136 |
| 77 jellemző + 3 címke (azonosító oszlopok nélkül) | 6 953 |

**A szűrés kulcsa: a 77 jellemző és a 3 címke, a 6 azonosító oszlop (Flow ID, Src/Dst IP, Src/Dst Port, Timestamp) nélkül.** A teljes sorra nézve gyakorlatilag nincs duplikátum, mert a Flow ID és a Timestamp minden sorban más. Ezek az oszlopok viszont nem kerülnek a modellbe (ML5, azonosító kategória). A modell szemszögéből ezért két sor akkor azonos, ha a jellemzőik megegyeznek. Ha az ilyen sorok bennmaradnának, ugyanaz a jellemzővektor a train- és a teszthalmazba is bekerülhetne, ami túl optimista teszteredményt adna. A megtartott sor mindig az eredeti fájlban előbb szereplő.

### Alosztályonként

| Traffic Type | Traffic Subtype | Minta | Törölt duplikátum | Marad |
|---|---|---|---|---|
| Audio | Audio | 190 | 0 | 190 |
| Background | Background | 32 | 0 | 32 |
| Bruteforce | Bruteforce DNS | 20 000 | 594 | 19 406 |
| Bruteforce | Bruteforce FTP | 3 485 | 0 | 3 485 |
| Bruteforce | Bruteforce HTTP | 628 | 0 | 628 |
| Bruteforce | Bruteforce SSH | 3 967 | 40 | 3 927 |
| Bruteforce | Bruteforce Telnet | 4 913 | 44 | 4 869 |
| DoS | DoS ACK | 20 000 | 149 | 19 851 |
| DoS | DoS CWR | 20 000 | 189 | 19 811 |
| DoS | DoS ECN | 20 000 | 147 | 19 853 |
| DoS | DoS FIN | 20 000 | 91 | 19 909 |
| DoS | DoS HTTP | 20 000 | 1 014 | 18 986 |
| DoS | DoS ICMP | 9 | 0 | 9 |
| DoS | DoS MAC | 30 | 0 | 30 |
| DoS | DoS PSH | 20 000 | 130 | 19 870 |
| DoS | DoS RST | 20 000 | 74 | 19 926 |
| DoS | DoS SYN | 20 000 | 152 | 19 848 |
| DoS | DoS UDP | 20 000 | 12 | 19 988 |
| DoS | DoS URG | 20 000 | 190 | 19 810 |
| Information Gathering | Information Gathering | 20 000 | 206 | 19 794 |
| Mirai | Mirai DDoS ACK | 3 779 | 51 | 3 728 |
| Mirai | Mirai DDoS DNS | 20 000 | 8 | 19 992 |
| Mirai | Mirai DDoS GREETH | 43 | 0 | 43 |
| Mirai | Mirai DDoS GREIP | 49 | 0 | 49 |
| Mirai | Mirai DDoS HTTP | 8 923 | 704 | 8 219 |
| Mirai | Mirai DDoS SYN | 14 210 | 284 | 13 926 |
| Mirai | Mirai DDoS UDP | 71 | 0 | 71 |
| Mirai | Mirai Scan Bruteforce | 8 731 | 2 862 | 5 869 |
| Text | Text | 209 | 0 | 209 |
| Video | Video HTTP | 376 | 12 | 364 |
| Video | Video RTP | 349 | 0 | 349 |
| Video | Video UDP | 145 | 0 | 145 |

### A végleges minta Traffic Type szerint

| Traffic Type | Sorok | % |
|---|---|---|
| DoS | 197 891 | 65.27 |
| Mirai | 51 897 | 17.12 |
| Bruteforce | 32 315 | 10.66 |
| Information Gathering | 19 794 | 6.53 |
| Video | 858 | 0.28 |
| Text | 209 | 0.07 |
| Audio | 190 | 0.06 |
| Background | 32 | 0.01 |

Végleges minta: **303 186** sor, 86 oszlop → `data/processed/sample.parquet`.

## 3. Ütköző címkék

A szűrés után **171** sor olyan, hogy ugyanaz a jellemzővektor egynél több Traffic Type címkével is előfordul. Ezeket a sorokat egyetlen modell sem tudja mind helyesen osztályozni. Nem töröltem őket, mert valós mérésekből származnak, csak jelzem a létezésüket (a teljes adatban 118 ilyen jellemzővektor van, 4 762 sorban).
