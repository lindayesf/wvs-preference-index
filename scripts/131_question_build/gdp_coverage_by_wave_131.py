"""
gdp_coverage_by_wave_131.py

For each WVS wave, compute the share of world GDP covered by countries
represented in that wave (index_131 context).

Method:
- A country is represented in a wave if it appears in the raw WVS data.
- For each (country, wave), use the median survey year in that country-wave.
- Merge to nominal GDP shares by (iso3c, year) and sum shares by wave.

Run from project root:
    python3 scripts/131_question_build/gdp_coverage_by_wave_131.py

Outputs:
- results/index_131/diagnostics/gdp_coverage_by_wave_131.csv
- results/index_131/diagnostics/figures/gdp_coverage_by_wave_131.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

WVS_FILE = Path("data") / "WVS_Time_Series_1981-2022_csv_v5_0.csv"
GDP_FILE = Path("data") / "country_year_gdp_nominal.csv"

OUT_DIR = Path("results") / "index_131" / "diagnostics"
FIG_DIR = OUT_DIR / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]


def build_coverage() -> pd.DataFrame:
    wvs = pd.read_csv(
        WVS_FILE,
        usecols=["S002VS", "COUNTRY_ALPHA", "S020"],
        dtype=str,
    ).rename(columns={"S002VS": "wave", "COUNTRY_ALPHA": "country", "S020": "year"})

    wvs["wave"] = pd.to_numeric(wvs["wave"], errors="coerce")
    wvs["year"] = pd.to_numeric(wvs["year"], errors="coerce")
    wvs = wvs.dropna(subset=["wave", "country", "year"])

    # One survey year per (country, wave), aligned with existing index collapse logic.
    cw = (
        wvs.groupby(["country", "wave"], as_index=False)
        .agg(year=("year", "median"))
    )
    cw["year"] = cw["year"].round().astype(int)

    gdp = pd.read_csv(GDP_FILE, usecols=["iso3c", "year", "gdp_nominal_share"])
    gdp["year"] = pd.to_numeric(gdp["year"], errors="coerce")
    gdp = gdp.dropna(subset=["iso3c", "year", "gdp_nominal_share"])
    gdp["year"] = gdp["year"].astype(int)

    merged = cw.merge(gdp, left_on=["country", "year"], right_on=["iso3c", "year"], how="left")

    # Summed country shares -> percent of world GDP covered by represented countries in each wave.
    out = (
        merged.groupby("wave", as_index=False)
        .agg(
            gdp_coverage_pct=("gdp_nominal_share", "sum"),
            n_countries=("country", "nunique"),
            n_with_gdp=("gdp_nominal_share", lambda x: x.notna().sum()),
        )
        .sort_values("wave")
        .reset_index(drop=True)
    )

    # Shares are stored as fractions (0..1), convert to percent scale.
    out["gdp_coverage_pct"] = (out["gdp_coverage_pct"] * 100).round(2)
    return out


def plot_coverage(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))

    x = df["wave"].astype(int).astype(str)
    y = df["gdp_coverage_pct"]

    ax.bar(x, y, color="#2980b9")
    for i, v in enumerate(y):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=9)

    ax.set_ylim(0, max(100, float(y.max()) + 8))
    ax.set_xlabel("WVS wave")
    ax.set_ylabel("World GDP coverage (%)")
    ax.set_title("Index 131 context: % of world GDP covered by represented countries")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "gdp_coverage_by_wave_131.png", dpi=300)
    plt.close()


def main() -> None:
    print("Computing GDP coverage by wave (index_131 context)...")
    out = build_coverage()

    out_path = OUT_DIR / "gdp_coverage_by_wave_131.csv"
    out.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")

    print("\nSummary:")
    print(out.to_string(index=False))

    plot_coverage(out)
    print(f"Saved: {FIG_DIR / 'gdp_coverage_by_wave_131.png'}")


if __name__ == "__main__":
    main()
