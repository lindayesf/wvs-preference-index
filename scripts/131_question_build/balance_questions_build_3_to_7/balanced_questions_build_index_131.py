"""
build_index_131.py (NEEDS TO BE UPDATED)

Build the 131-question preference index using Keep >= 2
in wvs_wave_1-7_questions_categorized-UPDATED.xlsx.

See README.md for the full reasoning behind every reversal/exclusion/indicator decision
made below - this file only contains the resulting configuration, not the
reasoning.

Run from the project root:
    python3 scripts/131_question_build/build_index_131.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

DATA_DIR = Path("data")
WVS_FILE = DATA_DIR / "WVS_Time_Series_1981-2022_csv_v5_0.csv"
MISSING_CODES = [-1, -2, -3, -4, -5]
ID_COLS = {
    "wave": "S002VS",
    "country_num": "S003",
    "country": "COUNTRY_ALPHA",
    "year": "S020",
}

# Full reverse-code list used in the current 131 build.
REVERSE_CODE_131 = [
    "E117", "E124", "E225", "E228", "E143",
    "E069_02", "E069_19", "E069_20", "E069_21", "E069_22",
    "E069_26", "E069_27", "E069_30", "E069_40", "E069_41", "E069_43",
    "E036", "E037", "E039",
    "E007", "E009", "E059",
    "E105", "E106", "E107", "E109", "E110",
    "E123", "E127", "E129", "E129A", "E129D",
    "E184", "E185", "E186", "E198",
    "E207", "E208", "E214", "E215", "E216",
    "E233B",
    "E242", "E243", "E244", "E245", "E246", "E247",
    "E266", "E267", "E290",
    "F114E", "F136",
    # 17 confidence items coded as 1=most confidence in source data.
    "E069_25", "E069_28", "E069_34", "E069_35", "E069_42", "E069_45",
    "E069_46", "E069_55", "E069_56", "E069_57", "E069_59", "E069_61",
    "E069_62", "E069_63", "E069_65", "E069_66", "E069_67",
    # Negative-effects immigration items are reversed; positive-effects items are not.
    "G055", "G057", "G059", "G060",
]

# THIS IS ADDED FOR BALANCED QUESTIONS: 
QUESTIONS_131_FILE = Path("data") / "wvs_wave_1-7_questions_categorized-UPDATED.xlsx"
BALANCED_QUESTIONS_FILE = (
    Path("results")
    / "index_131"
    / "diagnostics"
    / "questions_present_all_waves_3_to_7.csv"
)

def load_wvs_data(path: Path, variables: list[str],
                  categorical_source_vars: list[str]) -> pd.DataFrame:
    requested = sorted(set(variables) | set(categorical_source_vars))
    available_cols = set(pd.read_csv(path, nrows=0).columns)
    all_needed = [v for v in requested if v in available_cols]
    missing_vars = sorted(set(requested) - set(all_needed))
    if missing_vars:
        print(f"  Note: {len(missing_vars)} variables not found in WVS file and skipped: {missing_vars}")

    usecols = list(ID_COLS.values()) + all_needed
    dtype_map = {c: str for c in usecols}
    df = pd.read_csv(path, usecols=usecols, dtype=dtype_map)

    df = df.rename(columns={v: k for k, v in ID_COLS.items()})

    numeric_cols = ["wave", "year"] + all_needed
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col].isin(MISSING_CODES), col] = np.nan

    return df

def zscore_within_wave(df: pd.DataFrame, variables: list[str],
                       reverse_code: Optional[list[str]] = None) -> pd.DataFrame:
    reverse_code = set(reverse_code or [])
    for var in variables:
        z_col = f"z_{var}"
        df[z_col] = df.groupby("wave")[var].transform(
            lambda x: (x - x.mean()) / x.std() # A respondent's z-score is calculated by taking each respondent's answer (x) and then subtracting the (unweighted) mean (x.mean) of the question, before dividing by the standard deviation (x.std) of the question in a given wave.
        )
        if var in reverse_code:
            df[z_col] = -df[z_col]
    return df

def build_categorical_indicators(df: pd.DataFrame,
                                 indicators: list[dict]) -> pd.DataFrame:
    """Build binary indicators from categorical source variables, then
    z-score each indicator within wave."""
    for ind in indicators:
        name = ind["name"]
        cols = ind["source_vars"]
        category = ind["category"]

        if isinstance(category, list):
            matches = pd.DataFrame({c: df[c].isin(category) for c in cols})
        else:
            matches = pd.DataFrame({c: (df[c] == category) for c in cols})

        all_missing = df[cols].isna().all(axis=1)

        indicator = matches.any(axis=1).astype(float)
        indicator[all_missing] = np.nan
        df[name] = indicator

        z_col = f"z_{name}"
        df[z_col] = df.groupby("wave")[name].transform(
            lambda x: (x - x.mean()) / x.std() # Performs z-score here to standardize against the ordinal variables. 
        )
    return df

RESULTS_131_DIR = Path("results") / "index_131"
RESULTS_131_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Exclusions with rationale documented in README.md
# ---------------------------------------------------------------------------
EXCLUDED_VARS_131 = [
    "E115",     # ambiguous technocracy/democracy reading
    "E057",     # ambiguous: dissatisfaction with status quo vs. alignment with reform
    "E111_01",  # does not exist as a usable column in the WVS data file
    "E278",     # effective vs. democratic - no single correct direction across domains
]

# We can always incorporate these back in later. 

# ---------------------------------------------------------------------------
# Data-quality type fix: category 4 ("other answer") on E133/E134 is a residual
# catch-all, not a continuation of the too-much/too-little ordinal scale so we can just recode as NaN. 
# ---------------------------------------------------------------------------
RECODE_TO_NAN = {
    "E133": [4],
    "E134": [4],
}

# Full categorical -> indicator mapping used in the current 131 build.
CATEGORICAL_INDICATORS_131 = [
    {
        "name": "chose_defence",
        "source_vars": ["E001", "E002"],
        "category": 2,
        "is_preference": True, "is_imf": False, "is_idawb": False, "is_unsc": True,
    },
    {
        "name": "chose_growth",
        "source_vars": ["E001", "E002"],
        "category": 1,
        "is_preference": True, "is_imf": True, "is_idawb": False, "is_unsc": False,
    },
    {
        "name": "chose_prices",
        "source_vars": ["E003", "E004"],
        "category": 3,
        "is_preference": True, "is_imf": True, "is_idawb": False, "is_unsc": False,
    },
    {
        "name": "chose_order",
        "source_vars": ["E003", "E004"],
        "category": 1,
        "is_preference": True, "is_imf": False, "is_idawb": False, "is_unsc": True,
    },
    {
        "name": "chose_stable_economy",
        "source_vars": ["E005", "E006"],
        "category": 1,
        "is_preference": True, "is_imf": True, "is_idawb": False, "is_unsc": False,
    },
    {
        "name": "chose_growth_B008",
        "source_vars": ["B008"],
        "category": 2,
        "is_preference": True, "is_imf": False, "is_idawb": True, "is_unsc": False,
    },
    {
        "name": "chose_import",
        "source_vars": ["E062"],
        "category": 1,  # "goods can be imported freely"
        "is_preference": True, "is_imf": True, "is_idawb": False, "is_unsc": False,
    },
    {
        "name": "believes_reforms_improve_lives",
        "source_vars": ["E204"],
        "category": 2,  # "improve the lives of most people" (natural order 1->3->2, not 1->2->3)
        "is_preference": True, "is_imf": True, "is_idawb": False, "is_unsc": False,
    },
    {
        "name": "who_decide_un_peacekeeping",
        "source_vars": ["E135"],
        "category": [2, 3],  # UN alone, or national govts + UN coordination
        "is_preference": True, "is_imf": False, "is_idawb": False, "is_unsc": True,
    },
    {
        "name": "who_decide_un_aid",
        "source_vars": ["E137"],
        "category": [2, 3],
        "is_preference": True, "is_imf": False, "is_idawb": True, "is_unsc": False,
    },
    {
        "name": "who_decide_un_refugees",
        "source_vars": ["E138"],
        "category": [2, 3],
        "is_preference": True, "is_imf": False, "is_idawb": False, "is_unsc": True,
    },
    {
        "name": "who_decide_un_human_rights",
        "source_vars": ["E139"],
        "category": [2, 3],
        "is_preference": True, "is_imf": False, "is_idawb": False, "is_unsc": True,
    },
    {
        "name": "chose_poverty_world",
        "source_vars": ["E238", "E239"],
        "category": 1,  # "people living in poverty and need"
        "is_preference": True, "is_imf": False, "is_idawb": True, "is_unsc": False,
    },
    {
        "name": "chose_poverty_country",
        "source_vars": ["E240", "E241"],
        "category": 1,
        "is_preference": True, "is_imf": False, "is_idawb": True, "is_unsc": False,
    },
]

# Compiling the questions listed as the categorical indicators (not z-scored
# directly because excluded from the ordinal variable list, but will be z-scored later)
CATEGORICAL_SOURCE_VARS_131 = sorted(set(
    v for ind in CATEGORICAL_INDICATORS_131 for v in ind["source_vars"]
))

def load_keep_sheet_131(path: Path) -> pd.DataFrame:
    """Load the 131-core QuestionsCode catalog.

    Starts from Keep >= 2 and then applies explicit exclusions. This single
    kept-question universe is used for both core (142) and re-evaluation subsets (137).
    """
    raw = pd.read_excel(path, sheet_name="QuestionsCode", header=0)
    raw = raw.rename(columns={
        "Variable": "variable",
        "Title": "title",
        "Preference ": "is_preference",
        "IMF": "is_imf",
        "IDA/WB": "is_idawb",
        "UNSC": "is_unsc",
        "Confidence": "confidence",
        "Keep": "keep_score",
        "Re-evaluation": "re_evaluation",
    })
    raw = raw.dropna(subset=["variable"]).reset_index(drop=True)

    # Generates clean boolean flags for domain columns
    for col in ["is_preference", "is_imf", "is_idawb", "is_unsc"]:
        raw[col] = raw[col].fillna(0).astype(float).astype(bool) 
    raw["re_evaluation"] = raw["re_evaluation"].astype(str).str.strip().str.lower()

    kept = raw[raw["keep_score"] >= 2].copy()
    kept = kept[~kept["variable"].isin(EXCLUDED_VARS_131)].reset_index(drop=True)

    return kept[["variable", "title", "is_preference", "is_imf", "is_idawb",
                 "is_unsc", "confidence", "re_evaluation"]]


def build_domain_subset_catalog(subset_questions: pd.DataFrame,
                                categorical_source_vars: list[str],
                                categorical_indicators: list[dict]) -> pd.DataFrame: # this creates the correct subset catalog that combines the ordinal variables and the indicator variables, and then adds the domain flags for each variable.
    """Build a domain catalog (all/imf/idawb/unsc) for a subset definition.

    Categorical source variables are excluded as direct ordinal items, and
    corresponding derived indicators are included using indicator domain flags.
    """
    subset_questions = subset_questions.copy()
    subset_vars = set(subset_questions["variable"])

    ordinal_catalog = subset_questions[
        ~subset_questions["variable"].isin(categorical_source_vars)
    ][["variable", "is_imf", "is_idawb", "is_unsc"]].copy()

    indicator_rows = []
    for ind in categorical_indicators:
        if any(v in subset_vars for v in ind["source_vars"]):
            indicator_rows.append({
                "variable": ind["name"],
                "is_imf": ind["is_imf"],
                "is_idawb": ind["is_idawb"],
                "is_unsc": ind["is_unsc"],
            })
    indicator_catalog = pd.DataFrame(indicator_rows)

    full_catalog = pd.concat([ordinal_catalog, indicator_catalog], ignore_index=True)
    for col in ["is_imf", "is_idawb", "is_unsc"]:
        full_catalog[col] = full_catalog[col].fillna(False).astype(bool)
    return full_catalog

def recode_to_nan(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the E133/E134 'other answer' -> NaN fix before z-scoring."""
    for var, bad_values in RECODE_TO_NAN.items():
        if var in df.columns:
            df.loc[df[var].isin(bad_values), var] = np.nan
    return df


def load_balanced_question_set(path: Path) -> set[str]:
    q = pd.read_csv(path)
    if "question" not in q.columns:
        raise RuntimeError(f"Expected 'question' column in balanced question file: {path}")
    values = set(q["question"].dropna().astype(str).str.strip())
    if not values:
        raise RuntimeError(f"No questions found in balanced question file: {path}")
    return values

def build_composite_indices_131(df: pd.DataFrame, catalog: pd.DataFrame,
                                  suffix: str = "") -> pd.DataFrame:
    """Build respondent-level composite indices from a pre-built
    catalog (ordinal vars + indicator vars combined),
    using the current 131 catalog assembly."""
    def z_cols_for(mask):
        vars_ = catalog.loc[mask, "variable"].tolist()
        return [f"z_{v}" for v in vars_]

    index_defs = {
        f"index_all{suffix}": catalog["variable"].notna(),
        f"index_imf{suffix}": catalog["is_imf"],
        f"index_idawb{suffix}": catalog["is_idawb"],
        f"index_unsc{suffix}": catalog["is_unsc"],
        f"index_preference_only{suffix}": catalog["is_preference"],
        f"index_preference_plus_others{suffix}": (
            catalog["is_preference"] | catalog["is_imf"] |
            catalog["is_idawb"] | catalog["is_unsc"]
        ),
    }

    for name, mask in index_defs.items():
        cols = z_cols_for(mask)
        cols = [c for c in cols if c in df.columns]
        df[name] = df[cols].mean(axis=1, skipna=True)

    return df


def build_domain_indices(df: pd.DataFrame, catalog: pd.DataFrame, suffix: str) -> pd.DataFrame:
    """Build exactly four domain-style indices for a subset: all/imf/idawb/unsc."""
    index_defs = {
        f"index_all_{suffix}": catalog["variable"].notna(),
        f"index_imf_{suffix}": catalog["is_imf"],
        f"index_idawb_{suffix}": catalog["is_idawb"],
        f"index_unsc_{suffix}": catalog["is_unsc"],
    }

    for name, mask in index_defs.items():
        vars_ = catalog.loc[mask, "variable"].tolist()
        cols = [f"z_{v}" for v in vars_ if f"z_{v}" in df.columns]
        df[name] = df[cols].mean(axis=1, skipna=True)

    return df


def collapse_to_country_wave(df: pd.DataFrame, index_cols: list) -> pd.DataFrame:
    agg = df.groupby(["country", "wave", "year"], as_index=False).agg(
        n_respondents=(index_cols[0], "count"),
        **{c: (c, "mean") for c in index_cols},
    )
    return agg.sort_values(["country", "wave", "year"]).reset_index(drop=True)


def main():
    print("Loading Keep sheet...")
    keep131 = load_keep_sheet_131(QUESTIONS_131_FILE)
    balanced_questions = load_balanced_question_set(BALANCED_QUESTIONS_FILE)
    keep131 = keep131[keep131["variable"].isin(balanced_questions)].copy()

    # Keep indicator definitions only when all their source questions are in the
    # balanced question set.
    active_indicators = [
        ind for ind in CATEGORICAL_INDICATORS_131
        if all(v in balanced_questions for v in ind["source_vars"])
    ]
    active_categorical_source_vars = sorted(
        set(v for ind in active_indicators for v in ind["source_vars"])
    )

    ym_questions = keep131[keep131["re_evaluation"].isin(["y", "m"])].copy()
    y_questions = keep131[keep131["re_evaluation"] == "y"].copy()

    ordinal_vars = [v for v in keep131["variable"].tolist()
                     if v not in active_categorical_source_vars]
    ym_ordinal_vars = [v for v in ym_questions["variable"].tolist()
                       if v not in active_categorical_source_vars]
    y_ordinal_vars = [v for v in y_questions["variable"].tolist()
                      if v not in active_categorical_source_vars]

    print(f"  Restricted to balanced question list: {len(keep131)} questions")
    print(f"  {len(ordinal_vars)} ordinal + {len(active_categorical_source_vars)} categorical source vars")
    print(f"  {len(active_indicators)} active categorical indicators")
    print(f"  Re-evaluation y|m question count: {len(ym_questions)}")
    print(f"  Re-evaluation y-only question count: {len(y_questions)}")

    print("Loading WVS data (this can take a minute)...")
    all_needed_vars = sorted(
        set(ordinal_vars)
        | set(ym_ordinal_vars)
        | set(y_ordinal_vars)
        | set(active_categorical_source_vars)
    )
    df = load_wvs_data(WVS_FILE, all_needed_vars, active_categorical_source_vars)
    print(f"  Loaded {len(df):,} respondents")

    print("Applying E133/E134 'other answer' -> NaN fix...")
    df = recode_to_nan(df)

    print("Z-scoring ordinal questions within wave...")
    df = zscore_within_wave(df, ordinal_vars, reverse_code=REVERSE_CODE_131)

    print(f"Building categorical -> indicator variables ({len(active_indicators)} total)...")
    df = build_categorical_indicators(df, active_indicators)

    # Build the ordinal-only catalog (indicator catalog rows added separately
    # since they carry their own domain flags from CATEGORICAL_INDICATORS_131,
    # not from the spreadsheet)
    ordinal_catalog = keep131[keep131["variable"].isin(ordinal_vars)].copy()
    indicator_catalog = pd.DataFrame([
        {
            "variable": ind["name"],
            "is_preference": ind["is_preference"],
            "is_imf": ind["is_imf"],
            "is_idawb": ind["is_idawb"],
            "is_unsc": ind["is_unsc"],
            "confidence": "y",
        }
        for ind in active_indicators
    ])
    catalog_131 = pd.concat([ordinal_catalog, indicator_catalog], ignore_index=True)

    print("Building composite indices (131-question version)...")
    df = build_composite_indices_131(df, catalog_131)

    # Re-evaluation subset indices:
    # - *_ym uses the same 131-core universe with Re-evaluation in {y, m}
    # - *_y  uses the same 131-core universe with Re-evaluation == y
    print("Building re-evaluation subset indices...")
    print(f"  Re-evaluation y|m questions: {len(ym_questions)}")
    print(f"  Re-evaluation y-only questions: {len(y_questions)}")

    catalog_ym = build_domain_subset_catalog(
        ym_questions,
        active_categorical_source_vars,
        active_indicators,
    )
    catalog_y = build_domain_subset_catalog(
        y_questions,
        active_categorical_source_vars,
        active_indicators,
    )

    df = build_domain_indices(df, catalog_ym, suffix="ym")
    df = build_domain_indices(df, catalog_y, suffix="y")

    index_cols_131 = [
        "index_all_ym", "index_imf_ym", "index_idawb_ym", "index_unsc_ym",
        "index_all_y", "index_imf_y", "index_idawb_y", "index_unsc_y",
    ]

    print("Collapsing to country x wave x year (131-question preference_it)...")
    preference_it_131 = collapse_to_country_wave(df, index_cols_131)
    if preference_it_131.duplicated(subset=["country", "wave", "year"]).any():
        raise RuntimeError("Pause: found duplicate country-wave-year rows after collapse.")
    print(f"  Built {len(preference_it_131)} country-wave-year rows (8 index versions)")

    out_path = RESULTS_131_DIR / "preference_it_131.csv"
    preference_it_131.to_csv(out_path, index=False)
    print(f"Saved: {out_path} ({len(preference_it_131)} country-wave-year rows, "
          f"{len(preference_it_131.columns)} columns)")


if __name__ == "__main__":
    main()
