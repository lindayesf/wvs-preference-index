"""Exercise 2 visualization for the 131-question build.

Reads current Exercise 2 outputs from results/index_131/exercise2/:
- weighted_variance_sweep_index_*_ym.csv
- weighted_variance_sweep_index_*_y.csv

Writes figures to results/index_131/exercise2/figures/.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]

RESULTS_DIR = Path("results") / "index_131"
EX2_DIR = RESULTS_DIR / "exercise2"
FIG_DIR = EX2_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

DOMAIN_COLS = ["index_all", "index_imf", "index_idawb", "index_unsc"]
DOMAIN_TITLES = {
    "index_all": "All",
    "index_imf": "IMF",
    "index_idawb": "IDA/WB",
    "index_unsc": "UNSC",
}

REEVAL_GROUPS = {
    "reeval_ym_127": {
        "suffix": "ym",
        "title": "Re-evaluation in {y,m} (127 questions)",
    },
    "reeval_y_86": {
        "suffix": "y",
        "title": "Re-evaluation = y (86 questions)",
    },
}


def load_sweep(domain: str, suffix: str) -> pd.DataFrame:
    path = EX2_DIR / f"weighted_variance_sweep_{domain}_{suffix}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing required sweep file: {path}")
    return pd.read_csv(path)


def plot_reevaluation_grid(group_name: str, suffix: str, title: str) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    axes = axes.flatten()

    for ax, domain in zip(axes, DOMAIN_COLS):
        sweep = load_sweep(domain, suffix)
        sweep = sweep[sweep["wave"].between(3, 7)].copy()

        for wave, group in sweep.groupby("wave"):
            group = group.sort_values("weighting_year")
            ax.plot(
                group["weighting_year"],
                group["weighted_variance"],
                marker="o",
                markersize=2.5,
                linewidth=1.2,
                label=f"Wave {int(wave)}",
            )

        ax.set_title(DOMAIN_TITLES[domain])
        ax.set_xlabel("GDP weighting year")
        ax.set_ylabel("Weighted variance")

    axes[0].legend(title="WVS wave", fontsize=8, loc="best")
    fig.suptitle(f"Sensitivity of GDP-weighted variance to weighting year: {title}", fontsize=13, y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    out_path = FIG_DIR / f"weighted_variance_sweep_domains_{group_name}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  Saved: {out_path}")


def main() -> None:
    print("Generating Exercise 2 re-evaluation sensitivity charts...")
    for group_name, cfg in REEVAL_GROUPS.items():
        plot_reevaluation_grid(group_name, cfg["suffix"], cfg["title"])
    print(f"\nAll Exercise 2 figures saved to {FIG_DIR}/")


if __name__ == "__main__":
    main()
