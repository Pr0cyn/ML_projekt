# 01d – Train/test split (ML4)

- Minta: **303 186** sor → train: **212 230** (70.0%), test: **90 956** (30.0%).
- `train_test_split(test_size=0.3, stratify=Traffic Type, random_state=42)`.
- A legnagyobb aránybeli eltérés a mintához képest Traffic Type szerint **0.001** százalékpont, Traffic Subtype szerint 0.145 százalékpont.
- Train és test között közös (jellemzők + címkék szerint azonos) sor: **0**.
- **Innentől a teszthalmaz zárolva van.** Csak egyszer, az ML8 végső kiértékelésénél használjuk.

## Osztályarányok Traffic Type szerint (erre rétegeztünk)

| Osztály | Minta | Train | Test | Minta % | Train % | Test % | Max. eltérés (%-pont) |
|---|---|---|---|---|---|---|---|
| DoS | 197 891 | 138 524 | 59 367 | 65.270 | 65.271 | 65.270 | 0.000 |
| Mirai | 51 897 | 36 328 | 15 569 | 17.117 | 17.117 | 17.117 | 0.000 |
| Bruteforce | 32 315 | 22 620 | 9 695 | 10.658 | 10.658 | 10.659 | 0.001 |
| Information Gathering | 19 794 | 13 856 | 5 938 | 6.529 | 6.529 | 6.528 | 0.000 |
| Video | 858 | 601 | 257 | 0.283 | 0.283 | 0.283 | 0.000 |
| Text | 209 | 146 | 63 | 0.069 | 0.069 | 0.069 | 0.000 |
| Audio | 190 | 133 | 57 | 0.063 | 0.063 | 0.063 | 0.000 |
| Background | 32 | 22 | 10 | 0.011 | 0.010 | 0.011 | 0.000 |

## Ellenőrzés Traffic Subtype szerint (erre nem rétegeztünk)

A rétegzés csak a Traffic Type-ra vonatkozik, az alosztályok aránya a véletlen miatt kicsit jobban ingadozhat. Minden alosztályból jutott sor a tesztbe is.

| Osztály | Minta | Train | Test | Minta % | Train % | Test % | Max. eltérés (%-pont) |
|---|---|---|---|---|---|---|---|
| Mirai DDoS DNS | 19 992 | 14 061 | 5 931 | 6.594 | 6.625 | 6.521 | 0.073 |
| DoS UDP | 19 988 | 14 007 | 5 981 | 6.593 | 6.600 | 6.576 | 0.017 |
| DoS RST | 19 926 | 13 926 | 6 000 | 6.572 | 6.562 | 6.597 | 0.024 |
| DoS FIN | 19 909 | 13 856 | 6 053 | 6.567 | 6.529 | 6.655 | 0.088 |
| DoS PSH | 19 870 | 13 838 | 6 032 | 6.554 | 6.520 | 6.632 | 0.078 |
| DoS ECN | 19 853 | 13 924 | 5 929 | 6.548 | 6.561 | 6.519 | 0.030 |
| DoS ACK | 19 851 | 13 860 | 5 991 | 6.547 | 6.531 | 6.587 | 0.039 |
| DoS SYN | 19 848 | 13 875 | 5 973 | 6.546 | 6.538 | 6.567 | 0.020 |
| DoS CWR | 19 811 | 13 937 | 5 874 | 6.534 | 6.567 | 6.458 | 0.076 |
| DoS URG | 19 810 | 13 999 | 5 811 | 6.534 | 6.596 | 6.389 | 0.145 |
| Information Gathering | 19 794 | 13 856 | 5 938 | 6.529 | 6.529 | 6.528 | 0.000 |
| Bruteforce DNS | 19 406 | 13 633 | 5 773 | 6.401 | 6.424 | 6.347 | 0.054 |
| DoS HTTP | 18 986 | 13 273 | 5 713 | 6.262 | 6.254 | 6.281 | 0.019 |
| Mirai DDoS SYN | 13 926 | 9 674 | 4 252 | 4.593 | 4.558 | 4.675 | 0.082 |
| Mirai DDoS HTTP | 8 219 | 5 763 | 2 456 | 2.711 | 2.715 | 2.700 | 0.011 |
| Mirai Scan Bruteforce | 5 869 | 4 082 | 1 787 | 1.936 | 1.923 | 1.965 | 0.029 |
| Bruteforce Telnet | 4 869 | 3 344 | 1 525 | 1.606 | 1.576 | 1.677 | 0.071 |
| Bruteforce SSH | 3 927 | 2 753 | 1 174 | 1.295 | 1.297 | 1.291 | 0.005 |
| Mirai DDoS ACK | 3 728 | 2 626 | 1 102 | 1.230 | 1.237 | 1.212 | 0.018 |
| Bruteforce FTP | 3 485 | 2 443 | 1 042 | 1.149 | 1.151 | 1.146 | 0.004 |
| Bruteforce HTTP | 628 | 447 | 181 | 0.207 | 0.211 | 0.199 | 0.008 |
| Video HTTP | 364 | 258 | 106 | 0.120 | 0.122 | 0.117 | 0.004 |
| Video RTP | 349 | 247 | 102 | 0.115 | 0.116 | 0.112 | 0.003 |
| Text | 209 | 146 | 63 | 0.069 | 0.069 | 0.069 | 0.000 |
| Audio | 190 | 133 | 57 | 0.063 | 0.063 | 0.063 | 0.000 |
| Video UDP | 145 | 96 | 49 | 0.048 | 0.045 | 0.054 | 0.006 |
| Mirai DDoS UDP | 71 | 51 | 20 | 0.023 | 0.024 | 0.022 | 0.001 |
| Mirai DDoS GREIP | 49 | 39 | 10 | 0.016 | 0.018 | 0.011 | 0.005 |
| Mirai DDoS GREETH | 43 | 32 | 11 | 0.014 | 0.015 | 0.012 | 0.002 |
| Background | 32 | 22 | 10 | 0.011 | 0.010 | 0.011 | 0.000 |
| DoS MAC | 30 | 22 | 8 | 0.010 | 0.010 | 0.009 | 0.001 |
| DoS ICMP | 9 | 7 | 2 | 0.003 | 0.003 | 0.002 | 0.001 |
