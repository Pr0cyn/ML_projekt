# Munkanapló

**ML1** – uv-s projektet hoztam létre Python 3.12-vel és a szükséges függőségekkel (pandas, pyarrow, numpy, scikit-learn, matplotlib, joblib, duckdb); a nyers CSV a data/raw/data.csv helyre került, és a data/ mappa a .gitignore miatt nem kerül a repóba. DuckDB-vel, teljes betöltés nélkül ellenőriztem: 4,68 GB, 86 oszlop, 8 656 767 sor, és mindhárom címkeoszlop (Label, Traffic Type, Traffic Subtype) megvan.

**ML2** – DuckDB-vel (Parquet-másolaton) felmértem a 86 oszlopot és a címkéket: a Traffic Type 8 osztályú, extrém kiegyensúlyozatlan (DoS 86,5%, a Background csak 32 sor, benign összesen 1301), hiányzó vagy végtelen érték pedig sehol sincs, ezt a nyers szövegen is ellenőriztem. Az egyetlen anomália a negatív `Flow IAT Min` (72 sor), ami kizárólag az Audio (23%) és a Text (13%) osztályban fordul elő, tehát osztályhoz kötött; ezt az ML6-ban kezelni kell.
