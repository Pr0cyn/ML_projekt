# 02 – Oszlopválasztás (ML5, döntési pont)

Minden mérés a **train-halmazon** (212 230 sor) készült, a teszthalmazt nem érintettem.

## Összefoglalás

- Kiinduló oszlopok: 86 (ebből 1 célváltozó).
- Kimarad – erősen korreláló pár: **18**
- Kimarad – azonosító / hálózati cím: **6**
- Kimarad – konstans: **5**
- Kimarad – címkeoszlop: **2**
- **Marad (javasolt B opció): 54 jellemző.**

## 1. Azonosítók és hálózati címek

A **tisztaság** azt mutatja, hogy a sorok hány százalékában egyezik a sor osztálya az oszlop adott értékénél leggyakoribb osztállyal. 100% esetén az oszlop értéke önmagában megmondja az osztályt.

- A `Flow ID` a sorok 65%-ában egyedi, ezért a magas tisztaság itt azt jelenti, hogy a modell egyedi kapcsolatokat magolna be, ami új adatra nem visz át. A `Timestamp` másodperces felbontású, és a felvételek időpontját kódolja (lásd lent).
- Az IP-címekből csak 12, illetve 14 különböző van, mégis a sorok kb. 82%-ában megmondják az osztályt. Ez a tesztkörnyezet felépítését tükrözi (melyik gép támadott melyiket), nem a forgalom viselkedését. Egy másik hálózaton használhatatlan lenne.
- A portok hasonlóan működnek: a `Src Port` véletlenszerű kliensport, a `Dst Port` a célgép szolgáltatását jelzi.

| Oszlop | Egyedi értékek | Tisztaság |
|---|---|---|
| Flow ID | 138 215 | 99.9% |
| Src IP | 12 | 82.4% |
| Src Port | 60 332 | 78.3% |
| Dst IP | 14 | 82.5% |
| Dst Port | 24 313 | 88.8% |
| Timestamp | 9 338 | 99.9% |

A `Timestamp` osztályonkénti időtartománya. A legtöbb érték hibás, 1970-es dátum (epoch-hiba), a Mirai viszont 2023-as. Az évszám önmagában elárulná a Mirai osztályt, ez egyértelmű szivárgás:

| Traffic Type | Első flow | Utolsó flow |
|---|---|---|
| DoS | 1970-01-01 04:08:55 | 1970-03-01 06:19:11 |
| Video | 1970-01-01 04:41:58 | 1970-02-01 04:46:19 |
| Information Gathering | 1970-01-01 05:07:29 | 1970-01-01 09:19:10 |
| Text | 1970-01-01 06:08:21 | 1970-02-01 05:09:37 |
| Background | 1970-01-01 07:18:05 | 1970-02-01 03:25:58 |
| Audio | 1970-01-01 07:41:46 | 1970-02-01 05:31:17 |
| Bruteforce | 1970-01-01 07:58:35 | 1970-02-01 10:40:33 |
| Mirai | 2023-07-02 15:43:32 | 2023-08-02 04:17:06 |

Megjegyzés: a `Dst Port` vitatható eset, mert a szolgáltatást jelzi (pl. 22 = SSH), ami valós tudás is lehet. A port azonban könnyen megváltoztatható, és ebben az adatban 88.8%-ban megmondja az osztályt, vagyis főleg a tesztkörnyezet felépítését kódolja. Ezért a feladat szerint kimarad.

## 2. Konstans és közel konstans oszlopok

Konstans (1 egyedi érték): `Bwd PSH Flags`, `Bwd URG Flags`, `Fwd Bytes/Bulk Avg`, `Fwd Packet/Bulk Avg`, `Fwd Bulk Rate Avg`.

Közel konstans (a leggyakoribb érték ≥ 99.9%): **nincs**. A legmagasabb dominanciájú nem konstans oszlopok: `Active Std` (98.04%), `Bwd Packet/Bulk Avg` (96.14%), `Bwd Bytes/Bulk Avg` (96.14%), `Bwd Bulk Rate Avg` (96.14%), `ECE Flag Count` (93.44%). A küszöböt szándékosan magasra tettem. Egy oszlop, amely a sorok 99,6%-ában 0, épp a 0,4%-nyi benign forgalmat különítheti el, ezért alacsonyabb küszöbnél ellenőrizni kellene, melyik osztályban térnek el az értékek.

## 3. Erősen korreláló párok

Pearson-korreláció, \|r\| > 0.95. A párokat csökkenő |r| szerint dolgoztam fel. Mindkét tag még megvan → az marad, amelyiknek nagyobb a kölcsönös információja (MI) a Traffic Type-pal; a másik kimarad. Ha egy tag már korábban kimaradt, a pár már eldőlt. Az MI számítása (`mutual_info_classif`, random_state=42) 8 másodpercig tartott.

| A oszlop | B oszlop | \|r\| | MI (A) | MI (B) | Döntés |
|---|---|---|---|---|---|
| Fwd Packet Length Mean | Fwd Segment Size Avg | 1.000 | 0.688 | 0.690 | marad: **Fwd Segment Size Avg** |
| Bwd Packet Length Mean | Bwd Segment Size Avg | 1.000 | 0.298 | 0.299 | marad: **Bwd Segment Size Avg** |
| Flow Packets/s | Fwd Packets/s | 0.998 | 0.328 | 0.329 | marad: **Fwd Packets/s** |
| Bwd Bytes/Bulk Avg | Bwd Packet/Bulk Avg | 0.995 | 0.088 | 0.070 | marad: **Bwd Bytes/Bulk Avg** |
| Flow IAT Max | Idle Max | 0.993 | 0.363 | 0.139 | marad: **Flow IAT Max** |
| Packet Length Mean | Average Packet Size | 0.993 | 0.712 | 0.716 | marad: **Average Packet Size** |
| Bwd Header Length | ACK Flag Count | 0.988 | 0.352 | 0.171 | marad: **Bwd Header Length** |
| Fwd Packet Length Min | Fwd Packet Length Mean | 0.983 | 0.576 | 0.688 | már eldőlt (az egyik tag korábban kimaradt) |
| Fwd Packet Length Min | Fwd Segment Size Avg | 0.983 | 0.576 | 0.690 | marad: **Fwd Segment Size Avg** |
| Idle Mean | Idle Max | 0.977 | 0.132 | 0.139 | már eldőlt (az egyik tag korábban kimaradt) |
| Total Fwd Packet | Subflow Fwd Packets | 0.976 | 0.104 | 0.116 | marad: **Subflow Fwd Packets** |
| Idle Mean | Idle Min | 0.974 | 0.132 | 0.132 | marad: **Idle Mean** |
| Total Length of Fwd Packet | Fwd Act Data Pkts | 0.974 | 0.720 | 0.122 | marad: **Total Length of Fwd Packet** |
| Flow IAT Max | Idle Mean | 0.968 | 0.363 | 0.132 | marad: **Flow IAT Max** |
| Total Bwd packets | Subflow Fwd Packets | 0.967 | 0.146 | 0.116 | marad: **Total Bwd packets** |
| Packet Length Mean | Fwd Segment Size Avg | 0.967 | 0.712 | 0.690 | már eldőlt (az egyik tag korábban kimaradt) |
| Fwd Packet Length Mean | Packet Length Mean | 0.967 | 0.688 | 0.712 | már eldőlt (az egyik tag korábban kimaradt) |
| Average Packet Size | Fwd Segment Size Avg | 0.967 | 0.716 | 0.690 | marad: **Average Packet Size** |
| Fwd Packet Length Mean | Average Packet Size | 0.967 | 0.688 | 0.716 | már eldőlt (az egyik tag korábban kimaradt) |
| Flow Duration | Fwd IAT Total | 0.966 | 0.345 | 0.215 | marad: **Flow Duration** |
| Subflow Fwd Packets | Subflow Bwd Packets | 0.963 | 0.116 | 0.092 | már eldőlt (az egyik tag korábban kimaradt) |
| Total Fwd Packet | Total Bwd packets | 0.962 | 0.104 | 0.146 | már eldőlt (az egyik tag korábban kimaradt) |
| Active Mean | Active Min | 0.962 | 0.067 | 0.067 | marad: **Active Min** |
| Active Mean | Active Max | 0.958 | 0.067 | 0.070 | már eldőlt (az egyik tag korábban kimaradt) |
| Fwd Packet Length Max | Packet Length Max | 0.957 | 0.715 | 0.714 | marad: **Fwd Packet Length Max** |
| Fwd Packet Length Min | Average Packet Size | 0.955 | 0.576 | 0.716 | már eldőlt (az egyik tag korábban kimaradt) |
| Total Bwd packets | Subflow Bwd Packets | 0.951 | 0.146 | 0.092 | marad: **Total Bwd packets** |

## 4. Opciók összevetése keresztvalidációval

RandomForest (100 fa, `class_weight='balanced'`, random_state=42), 5-fold rétegzett keresztvalidáció a train-halmazon, macro F1. Ez csak az oszlophalmazok összehasonlítására szolgál, a modellválasztás az ML7-ben lesz. Megjegyzés: a korrelációs és MI-alapú szűrést a teljes train-halmazon számoltam, ezért a CV-értékek enyhén optimisták lehetnek, de az opciók egymáshoz mért különbsége ettől még értelmezhető.

| Opció | Leírás | Oszlopok | Macro F1 (átlag ± szórás) | Idő |
|---|---|---|---|---|
| A | csak azonosítók, címkék és konstansok nélkül | 72 | 0.9151 ± 0.0346 | 7 s |
| B | A + korrelációs szűrés (\|r\| > 0.95) | 54 | 0.9120 ± 0.0183 | 7 s |
| C | B közül a 15 legnagyobb MI-jű oszlop | 15 | 0.9068 ± 0.0255 | 5 s |

**A különbségek kicsik: mindhárom átlag egy szóráson belül van.** A nagy szórást főleg a Background osztály okozza, amelyből foldonként csak 4–5 sor jut a validációra. A szűkítés tehát mérhetően nem rontja érdemben a teljesítményt, a döntést ezért az egyszerűség és a magyarázhatóság alapján lehet meghozni.

**Előnyök és hátrányok:**

- **A** – a legtöbb információ marad meg, de sok a redundáns oszlop: nehezebb elmagyarázni, a lineáris modellnél pedig a multikollinearitás instabil együtthatókat okoz.
- **B** – csak a mérhetően felesleges oszlopok esnek ki (konstans, \|r\| > 0,95 másolat), ezért minden kidobott oszlop egy mért számmal indokolható. **Ezt javaslom.**
- **C** – a legegyszerűbb (15 oszlop), de a k szám önkényes, és az MI egyenként nézi az oszlopokat, így kieshet olyan, ami csak más oszlopokkal együtt hasznos.

## 5. Minden oszlop egyenként

| Oszlop | Marad / kimarad | Kategória | Indok | Bizonyíték |
|---|---|---|---|---|
| Flow ID | kimarad | azonosító / hálózati cím | tesztkörnyezet-specifikus, nem a forgalom viselkedését írja le, nem általánosít | egyedi értékek: 138 215 (65.1%), tisztaság: 99.9% |
| Src IP | kimarad | azonosító / hálózati cím | tesztkörnyezet-specifikus, nem a forgalom viselkedését írja le, nem általánosít | egyedi értékek: 12 (0.0%), tisztaság: 82.4% |
| Src Port | kimarad | azonosító / hálózati cím | tesztkörnyezet-specifikus, nem a forgalom viselkedését írja le, nem általánosít | egyedi értékek: 60 332 (28.4%), tisztaság: 78.3% |
| Dst IP | kimarad | azonosító / hálózati cím | tesztkörnyezet-specifikus, nem a forgalom viselkedését írja le, nem általánosít | egyedi értékek: 14 (0.0%), tisztaság: 82.5% |
| Dst Port | kimarad | azonosító / hálózati cím | tesztkörnyezet-specifikus, nem a forgalom viselkedését írja le, nem általánosít | egyedi értékek: 24 313 (11.5%), tisztaság: 88.8% |
| Protocol | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 3, MI: 0.114 |
| Timestamp | kimarad | azonosító / hálózati cím | tesztkörnyezet-specifikus, nem a forgalom viselkedését írja le, nem általánosít | egyedi értékek: 9 338 (4.4%), tisztaság: 99.9% |
| Flow Duration | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 188 127, MI: 0.345 |
| Total Fwd Packet | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Subflow Fwd Packets`, amely több információt hordoz a célról | \|r\| = 0.976 a(z) `Subflow Fwd Packets` oszloppal; MI: 0.104 vs 0.116 |
| Total Bwd packets | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 340, MI: 0.146 |
| Total Length of Fwd Packet | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 1 912, MI: 0.720 |
| Total Length of Bwd Packet | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 888, MI: 0.302 |
| Fwd Packet Length Max | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 717, MI: 0.715 |
| Fwd Packet Length Min | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Fwd Segment Size Avg`, amely több információt hordoz a célról | \|r\| = 0.983 a(z) `Fwd Segment Size Avg` oszloppal; MI: 0.576 vs 0.690 |
| Fwd Packet Length Mean | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Fwd Segment Size Avg`, amely több információt hordoz a célról | \|r\| = 1.000 a(z) `Fwd Segment Size Avg` oszloppal; MI: 0.688 vs 0.690 |
| Fwd Packet Length Std | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 4 048, MI: 0.189 |
| Bwd Packet Length Max | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 311, MI: 0.294 |
| Bwd Packet Length Min | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 175, MI: 0.171 |
| Bwd Packet Length Mean | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Bwd Segment Size Avg`, amely több információt hordoz a célról | \|r\| = 1.000 a(z) `Bwd Segment Size Avg` oszloppal; MI: 0.298 vs 0.299 |
| Bwd Packet Length Std | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 1 536, MI: 0.127 |
| Flow Bytes/s | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 170 700, MI: 0.383 |
| Flow Packets/s | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Fwd Packets/s`, amely több információt hordoz a célról | \|r\| = 0.998 a(z) `Fwd Packets/s` oszloppal; MI: 0.328 vs 0.329 |
| Flow IAT Mean | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 190 221, MI: 0.313 |
| Flow IAT Std | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 85 557, MI: 0.144 |
| Flow IAT Max | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 187 122, MI: 0.363 |
| Flow IAT Min | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 153 677, MI: 0.397 |
| Fwd IAT Total | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Flow Duration`, amely több információt hordoz a célról | \|r\| = 0.966 a(z) `Flow Duration` oszloppal; MI: 0.215 vs 0.345 |
| Fwd IAT Mean | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 127 768, MI: 0.210 |
| Fwd IAT Std | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 54 896, MI: 0.113 |
| Fwd IAT Max | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 126 867, MI: 0.224 |
| Fwd IAT Min | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 112 261, MI: 0.212 |
| Bwd IAT Total | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 19 404, MI: 0.120 |
| Bwd IAT Mean | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 19 427, MI: 0.113 |
| Bwd IAT Std | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 16 082, MI: 0.088 |
| Bwd IAT Max | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 19 033, MI: 0.115 |
| Bwd IAT Min | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 10 524, MI: 0.096 |
| Fwd PSH Flags | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 2, MI: 0.013 |
| Bwd PSH Flags | kimarad | konstans | egyetlen értéket vesz fel, nem hordoz információt | egyedi értékek: 1 (mindig 0), variancia: 0 |
| Fwd URG Flags | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 2, MI: 0.016 |
| Bwd URG Flags | kimarad | konstans | egyetlen értéket vesz fel, nem hordoz információt | egyedi értékek: 1 (mindig 0), variancia: 0 |
| Fwd Header Length | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 939, MI: 0.403 |
| Bwd Header Length | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 489, MI: 0.352 |
| Fwd Packets/s | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 190 336, MI: 0.329 |
| Bwd Packets/s | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 121 032, MI: 0.327 |
| Packet Length Min | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 62, MI: 0.345 |
| Packet Length Max | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Fwd Packet Length Max`, amely több információt hordoz a célról | \|r\| = 0.957 a(z) `Fwd Packet Length Max` oszloppal; MI: 0.714 vs 0.715 |
| Packet Length Mean | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Average Packet Size`, amely több információt hordoz a célról | \|r\| = 0.993 a(z) `Average Packet Size` oszloppal; MI: 0.712 vs 0.716 |
| Packet Length Std | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 9 800, MI: 0.396 |
| Packet Length Variance | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 9 958, MI: 0.394 |
| FIN Flag Count | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 4, MI: 0.022 |
| SYN Flag Count | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 168, MI: 0.066 |
| RST Flag Count | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 3, MI: 0.138 |
| PSH Flag Count | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 307, MI: 0.074 |
| ACK Flag Count | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Bwd Header Length`, amely több információt hordoz a célról | \|r\| = 0.988 a(z) `Bwd Header Length` oszloppal; MI: 0.171 vs 0.352 |
| URG Flag Count | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 15, MI: 0.020 |
| CWR Flag Count | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 15, MI: 0.030 |
| ECE Flag Count | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 13, MI: 0.029 |
| Down/Up Ratio | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 24, MI: 0.030 |
| Average Packet Size | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 4 129, MI: 0.716 |
| Fwd Segment Size Avg | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Average Packet Size`, amely több információt hordoz a célról | \|r\| = 0.967 a(z) `Average Packet Size` oszloppal; MI: 0.690 vs 0.716 |
| Bwd Segment Size Avg | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 1 506, MI: 0.299 |
| Fwd Bytes/Bulk Avg | kimarad | konstans | egyetlen értéket vesz fel, nem hordoz információt | egyedi értékek: 1 (mindig 0), variancia: 0 |
| Fwd Packet/Bulk Avg | kimarad | konstans | egyetlen értéket vesz fel, nem hordoz információt | egyedi értékek: 1 (mindig 0), variancia: 0 |
| Fwd Bulk Rate Avg | kimarad | konstans | egyetlen értéket vesz fel, nem hordoz információt | egyedi értékek: 1 (mindig 0), variancia: 0 |
| Bwd Bytes/Bulk Avg | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 1 188, MI: 0.088 |
| Bwd Packet/Bulk Avg | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Bwd Bytes/Bulk Avg`, amely több információt hordoz a célról | \|r\| = 0.995 a(z) `Bwd Bytes/Bulk Avg` oszloppal; MI: 0.070 vs 0.088 |
| Bwd Bulk Rate Avg | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 6 114, MI: 0.077 |
| Subflow Fwd Packets | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Total Bwd packets`, amely több információt hordoz a célról | \|r\| = 0.967 a(z) `Total Bwd packets` oszloppal; MI: 0.116 vs 0.146 |
| Subflow Fwd Bytes | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 1 058, MI: 0.370 |
| Subflow Bwd Packets | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Total Bwd packets`, amely több információt hordoz a célról | \|r\| = 0.951 a(z) `Total Bwd packets` oszloppal; MI: 0.092 vs 0.146 |
| Subflow Bwd Bytes | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 748, MI: 0.121 |
| FWD Init Win Bytes | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 134, MI: 0.453 |
| Bwd Init Win Bytes | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 132, MI: 0.089 |
| Fwd Act Data Pkts | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Total Length of Fwd Packet`, amely több információt hordoz a célról | \|r\| = 0.974 a(z) `Total Length of Fwd Packet` oszloppal; MI: 0.122 vs 0.720 |
| Fwd Seg Size Min | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 7, MI: 0.259 |
| Active Mean | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Active Min`, amely több információt hordoz a célról | \|r\| = 0.962 a(z) `Active Min` oszloppal; MI: 0.067 vs 0.067 |
| Active Std | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 4 168, MI: 0.010 |
| Active Max | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 29 459, MI: 0.070 |
| Active Min | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 29 423, MI: 0.067 |
| Idle Mean | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Flow IAT Max`, amely több információt hordoz a célról | \|r\| = 0.968 a(z) `Flow IAT Max` oszloppal; MI: 0.132 vs 0.363 |
| Idle Std | marad | jellemző | nem konstans, és nincs \|r\| > 0,95 párja a megmaradó oszlopok között | egyedi értékek: 21 803, MI: 0.036 |
| Idle Max | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Flow IAT Max`, amely több információt hordoz a célról | \|r\| = 0.993 a(z) `Flow IAT Max` oszloppal; MI: 0.139 vs 0.363 |
| Idle Min | kimarad | erősen korreláló pár | szinte ugyanazt méri, mint a(z) `Idle Mean`, amely több információt hordoz a célról | \|r\| = 0.974 a(z) `Idle Mean` oszloppal; MI: 0.132 vs 0.132 |
| Label | kimarad | címkeoszlop | a célváltozóból származik, a modell bemeneteként szivárogtatná a választ | minden Traffic Type-hoz pontosan 1 Label érték tartozik; tisztaság: 65.6% |
| Traffic Type | cél | célváltozó | ezt tanulja meg a modell | 8 osztály |
| Traffic Subtype | kimarad | címkeoszlop | a célváltozó finomabb bontása, egyértelműen meghatározza | minden alosztály pontosan 1 Traffic Type-ba tartozik; tisztaság: 100.0% |

## Döntés

**A választott opció a B: 54 jellemző.** Kimaradt az azonosító és hálózati cím oszlop (6), a többi címkeoszlop (2), a konstans oszlop (5) és a korreláló párok gyengébbik tagja (18). A kiválasztott oszloplista a `src/selected_columns.json` fájlban van, ezt használja a Pipeline első lépése, így a teszthalmazon pontosan ugyanezek az oszlopok kerülnek a modellbe. A további, modellalapú szűkítést nem alkalmazzuk. Az ML9-ben a permutation importance megmutatja, mely oszlopok hagyhatók még el.
