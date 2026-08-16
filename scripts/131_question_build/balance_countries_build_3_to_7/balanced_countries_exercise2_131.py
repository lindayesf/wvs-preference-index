"""Exercise 2 outputs for countries present in WVS waves 3 to 7.

Uses precomputed indices from results/index_131/preference_it_131.csv.
Restricts the sample to countries listed in
results/index_131/diagnostics/countries_present_all_waves_3_to_7.csv.

Outputs:
    - GDP-weighted variance sweeps (1974-2025) for the 8 output indices:
        * index_*_ym (Re-evaluation in {y, m}; 127-question subset)
        * index_*_y  (Re-evaluation == y; 86-question subset)
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("data")
RESULTS_DIR = Path("results") / "index_131"
EX2_DIR = RESULTS_DIR / "balanced_countries_exercise2"
EX2_DIR.mkdir(parents=True, exist_ok=True)
# THIS IS ADDED FOR BALANCED COUNTRIES EXERCISE 2: 
COUNTRIES_FILE = RESULTS_DIR / "diagnostics" / "countries_present_all_waves_3_to_7.csv"

PREFERENCE_FILE = RESULTS_DIR / "preference_it_131.csv"
GDP_FILE = DATA_DIR / "country_year_gdp_nominal.csv"

GDP_YEAR_MIN = 1974
GDP_YEAR_MAX = 2025

INDEX_COLS = [
    "index_all_ym", "index_imf_ym", "index_idawb_ym", "index_unsc_ym",
    "index_all_y", "index_imf_y", "index_idawb_y", "index_unsc_y",
]

REEVAL_GROUPS = {
    "reeval_ym_127": {
        "index_all": "index_all_ym",
        "index_imf": "index_imf_ym",
        "index_idawb": "index_idawb_ym",
        "index_unsc": "index_unsc_ym",
    },
    "reeval_y_86": {
        "index_all": "index_all_y",
        "index_imf": "index_imf_y",
        "index_idawb": "index_idawb_y",
        "index_unsc": "index_unsc_y",
    },
}

# Country-set handling across GDP weighting years.
#   False = original behaviour: countries enter/leave as GDP coverage changes.
#   True  = hold the country set fixed (only countries with GDP in every year).
# Left at False so results are unchanged from the original script. Flipping
# this is a methodological decision, can be later changed. 
BALANCED_PANEL = False


def weighted_variance(values: np.ndarray, weights: np.ndarray) -> float:
    """Population-style (ddof = 0) weighted variance: sum(w*(x-xbar)^2) / sum(w)."""
    mask = ~(np.isnan(values) | np.isnan(weights))
    values, weights = values[mask], weights[mask]
    if weights.sum() == 0 or len(values) < 2:
        return np.nan
    xbar = np.average(values, weights=weights)
    return np.average((values - xbar) ** 2, weights=weights)


def _balanced_country_set(gdp: pd.DataFrame) -> set:
    """Countries with a non-null GDP figure in EVERY weighting year.

    Used when balanced-panel mode (so BALANCED_PANEL = True) is enabled, so country membership stays
    fixed across weighting years.
    """
    g = gdp.dropna(subset=["gdp_nominal"])
    n_years = g["year"].nunique()
    coverage = g.groupby("iso3c")["year"].nunique()
    return set(coverage[coverage == n_years].index)


def compute_sweep(pref: pd.DataFrame, gdp: pd.DataFrame, index_col: str,
                  balanced: bool = None) -> pd.DataFrame:
    """Sweep the GDP weighting year for one index column.

    balanced=True  fixes the country set across all weighting years.
    balanced=False reproduces the old per-year inner join, for comparison.
    """
    if balanced is None:
        balanced = BALANCED_PANEL

    gdp = (gdp[gdp["year"].between(GDP_YEAR_MIN, GDP_YEAR_MAX)]
              .dropna(subset=["gdp_nominal"])
              .drop_duplicates(subset=["iso3c", "year"]))
    weighting_years = sorted(gdp["year"].unique())
    waves = sorted(pref["wave"].unique())

    always = _balanced_country_set(gdp) if balanced else None
    gdp_by_year = {y: g.set_index("iso3c")["gdp_nominal"]
                   for y, g in gdp.groupby("year")}

    records = []
    for wave in waves:
        wave_df = pref[pref["wave"] == wave][["country", index_col]].dropna()
        if balanced:
            wave_df = wave_df[wave_df["country"].isin(always)]
        duplicates = sorted(wave_df.loc[wave_df["country"].duplicated(), "country"].unique())
        if duplicates:
            raise RuntimeError(
                f"Exercise 2 expects at most one row per country after preprocessing "
                f"for wave {wave}, index {index_col}; duplicates found: {duplicates}"
            )
        sub = wave_df.set_index("country")[index_col]

        for wy in weighting_years:
            gser = gdp_by_year[wy]
            common = sub.index.intersection(gser.index)
            x = sub.loc[common].to_numpy(dtype=float)
            w = gser.loc[common].to_numpy(dtype=float)

            var = weighted_variance(x, w)

            total = np.nansum(w)
            wn = w / total if total > 0 else w

            records.append({
                "wave": wave,
                "weighting_year": wy,
                "weighted_variance": var,
                "n_countries": len(common),
                "top1_share": float(np.nanmax(wn)) if len(wn) else np.nan,
                "balanced_panel": balanced,
            })
    return pd.DataFrame(records)


def compute_unweighted_baseline(pref: pd.DataFrame, index_col: str) -> pd.DataFrame:
    return (
        pref.groupby("wave")[index_col]
        .agg(unweighted_mean="mean", unweighted_variance="var", n_countries="count")
        .reset_index()
    )


def require_columns(df: pd.DataFrame, cols: list[str], context: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing expected columns for {context}: {missing}")

# This helper function is added to load the list of balanced countries for Exercise 2, which is a new addition to the script.
def load_balanced_countries() -> list[str]:
    countries = pd.read_csv(COUNTRIES_FILE)
    require_columns(countries, ["country"], context="balanced country restriction")
    values = sorted(countries["country"].dropna().astype(str).str.strip().unique())
    if not values:
        raise RuntimeError(f"No countries found in restriction file: {COUNTRIES_FILE}")
    return values


def collapse_colombia_wave3_for_ex2(pref: pd.DataFrame) -> pd.DataFrame:
    """JUDGEMENT CALL: This is a manual adjustment of the row for COL Wave 3 such that we are
    keeping the year 1997 but adding the 1998 surveying respondents (so about
    6000 respondents total) into that same Wave 3 row for Exercise 2. Colombia is the only country 
    in the data that surveyed in two years for Wave 3. 

    The source preference_it_131.csv file is not changed.
    """
    required = ["country", "wave", "year", "n_respondents"] + INDEX_COLS
    require_columns(pref, required, context="COL wave 3 adjustment")

    mask = (pref["country"] == "COL") & (pref["wave"] == 3)
    g = pref.loc[mask].copy()

    if len(g) <= 1:
        return pref

    out = g.iloc[[0]].copy()
    out.loc[:, "year"] = float(pd.to_numeric(g["year"], errors="coerce").min())

    w = pd.to_numeric(g["n_respondents"], errors="coerce").fillna(0).to_numpy(dtype=float)
    out.loc[:, "n_respondents"] = float(np.nansum(w))

    for col in INDEX_COLS:
        x = pd.to_numeric(g[col], errors="coerce").to_numpy(dtype=float)
        good = ~(np.isnan(x) | np.isnan(w))
        if good.any() and np.nansum(w[good]) > 0:
            out.loc[:, col] = float(np.average(x[good], weights=w[good]))
        else:
            out.loc[:, col] = np.nan

    pref_out = pd.concat([pref.loc[~mask], out], ignore_index=True)
    return pref_out.sort_values(["country", "wave", "year"]).reset_index(drop=True)


def run_sweeps(pref: pd.DataFrame, gdp: pd.DataFrame,
               output_to_input: dict[str, str],
               output_prefix: str = "") -> None:
    for output_name, input_col in output_to_input.items():
        print(f"\nProcessing {output_name} (from {input_col})...")

        sweep = compute_sweep(pref, gdp, input_col)
        sweep_name = f"weighted_variance_sweep_{output_prefix}{output_name}.csv"
        sweep_path = EX2_DIR / sweep_name
        sweep.to_csv(sweep_path, index=False)
        print(f"  Saved: {sweep_path} ({len(sweep)} wave x weighting-year rows)")

        baseline = compute_unweighted_baseline(pref, input_col)
        base_name = f"unweighted_variance_{output_prefix}{output_name}.csv"
        base_path = EX2_DIR / base_name
        baseline.to_csv(base_path, index=False)
        print(f"  Saved: {base_path}")


def save_reevaluation_preference_views(pref: pd.DataFrame) -> None:
    base_cols = ["country", "wave", "year", "n_respondents"]

    for suffix, mapping in REEVAL_GROUPS.items():
        cols = base_cols + list(mapping.values())
        require_columns(pref, cols, context=suffix)

        sub = pref[cols].rename(columns={v: k for k, v in mapping.items()})
        out_path = EX2_DIR / f"preference_it_{suffix}.csv"
        sub.to_csv(out_path, index=False)
        print(f"  Saved: {out_path}")


def main():
    print("Loading 131-question preference_it and GDP data...")
    pref = pd.read_csv(PREFERENCE_FILE)
    pref_rows_before = len(pref)
    pref = collapse_colombia_wave3_for_ex2(pref)
    print(f"  Applied manual COL wave 3 collapse before weighting: {pref_rows_before} -> {len(pref)} rows")
    balanced_countries = load_balanced_countries()
    pref = pref[pref["country"].isin(balanced_countries)].copy()
    print(f"  Restricted Exercise 2 sample to {len(balanced_countries)} countries present in waves 3 to 7")
    gdp = pd.read_csv(GDP_FILE)
    gdp["year"] = pd.to_numeric(gdp["year"], errors="coerce")
    gdp = gdp[gdp["year"].between(GDP_YEAR_MIN, GDP_YEAR_MAX)].copy()
    used_years = sorted(gdp.loc[gdp["gdp_nominal"].notna(), "year"].dropna().unique())

    missing_gdp = sorted(set(pref["country"]) - set(gdp["iso3c"]))
    print(f"  {len(missing_gdp)} WVS countries have no GDP series (dropped from weighted calcs): {missing_gdp}")
    # With current GDP input coverage, this prints: 1974-2023. So GDP_YEAR_MIN and GDP_YEAR_MAX are not actually used in the current data, but they are still set to 1974-2025 for future-proofing! 
    if used_years:
        print(f"  GDP weighting years used (observed): {int(used_years[0])}-{int(used_years[-1])}")
    else:
        print("  GDP weighting years used (observed): none")

    require_columns(pref, INDEX_COLS, context="current 8 output indices")
    run_sweeps(pref, gdp, output_to_input={c: c for c in INDEX_COLS})

    print("\nSaving re-evaluation preference_it views...")
    save_reevaluation_preference_views(pref)

    print(f"\nAll balanced-country Exercise 2 (131-question) results saved to {EX2_DIR}/")


if __name__ == "__main__":
    main()
