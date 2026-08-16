"""
wvs_data_diagnostics_131.py (131-question build)

Descriptive analysis of the underlying WVS sample, using the 131-question
set.

Run from the project root, AFTER build_index_131.py has been run at least
once (this script reuses its loading functions):
    python3 scripts/131_question_build/wvs_data_diagnostics_131.py

Outputs CSVs and figures into results/index_131/diagnostics/
"""

import sys
sys.path.insert(0, "scripts/131_question_build")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]

from build_index_131 import (
    load_wvs_data,
    load_keep_sheet_131, QUESTIONS_131_FILE, WVS_FILE,
    CATEGORICAL_SOURCE_VARS_131,
)

DIAG_DIR = Path("results") / "index_131" / "diagnostics"
DIAG_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR = DIAG_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def make_visuals(df, variables, n_per_cw, year_counts,
                  waves_per_country, coverage, missing_rate, missing_by_wave,
                  question_counts_by_wave):

    n_vars = len(variables)

    # 1. Respondents per wave
    resp_per_wave = df.groupby("wave").size()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(resp_per_wave.index.astype(int).astype(str), resp_per_wave.values, color="#2980b9")
    for i, v in enumerate(resp_per_wave.values):
        ax.text(i, v + 3000, f"{v:,}", ha="center", fontsize=9)
    ax.set_xlabel("WVS wave")
    ax.set_ylabel("Respondents")
    ax.set_title("Respondents per wave (131-question build)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "respondents_per_wave.png", dpi=300)
    plt.close()

    # 2. Panel balance ***
    balance_counts = waves_per_country.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(balance_counts.index.astype(str), balance_counts.values, color="#2980b9")
    ax.set_xlabel("Number of waves a country appears in (out of 7)")
    ax.set_ylabel("Number of countries")
    ax.set_title("Panel balance across countries")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "panel_balance.png", dpi=300)
    plt.close()

    # 3. Countries per wave
    countries_per_wave = df.groupby("wave")["country"].nunique()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(countries_per_wave.index.astype(int).astype(str), countries_per_wave.values, color="#2980b9")
    for i, v in enumerate(countries_per_wave.values):
        ax.text(i, v + 1, str(v), ha="center", fontsize=9)
    ax.set_xlabel("WVS wave")
    ax.set_ylabel("Number of distinct countries surveyed")
    ax.set_title("Country coverage per wave")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "countries_per_wave.png", dpi=300)
    plt.close()

    # 4. Missingness per question - 131 questions is a lot to fit on one
    # chart legibly, so this one is taller and only labels every few ticks
    fig, ax = plt.subplots(figsize=(9, 22))
    sorted_missing = missing_rate.sort_values()
    colors = ["#c0392b" if v > 50 else "#2980b9" for v in sorted_missing]
    ax.barh(sorted_missing.index, sorted_missing.values, color=colors)
    ax.axvline(50, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("% missing (only in waves where question is fielded)")
    ax.set_title(f"Missing-data rate by kept question ({n_vars} questions)\n(red = majority missing even when fielded)")
    ax.tick_params(axis="y", labelsize=6)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "missingness_per_question.png", dpi=300)
    plt.close()

    # 5a. Question fielding across waves. ***
    # "Fielded" = not 100% missing in that wave.
    fielded_by_wave = (missing_by_wave < 100)
    n_waves_fielded = fielded_by_wave.sum(axis=0).sort_values()
    fig, ax = plt.subplots(figsize=(9, 22))
    colors = ["#c0392b" if v <= 3 else "#2980b9" for v in n_waves_fielded]
    ax.barh(n_waves_fielded.index, n_waves_fielded.values, color=colors)
    ax.set_xlabel("Number of waves (out of 7) where question is fielded")
    ax.set_title(f"Question fielding across waves ({n_vars} questions)\n(red = fielded in 3 or fewer waves)")
    ax.set_xticks(range(0, 8))
    ax.tick_params(axis="y", labelsize=6)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "question_fielded_by_wave.png", dpi=300)
    plt.close()

    # 5b. Question usability across waves (same cutoff as earlier analyses). ***
    usable_by_wave = (missing_by_wave < 50)
    n_waves_usable = usable_by_wave.sum(axis=0).sort_values()
    fig, ax = plt.subplots(figsize=(9, 22))
    colors = ["#c0392b" if v <= 3 else "#2980b9" for v in n_waves_usable]
    ax.barh(n_waves_usable.index, n_waves_usable.values, color=colors)
    ax.set_xlabel("Number of waves (out of 7) where question is usable (<50% missing)")
    ax.set_title(
        f"Question availability across waves ({n_vars} questions)\n"
        "(red = usable in 3 or fewer waves; diagnostic flag only, all kept questions are still used in analysis)"
    )
    ax.set_xticks(range(0, 8))
    ax.tick_params(axis="y", labelsize=6)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "question_usable_by_wave.png", dpi=300)
    plt.close()

    # 6. Total questions fielded per wave 
    fig, ax = plt.subplots(figsize=(8, 5))
    x = question_counts_by_wave["wave"].astype(int).astype(str)
    y = question_counts_by_wave["n_questions_fielded"]
    ax.bar(x, y, color="#2980b9")
    for i, v in enumerate(y):
        ax.text(i, v + 1, str(int(v)), ha="center", fontsize=9)
    ax.set_xlabel("WVS wave")
    ax.set_ylabel("Number of questions fielded")
    ax.set_title("Index 131: total questions fielded per wave")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "question_counts_per_wave_131.png", dpi=300)
    plt.close()

    # 7. Domain-specific fielded question counts per wave
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = question_counts_by_wave["wave"].astype(int).tolist()
    width = 0.23
    ax.bar([v - width for v in x], question_counts_by_wave["n_imf_fielded"],
           width=width, label="IMF", color="#1f77b4")
    ax.bar(x, question_counts_by_wave["n_idawb_fielded"], width=width,
           label="IDA/WB", color="#2ca02c")
    ax.bar([v + width for v in x], question_counts_by_wave["n_unsc_fielded"],
           width=width, label="UNSC", color="#d62728")
    ax.set_xticks(x)
    ax.set_xlabel("WVS wave")
    ax.set_ylabel("Number of questions fielded")
    ax.set_title("Index 131: fielded questions per wave by domain")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "question_counts_by_wave_domains_131.png", dpi=300)
    plt.close()

    print(f"Saved 8 diagnostic figures to {FIG_DIR}/")


def main():
    print("Loading 131-question Keep sheet and WVS data...")
    keep131 = load_keep_sheet_131(QUESTIONS_131_FILE)
    # Include categorical source vars too, so their raw availability shows
    # up in these diagnostics (not just the 116 plain-ordinal ones)
    variables = sorted(set(keep131["variable"].tolist()) | set(CATEGORICAL_SOURCE_VARS_131))
    df = load_wvs_data(WVS_FILE, variables)
    print(f"  Loaded {len(df):,} respondents, {len(variables)} kept questions/source vars.\n")

    # -----------------------------------------------------------------
    # 1. Respondents per country-wave
    # -----------------------------------------------------------------
    n_per_cw = df.groupby(["country", "wave"]).size().reset_index(name="n_respondents")
    n_per_cw.to_csv(DIAG_DIR / "n_per_country_wave.csv", index=False)

    print("=== Respondents per country-wave ===")
    print(n_per_cw["n_respondents"].describe())
    print()
    print("Smallest country-waves:")
    print(n_per_cw.nsmallest(10, "n_respondents").to_string(index=False))
    print()

    # -----------------------------------------------------------------
    # 2. Years
    # -----------------------------------------------------------------
    year_counts = df["year"].value_counts().sort_index()
    year_counts.to_csv(DIAG_DIR / "respondents_per_year.csv", header=["n_respondents"])

    # -----------------------------------------------------------------
    # 3. Countries with most/least total respondents
    # -----------------------------------------------------------------
    n_per_country = df.groupby("country").size().sort_values(ascending=False)
    n_per_country.to_csv(DIAG_DIR / "n_per_country_total.csv", header=["n_respondents"])

    # -----------------------------------------------------------------
    # 4. Panel balance
    # -----------------------------------------------------------------
    waves_per_country = df.groupby("country")["wave"].nunique().sort_values(ascending=False)
    waves_per_country.to_csv(DIAG_DIR / "waves_per_country.csv", header=["n_waves_present"])

    balance_summary = waves_per_country.value_counts().sort_index(ascending=False)
    print("=== Panel balance ===")
    print(balance_summary.rename("n_countries").to_string())
    print()

    coverage = df.groupby(["country", "wave"]).size().unstack(fill_value=0)
    coverage.to_csv(DIAG_DIR / "coverage_matrix_country_by_wave.csv")

    # -----------------------------------------------------------------
    # 5. Missing-data rate per kept question
    # -----------------------------------------------------------------
    missing_rate_vals = {}
    for var in variables:
        present_waves = df.groupby("wave")[var].apply(lambda x: x.notna().any())
        waves_with_question = present_waves[present_waves].index
        sub = df[df["wave"].isin(waves_with_question)][var]
        missing_rate_vals[var] = sub.isna().mean() * 100 if len(sub) else np.nan

    missing_rate = pd.Series(missing_rate_vals).sort_values(ascending=False)
    missing_rate.to_csv(
        DIAG_DIR / "missing_rate_per_question.csv",
        header=["pct_missing_in_fielded_waves"],
    )

    print("=== Missing-data rate (highest 10, only in waves where question is fielded) ===")
    print(missing_rate.head(10).round(1).to_string())
    print()

    missing_by_wave = df.groupby("wave")[variables].apply(lambda x: x.isna().mean() * 100)
    missing_by_wave.to_csv(DIAG_DIR / "missing_rate_by_question_and_wave.csv")

    # -----------------------------------------------------------------
    # 6. Question counts fielded by wave (total + by domain)
    # -----------------------------------------------------------------
    fielded_by_wave = missing_by_wave < 100
    imf_vars = keep131.loc[keep131["is_imf"], "variable"].tolist()
    idawb_vars = keep131.loc[keep131["is_idawb"], "variable"].tolist()
    unsc_vars = keep131.loc[keep131["is_unsc"], "variable"].tolist()

    question_counts_by_wave = pd.DataFrame({
        "wave": fielded_by_wave.index,
        "n_questions_fielded": fielded_by_wave.sum(axis=1).values,
        "n_imf_fielded": fielded_by_wave[imf_vars].sum(axis=1).values,
        "n_idawb_fielded": fielded_by_wave[idawb_vars].sum(axis=1).values,
        "n_unsc_fielded": fielded_by_wave[unsc_vars].sum(axis=1).values,
    }).sort_values("wave").reset_index(drop=True)
    question_counts_by_wave.to_csv(DIAG_DIR / "question_counts_by_wave_131.csv", index=False)

    print("=== Questions fielded by wave (total + domains) ===")
    print(question_counts_by_wave.to_string(index=False))
    print()

    fully_missing_in_some_wave = (missing_by_wave == 100).any(axis=0)
    flagged = fully_missing_in_some_wave[fully_missing_in_some_wave].index.tolist()
    print(f"{len(flagged)} of {len(variables)} questions are 100% missing in at least one wave.")
    print()

    print(f"All diagnostic tables saved to {DIAG_DIR}/")

    print("\nGenerating diagnostic visuals...")
    make_visuals(df, variables, n_per_cw, year_counts,
                 waves_per_country, coverage, missing_rate, missing_by_wave,
                 question_counts_by_wave)


if __name__ == "__main__":
    main()
