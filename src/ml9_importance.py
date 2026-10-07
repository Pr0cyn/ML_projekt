"""ML9: permutation importance of the two final models, compared with the ML5 column decisions.

Importance is measured out-of-fold on the train set (same 5 folds as ML7): in each
fold the project's final Pipeline is fitted on 4 folds and every column is shuffled
on the 5th; the drop in macro F1 is the column's importance. The test set is not used.
"""

import importlib.util
import json
import time
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.base import clone  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402
from sklearn.model_selection import StratifiedKFold, cross_val_score  # noqa: E402

from preprocessing import RANDOM_STATE, TARGET, load_selected_columns  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TRAIN_PARQUET = ROOT / "data" / "processed" / "train.parquet"
REPORT = ROOT / "reports" / "06_feature_importance.md"
FIGURE = ROOT / "reports" / "feature_importance.png"
PROJECTS = {"DecisionTree": ROOT / "projects" / "decision_tree",
            "RandomForest": ROOT / "projects" / "random_forest"}
COLORS = {"DecisionTree": "#2a78d6", "RandomForest": "#eb6834"}  # categorical slots 1-2
INK, INK_MUTED, GRID = "#1f1f1f", "#6b6b6b", "#e6e6e6"
N_REPEATS = 5
TOP_N_PLOT = 15
TOP_K_CHECK = [5, 10, 15, 20]


def load_project_pipeline(name: str, project_dir: Path):
    spec = importlib.util.spec_from_file_location(f"{name}_tune", project_dir / "tune.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    params = json.loads((project_dir / "best_params.json").read_text(encoding="utf-8"))
    return mod.build_pipeline().set_params(**params)


def md_table(headers: list[str], rows: list[tuple]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def plot(imp: dict[str, pd.DataFrame]) -> None:
    """Small multiples: one panel per model, each with its own top features and own x scale
    (the two models' importances differ by an order of magnitude)."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 0.42 * TOP_N_PLOT + 1.8))
    for ax, (name, df) in zip(axes, imp.items()):
        top = df.iloc[:TOP_N_PLOT]
        y = np.arange(len(top))
        ax.barh(y, top["mean"], height=0.7, color=COLORS[name],
                xerr=top["std"], error_kw={"ecolor": INK_MUTED, "elinewidth": 1, "capsize": 0})
        ax.set_yticks(y, top.index, fontsize=9, color=INK)
        ax.invert_yaxis()
        ax.set_title(name, fontsize=11, color=INK, loc="left")
        ax.set_xlabel("A macro F1 csökkenése keverés után", fontsize=9, color=INK)
        ax.axvline(0, color=INK_MUTED, linewidth=1)
        ax.grid(axis="x", color=GRID, linewidth=1)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="x", colors=INK_MUTED, labelsize=8)
        ax.tick_params(axis="y", length=0)
    fig.suptitle(f"Permutation importance – a {TOP_N_PLOT} legfontosabb oszlop modellenként "
                 "(train, 5-fold, átlag ± szórás; a két panel skálája eltér)", fontsize=11, color=INK, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(FIGURE, dpi=150, facecolor="white")
    plt.close(fig)


def main() -> None:
    tr = pd.read_parquet(TRAIN_PARQUET)
    cols = load_selected_columns()
    X, y = tr[cols], tr[TARGET].to_numpy()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    folds = list(cv.split(X, y))
    ml5 = json.loads((ROOT / "src" / "column_options.json").read_text(encoding="utf-8"))

    imp: dict[str, pd.DataFrame] = {}
    mdi: dict[str, pd.Series] = {}
    pipes = {}
    for name, pdir in PROJECTS.items():
        pipe = load_project_pipeline(name, pdir)
        pipes[name] = pipe
        final = joblib.load(pdir / "models" / "pipeline.joblib")
        mdi[name] = pd.Series(final.named_steps["model"].feature_importances_, index=cols)
        cache = pdir / "permutation_importance.csv"
        if cache.exists():
            imp[name] = pd.read_csv(cache, index_col="feature")
            print(f"{name}: permutation importance loaded from {cache.name}")
            continue
        t0 = time.perf_counter()
        per_fold = []
        for tr_idx, va_idx in folds:
            model = clone(pipe).fit(X.iloc[tr_idx], y[tr_idx])
            r = permutation_importance(model, X.iloc[va_idx], y[va_idx], scoring="f1_macro",
                                       n_repeats=N_REPEATS, random_state=RANDOM_STATE, n_jobs=-1)
            per_fold.append(r.importances)  # (n_features, n_repeats)
        allv = np.concatenate(per_fold, axis=1)
        imp[name] = pd.DataFrame({"mean": allv.mean(axis=1), "std": allv.std(axis=1)}, index=cols) \
            .sort_values("mean", ascending=False)
        imp[name]["rank"] = np.arange(1, len(cols) + 1)
        imp[name].to_csv(cache, index_label="feature")
        print(f"{name}: permutation importance in {time.perf_counter() - t0:.0f}s; "
              f"top: {list(imp[name].index[:5])}")

    # --- Top-k check: CV macro F1 with only the k most important columns (per model)
    from sklearn.pipeline import Pipeline  # noqa: E402
    from preprocessing import preprocessing_steps  # noqa: E402
    topk_rows = []
    for name, pipe in pipes.items():
        row = [name]
        for k in TOP_K_CHECK + [len(cols)]:
            feats = list(imp[name].index[:k])
            p = Pipeline(preprocessing_steps(feats) + [("model", clone(pipe.named_steps["model"]))])
            s = cross_val_score(p, X, y, cv=cv, scoring="f1_macro")
            row.append(f"{s.mean():.4f} ± {s.std():.4f}")
            print(f"{name} top-{k}: {s.mean():.4f}")
        topk_rows.append(tuple(row))

    # --- Plot: union of the top features by average rank
    avg_rank = (imp["DecisionTree"]["rank"] + imp["RandomForest"]["rank"]) / 2
    plot(imp)

    # --- Comparison with ML5
    noise = {n: list(df.index[(df["mean"] - df["std"]) <= 0]) for n, df in imp.items()}
    useless_both = sorted(set(noise["DecisionTree"]) & set(noise["RandomForest"]))
    zero_both = sorted(set(imp["DecisionTree"].index[imp["DecisionTree"]["mean"] <= 0])
                       & set(imp["RandomForest"].index[imp["RandomForest"]["mean"] <= 0]))
    cum = {}
    for n, df in imp.items():
        pos = df["mean"].clip(lower=0)
        share = pos.cumsum() / pos.sum()
        cum[n] = {q: int((share < q).sum() + 1) for q in (0.8, 0.9, 0.95)}
    corr_dropped = [c for c in ml5["A"] if c not in ml5["B"]]
    report_ml5 = (ROOT / "reports" / "02_oszlopok.md").read_text(encoding="utf-8")
    direct = {}
    for c in corr_dropped:
        line = next(ln for ln in report_ml5.splitlines() if ln.startswith(f"| {c} | kimarad | erősen korreláló pár |"))
        direct[c] = line.split("`")[1]
    twin_rows = []
    for c in corr_dropped:
        chain = [direct[c]]
        while chain[-1] not in cols:  # the twin itself may have been dropped later in favour of another column
            chain.append(direct[chain[-1]])
        kept = chain[-1]
        via = f" (a(z) {', '.join(chain[:-1])} oszlopon át)" if len(chain) > 1 else ""
        twin_rows.append((c, kept + via, int(imp["DecisionTree"].loc[kept, "rank"]),
                          int(imp["RandomForest"].loc[kept, "rank"])))

    top_rows = []
    table_feats = set(imp["DecisionTree"].index[:10]) | set(imp["RandomForest"].index[:10])
    for c in avg_rank.loc[sorted(table_feats)].sort_values().index:
        d, r = imp["DecisionTree"].loc[c], imp["RandomForest"].loc[c]
        top_rows.append((c, int(d["rank"]), f"{d['mean']:.4f} ± {d['std']:.4f}", int(r["rank"]),
                         f"{r['mean']:.4f} ± {r['std']:.4f}", f"{mdi['RandomForest'][c]:.3f}"))

    out = ["# 06 – Feature importance (ML9)", "",
           "**Permutation importance:** egy oszlop értékeit véletlenszerűen összekeverjük, így az oszlop és a "
           "célváltozó kapcsolata megszűnik, és megmérjük, mennyit csökken a macro F1. Ha semmit, a modell "
           "nem használja érdemben az oszlopot.", "",
           "**Hogyan mértem:** a **train-halmazon**, ugyanazzal az 5 folddal, mint az ML7-ben. Minden foldban a "
           "projekt végső Pipeline-ja (hangolt beállításokkal) 4 folddal tanult, és a fontosságot az ötödiken "
           f"mértem, amelyet nem látott; oszloponként {N_REPEATS} keverés foldonként, összesen "
           f"{5 * N_REPEATS} érték átlaga és szórása. A teszthalmazt nem használtam. "
           "Ha a fontosságot a teljes train-halmazon tanult modell saját tanítóadatán mérném, az a "
           "„bemagolt” összefüggéseket is fontosnak mutatná.", "",
           "![Feature importance](feature_importance.png)", "",
           "## 1. A legfontosabb oszlopok", "",
           "Mindkét modell 10 legfontosabb oszlopa, a két modell átlagos helyezése szerint rendezve. Az utolsó oszlop a RandomForest beépített "
           "(impurity alapú) fontossága összehasonlításként: ez gyorsan számolható, de a sok különböző "
           "értékkel bíró oszlopokat túlértékeli, és a tanítóadaton mér.", "",
           md_table(["Oszlop", "DT rang", "DT fontosság", "RF rang", "RF fontosság", "RF impurity"], top_rows), "",
           "## 2. Hány oszlop hordozza a fontosságot?", "",
           md_table(["Modell", "A pozitív fontosság 80%-a", "90%-a", "95%-a"],
                    [(n, f"{c[0.8]} oszlop", f"{c[0.9]} oszlop", f"{c[0.95]} oszlop") for n, c in cum.items()]), "",
           "Ellenőrzés: ugyanaz a modell csak a k legfontosabb oszloppal, 5-fold CV a train-halmazon "
           "(macro F1). Megjegyzés: a rangsort ugyanezeken a foldokon mértem, ezért a kis k-jú értékek "
           "enyhén optimisták lehetnek.", "",
           md_table(["Modell"] + [f"Top {k}" for k in TOP_K_CHECK] + [f"Mind a {len(cols)}"], topk_rows), "",
           "**A zaj nagysága:** a „Mind” oszlop ugyanaz a modell, mint a hangolásnál, csak az oszlopok "
           "sorrendje más (fontossági sorrend). A RandomForest minden kérdésnél véletlenszerűen választ "
           "oszlopokat, ezért más sorrend más erdőt ad, és ez önmagában kb. 0,01 eltérést okozhat a macro "
           "F1-ben. Az ennél kisebb különbségek tehát zajnak tekintendők.", "",
           "## 3. Összevetés az ML5 döntéseivel", "",
           f"- **Elhagyható jelöltek:** {len(useless_both)} oszlop fontossága mindkét modellben a zajon belül "
           "van (átlag − szórás ≤ 0)"
           + (f": {', '.join(f'`{c}`' for c in useless_both)}." if useless_both else "."),
           f"- Ebből {len(zero_both)} oszlop átlagos fontossága is ≤ 0 mindkét modellben.",
           "- **Az ML5-ben kihagyott korreláló oszlopok** megmaradt párja hol áll a rangsorban (54 oszlopból). "
           "Ha a megmaradt pár fontos, az mutatja, hogy az információt nem veszítettük el, csak a másolatot "
           "dobtuk ki:", "",
           md_table(["Kihagyott oszlop (ML5)", "Megmaradt pár", "DT rang", "RF rang"], twin_rows), "",
           "- **A kihagyott azonosító oszlopok** (IP, port, Timestamp) nincsenek a modellben, így a fenti "
           "fontosságok kizárólag a forgalom viselkedését leíró jellemzőkből jönnek. Ez az ML5 egyik célja volt.",
           f"- **Flow IAT Min** (ML6, negatív értékek az Audio/Text osztályban): DT rang "
           f"{int(imp['DecisionTree'].loc['Flow IAT Min', 'rank'])}, RF rang "
           f"{int(imp['RandomForest'].loc['Flow IAT Min', 'rank'])}.",
           "- **Korlát:** ha két megmaradt oszlop még mindig erősen összefügg (|r| 0,90–0,95 között), a "
           "permutation importance mindkettőt alulbecsülheti, mert a modell a másikból pótolja a kevert "
           "oszlop információját.", ""]
    dt_imp, rf_imp = imp["DecisionTree"], imp["RandomForest"]
    fim = "Flow IAT Min"
    out += ["## 4. Mit jelent ez?", "",
            f"- **A két modell egészen másképp használja az oszlopokat.** A DecisionTree-nél egy-egy oszlop "
            f"összekeverése nagyot üt: a legfontosabb (`{dt_imp.index[0]}`) után a macro F1 "
            f"{dt_imp['mean'].iloc[0]:.2f}-dal esik. A RandomForestnél a legnagyobb esés is csak "
            f"{rf_imp['mean'].iloc[0]:.3f} (`{rf_imp.index[0]}`). Az egyetlen fa minden döntési útvonala "
            "konkrét oszlopokra épül, ezért ha egy oszlop „elromlik”, az egész útvonal hibázik. A 100 fa "
            "véletlen oszlophalmazokkal tanult, így ugyanazt az információt sok különböző oszlopból is "
            "kiolvassa: ha egyet elveszünk, a többi pótolja. Ez a redundancia az RF stabilitásának oka.",
            f"- **Ezért az RF-nél a „nulla körüli fontosság” nem azt jelenti, hogy az oszlop haszontalan,** csak "
            "azt, hogy pótolható. Az elhagyható oszlopokról ezért nem a fontosság, hanem a top-k ellenőrzés "
            "dönt (2. pont): a 20 legfontosabb oszlop mindkét modellnél a teljes 54 oszlop eredményét hozza, "
            "a zajon belül.",
            f"- **`{fim}`:** a DecisionTree legfontosabb oszlopa ({int(dt_imp.loc[fim, 'rank'])}. hely, "
            f"{dt_imp.loc[fim, 'mean']:.2f}), a RandomForestnél viszont az utolsó ({int(rf_imp.loc[fim, 'rank'])}. hely, "
            f"{rf_imp.loc[fim, 'mean']:.3f}). Ez az az oszlop, amelynek negatív értékei az ML6-ban csak az "
            "Audio és a Text osztályban fordultak elő. A DT erősen támaszkodik rá, az RF egyáltalán nem igényli, "
            "vagyis az RF eredménye biztosan nem ezen a felvételi hibán múlik.",
            "- **Összevetés az ML5-tel:** a korreláló párokból megtartott oszlopok több esetben a rangsor elején "
            "állnak (pl. `Fwd Packet Length Max`, `Average Packet Size`, `Flow Duration`), tehát a kihagyott "
            "másolatokkal nem veszett el információ. A top-k ellenőrzés szerint pedig az 54 oszlop tovább "
            "szűkíthető kb. 20-ra; ezt az ML5-ben nem tettük meg, de a „mit csinálnék másként” része lehet.", ""]
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print("cumulative:", cum, "| noise in both:", len(useless_both), "| zero in both:", len(zero_both))


if __name__ == "__main__":
    main()
