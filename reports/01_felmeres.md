# 01 – Az adat felmérése (ML2)

- Sorok száma: **8 656 767**
- Oszlopok száma: **86**

## Megállapítások

- **8 656 767 sor, 86 oszlop.** Típusok: VARCHAR: 6, DOUBLE: 78, BIGINT: 1, TIMESTAMP: 1.
- **A célváltozó (Traffic Type) 8 osztályú, és extrém kiegyensúlyozatlan.** A legnagyobb osztály (DoS) 86.53%, a legkisebb (Background) mindössze 32 sor. Benign csak 1 301 sor (0.015%). A Traffic Subtype 32 egyedi értéket vesz fel.
- **Hiányzó (NULL/NaN) és végtelen (±inf) érték nincs az adatban.** Ezt a nyers szövegen is ellenőriztem (3. pont).
- **Negatív értékek:** `Flow IAT Min`: 72 sor (részletek az 5. pontban).

## 1. Oszlopok és típusok

Típusok összesítve: VARCHAR: 6, DOUBLE: 78, BIGINT: 1, TIMESTAMP: 1

| # | Oszlop | Típus |
|---|---|---|
| 1 | Flow ID | VARCHAR |
| 2 | Src IP | VARCHAR |
| 3 | Src Port | DOUBLE |
| 4 | Dst IP | VARCHAR |
| 5 | Dst Port | BIGINT |
| 6 | Protocol | DOUBLE |
| 7 | Timestamp | TIMESTAMP |
| 8 | Flow Duration | DOUBLE |
| 9 | Total Fwd Packet | DOUBLE |
| 10 | Total Bwd packets | DOUBLE |
| 11 | Total Length of Fwd Packet | DOUBLE |
| 12 | Total Length of Bwd Packet | DOUBLE |
| 13 | Fwd Packet Length Max | DOUBLE |
| 14 | Fwd Packet Length Min | DOUBLE |
| 15 | Fwd Packet Length Mean | DOUBLE |
| 16 | Fwd Packet Length Std | DOUBLE |
| 17 | Bwd Packet Length Max | DOUBLE |
| 18 | Bwd Packet Length Min | DOUBLE |
| 19 | Bwd Packet Length Mean | DOUBLE |
| 20 | Bwd Packet Length Std | DOUBLE |
| 21 | Flow Bytes/s | DOUBLE |
| 22 | Flow Packets/s | DOUBLE |
| 23 | Flow IAT Mean | DOUBLE |
| 24 | Flow IAT Std | DOUBLE |
| 25 | Flow IAT Max | DOUBLE |
| 26 | Flow IAT Min | DOUBLE |
| 27 | Fwd IAT Total | DOUBLE |
| 28 | Fwd IAT Mean | DOUBLE |
| 29 | Fwd IAT Std | DOUBLE |
| 30 | Fwd IAT Max | DOUBLE |
| 31 | Fwd IAT Min | DOUBLE |
| 32 | Bwd IAT Total | DOUBLE |
| 33 | Bwd IAT Mean | DOUBLE |
| 34 | Bwd IAT Std | DOUBLE |
| 35 | Bwd IAT Max | DOUBLE |
| 36 | Bwd IAT Min | DOUBLE |
| 37 | Fwd PSH Flags | DOUBLE |
| 38 | Bwd PSH Flags | DOUBLE |
| 39 | Fwd URG Flags | DOUBLE |
| 40 | Bwd URG Flags | DOUBLE |
| 41 | Fwd Header Length | DOUBLE |
| 42 | Bwd Header Length | DOUBLE |
| 43 | Fwd Packets/s | DOUBLE |
| 44 | Bwd Packets/s | DOUBLE |
| 45 | Packet Length Min | DOUBLE |
| 46 | Packet Length Max | DOUBLE |
| 47 | Packet Length Mean | DOUBLE |
| 48 | Packet Length Std | DOUBLE |
| 49 | Packet Length Variance | DOUBLE |
| 50 | FIN Flag Count | DOUBLE |
| 51 | SYN Flag Count | DOUBLE |
| 52 | RST Flag Count | DOUBLE |
| 53 | PSH Flag Count | DOUBLE |
| 54 | ACK Flag Count | DOUBLE |
| 55 | URG Flag Count | DOUBLE |
| 56 | CWR Flag Count | DOUBLE |
| 57 | ECE Flag Count | DOUBLE |
| 58 | Down/Up Ratio | DOUBLE |
| 59 | Average Packet Size | DOUBLE |
| 60 | Fwd Segment Size Avg | DOUBLE |
| 61 | Bwd Segment Size Avg | DOUBLE |
| 62 | Fwd Bytes/Bulk Avg | DOUBLE |
| 63 | Fwd Packet/Bulk Avg | DOUBLE |
| 64 | Fwd Bulk Rate Avg | DOUBLE |
| 65 | Bwd Bytes/Bulk Avg | DOUBLE |
| 66 | Bwd Packet/Bulk Avg | DOUBLE |
| 67 | Bwd Bulk Rate Avg | DOUBLE |
| 68 | Subflow Fwd Packets | DOUBLE |
| 69 | Subflow Fwd Bytes | DOUBLE |
| 70 | Subflow Bwd Packets | DOUBLE |
| 71 | Subflow Bwd Bytes | DOUBLE |
| 72 | FWD Init Win Bytes | DOUBLE |
| 73 | Bwd Init Win Bytes | DOUBLE |
| 74 | Fwd Act Data Pkts | DOUBLE |
| 75 | Fwd Seg Size Min | DOUBLE |
| 76 | Active Mean | DOUBLE |
| 77 | Active Std | DOUBLE |
| 78 | Active Max | DOUBLE |
| 79 | Active Min | DOUBLE |
| 80 | Idle Mean | DOUBLE |
| 81 | Idle Std | DOUBLE |
| 82 | Idle Max | DOUBLE |
| 83 | Idle Min | DOUBLE |
| 84 | Label | VARCHAR |
| 85 | Traffic Type | VARCHAR |
| 86 | Traffic Subtype | VARCHAR |

## 2. A címkék eloszlása

### Label

| Label | Sorok | % |
|---|---|---|
| Malicious | 8 655 466 | 99.98 |
| Benign | 1 301 | 0.02 |

### Traffic Type

| Traffic Type | Sorok | % |
|---|---|---|
| DoS | 7 490 929 | 86.53 |
| Information Gathering | 1 038 363 | 11.99 |
| Mirai | 91 002 | 1.05 |
| Bruteforce | 35 172 | 0.41 |
| Video | 870 | 0.01 |
| Text | 209 | 0.00 |
| Audio | 190 | 0.00 |
| Background | 32 | 0.00 |

### Traffic Subtype (a Traffic Type és a Label szerint)

| Traffic Type | Traffic Subtype | Label | Sorok | % |
|---|---|---|---|---|
| Audio | Audio | Benign | 190 | 0.00 |
| Background | Background | Benign | 32 | 0.00 |
| Bruteforce | Bruteforce DNS | Malicious | 22 179 | 0.26 |
| Bruteforce | Bruteforce Telnet | Malicious | 4 913 | 0.06 |
| Bruteforce | Bruteforce SSH | Malicious | 3 967 | 0.05 |
| Bruteforce | Bruteforce FTP | Malicious | 3 485 | 0.04 |
| Bruteforce | Bruteforce HTTP | Malicious | 628 | 0.01 |
| DoS | DoS RST | Malicious | 1 072 504 | 12.39 |
| DoS | DoS ACK | Malicious | 936 307 | 10.82 |
| DoS | DoS PSH | Malicious | 909 507 | 10.51 |
| DoS | DoS URG | Malicious | 906 190 | 10.47 |
| DoS | DoS CWR | Malicious | 872 523 | 10.08 |
| DoS | DoS ECN | Malicious | 871 150 | 10.06 |
| DoS | DoS SYN | Malicious | 856 764 | 9.90 |
| DoS | DoS FIN | Malicious | 725 600 | 8.38 |
| DoS | DoS UDP | Malicious | 257 994 | 2.98 |
| DoS | DoS HTTP | Malicious | 82 351 | 0.95 |
| DoS | DoS MAC | Malicious | 30 | 0.00 |
| DoS | DoS ICMP | Malicious | 9 | 0.00 |
| Information Gathering | Information Gathering | Malicious | 1 038 363 | 11.99 |
| Mirai | Mirai DDoS DNS | Malicious | 55 196 | 0.64 |
| Mirai | Mirai DDoS SYN | Malicious | 14 210 | 0.16 |
| Mirai | Mirai DDoS HTTP | Malicious | 8 923 | 0.10 |
| Mirai | Mirai Scan Bruteforce | Malicious | 8 731 | 0.10 |
| Mirai | Mirai DDoS ACK | Malicious | 3 779 | 0.04 |
| Mirai | Mirai DDoS UDP | Malicious | 71 | 0.00 |
| Mirai | Mirai DDoS GREIP | Malicious | 49 | 0.00 |
| Mirai | Mirai DDoS GREETH | Malicious | 43 | 0.00 |
| Text | Text | Benign | 209 | 0.00 |
| Video | Video HTTP | Benign | 376 | 0.00 |
| Video | Video RTP | Benign | 349 | 0.00 |
| Video | Video UDP | Benign | 145 | 0.00 |

## 3. Hiányzó és végtelen értékek oszloponként

NULL = üres mező a CSV-ben, NaN = „NaN” érték, +inf / −inf = végtelen. A 86 oszlopból **0** érintett, a többiben egyik sem fordul elő.

Ellenőrzés a nyers CSV szövegén (DuckDB-értelmezés nélkül, soronként): `inf`/`infinity` tokent tartalmazó sor: **0**, `nan` tokent tartalmazó sor: **0**, üres mezőt tartalmazó sor: **0**.

A `Flow Duration` ≤ 0 sorok száma: **0**. Emiatt a /s-alapú oszlopokban (`Flow Bytes/s`, `Flow Packets/s`) nullával osztásból sem keletkezhet végtelen érték.

## 4. Hiányzó és végtelen értékek osztályonként (Traffic Type)

Minden cellában: érintett sorok száma (az osztály hány %-a). Az utolsó oszlop azt mutatja, hány sor esne ki, ha minden olyan sort törölnénk, amelyben bármelyik oszlopban hiány vagy végtelen érték van.

| Traffic Type | Sorok | Bármelyik oszlopban |
|---|---|---|
| DoS | 7 490 929 | 0 (0.00%) |
| Information Gathering | 1 038 363 | 0 (0.00%) |
| Mirai | 91 002 | 0 (0.00%) |
| Bruteforce | 35 172 | 0 (0.00%) |
| Video | 870 | 0 (0.00%) |
| Text | 209 | 0 (0.00%) |
| Audio | 190 | 0 (0.00%) |
| Background | 32 | 0 (0.00%) |

### Alosztályonként (Traffic Subtype), bármelyik oszlopban

| Traffic Type | Traffic Subtype | Sorok | Érintett sorok | % |
|---|---|---|---|---|
| Audio | Audio | 190 | 0 | 0.00 |
| Background | Background | 32 | 0 | 0.00 |
| Bruteforce | Bruteforce DNS | 22 179 | 0 | 0.00 |
| Bruteforce | Bruteforce Telnet | 4 913 | 0 | 0.00 |
| Bruteforce | Bruteforce SSH | 3 967 | 0 | 0.00 |
| Bruteforce | Bruteforce FTP | 3 485 | 0 | 0.00 |
| Bruteforce | Bruteforce HTTP | 628 | 0 | 0.00 |
| DoS | DoS RST | 1 072 504 | 0 | 0.00 |
| DoS | DoS ACK | 936 307 | 0 | 0.00 |
| DoS | DoS PSH | 909 507 | 0 | 0.00 |
| DoS | DoS URG | 906 190 | 0 | 0.00 |
| DoS | DoS CWR | 872 523 | 0 | 0.00 |
| DoS | DoS ECN | 871 150 | 0 | 0.00 |
| DoS | DoS SYN | 856 764 | 0 | 0.00 |
| DoS | DoS FIN | 725 600 | 0 | 0.00 |
| DoS | DoS UDP | 257 994 | 0 | 0.00 |
| DoS | DoS HTTP | 82 351 | 0 | 0.00 |
| DoS | DoS MAC | 30 | 0 | 0.00 |
| DoS | DoS ICMP | 9 | 0 | 0.00 |
| Information Gathering | Information Gathering | 1 038 363 | 0 | 0.00 |
| Mirai | Mirai DDoS DNS | 55 196 | 0 | 0.00 |
| Mirai | Mirai DDoS SYN | 14 210 | 0 | 0.00 |
| Mirai | Mirai DDoS HTTP | 8 923 | 0 | 0.00 |
| Mirai | Mirai Scan Bruteforce | 8 731 | 0 | 0.00 |
| Mirai | Mirai DDoS ACK | 3 779 | 0 | 0.00 |
| Mirai | Mirai DDoS UDP | 71 | 0 | 0.00 |
| Mirai | Mirai DDoS GREIP | 49 | 0 | 0.00 |
| Mirai | Mirai DDoS GREETH | 43 | 0 | 0.00 |
| Text | Text | 209 | 0 | 0.00 |
| Video | Video HTTP | 376 | 0 | 0.00 |
| Video | Video RTP | 349 | 0 | 0.00 |
| Video | Video UDP | 145 | 0 | 0.00 |

## 5. Negatív értékek (rejtett hiányjelzők, pl. −1)

A CICFlowMeter egyes verziói a −1 értékkel jelzik, ha egy mező nem mérhető. Ezért a numerikus oszlopokban a negatív értékeket is megszámoltam.

| Oszlop | Negatív értékű sorok |
|---|---|
| Flow IAT Min | 72 |

`Flow IAT Min` osztályonként:

| Traffic Type | Negatív sorok | % az osztályban | Minimum | Pontosan −1 |
|---|---|---|---|---|
| Audio | 44 | 23.16 | -945.00 | 0 |
| Text | 28 | 13.40 | -176.00 | 0 |
