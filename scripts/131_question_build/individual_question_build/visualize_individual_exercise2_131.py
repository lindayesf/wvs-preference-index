"""Individual-question Exercise 2 PDF export for the 131-question build.

This script mirrors the main 131-question build's final retained universe:
excluded variables are not included in the per-question catalog, and the derived
categorical indicators are used in place of their raw source variables.

It loops over the final retained question components in memory, builds a
temporary one-question index for each component, and appends a 2x2 Exercise 2
figure to a single multi-page PDF. It does not write per-question CSV files.
"""

import os
from pathlib import Path
from typing import Dict, List
import runpy

MPL_CACHE_DIR = Path(__file__).resolve().parents[2] / ".matplotlib_cache"
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
REPO_ROOT = SCRIPT_DIR.parents[2]
RESULTS_DIR = REPO_ROOT / "results" / "index_131" / "individual_question_build"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = RESULTS_DIR / "individual_question_exercise2_131.pdf"

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]


def _load_namespace(path: Path) -> Dict[str, object]:
	return runpy.run_path(str(path), run_name="__copilot_helpers__")


BASE_NS = _load_namespace(ROOT_DIR / "build_index_131.py")
EX2_NS = _load_namespace(ROOT_DIR / "exercise2_131.py")

DATA_DIR = BASE_NS["DATA_DIR"]
WVS_FILE = BASE_NS["WVS_FILE"]
QUESTIONS_131_FILE = BASE_NS["QUESTIONS_131_FILE"]
REVERSE_CODE_131 = BASE_NS["REVERSE_CODE_131"]
EXCLUDED_VARS_131 = BASE_NS["EXCLUDED_VARS_131"]
CATEGORICAL_INDICATORS_131 = BASE_NS["CATEGORICAL_INDICATORS_131"]
CATEGORICAL_SOURCE_VARS_131 = BASE_NS["CATEGORICAL_SOURCE_VARS_131"]
load_wvs_data = BASE_NS["load_wvs_data"]
recode_to_nan = BASE_NS["recode_to_nan"]
build_categorical_indicators = BASE_NS["build_categorical_indicators"]
zscore_within_wave = BASE_NS["zscore_within_wave"]

compute_sweep = EX2_NS["compute_sweep"]
GDP_FILE = DATA_DIR / "country_year_gdp_nominal.csv"
GDP_YEAR_MIN = EX2_NS["GDP_YEAR_MIN"]
GDP_YEAR_MAX = EX2_NS["GDP_YEAR_MAX"]
BALANCED_PANEL = EX2_NS["BALANCED_PANEL"]

DOMAIN_COLS = ["index_all", "index_imf", "index_idawb", "index_unsc"]
DOMAIN_TITLES = {
	"index_all": "All",
	"index_imf": "IMF",
	"index_idawb": "IDA/WB",
	"index_unsc": "UNSC",
}

DOMAIN_FLAG_BY_COL = {
	"index_all": "is_preference",
	"index_imf": "is_imf",
	"index_idawb": "is_idawb",
	"index_unsc": "is_unsc",
}


def collapse_colombia_wave3_for_question(pref: pd.DataFrame, index_cols: List[str]) -> pd.DataFrame:
	"""Collapse the COL Wave 3 split-year rows into a single row."""
	mask = (pref["country"] == "COL") & (pref["wave"] == 3)
	g = pref.loc[mask].copy()

	if len(g) <= 1:
		return pref

	out = g.iloc[[0]].copy()
	out.loc[:, "year"] = float(pd.to_numeric(g["year"], errors="coerce").min())

	w = pd.to_numeric(g["n_respondents"], errors="coerce").fillna(0).to_numpy(dtype=float)
	out.loc[:, "n_respondents"] = float(np.nansum(w))

	for col in index_cols:
		x = pd.to_numeric(g[col], errors="coerce").to_numpy(dtype=float)
		good = ~(np.isnan(x) | np.isnan(w))
		if good.any() and np.nansum(w[good]) > 0:
			out.loc[:, col] = float(np.average(x[good], weights=w[good]))
		else:
			out.loc[:, col] = np.nan

	pref_out = pd.concat([pref.loc[~mask], out], ignore_index=True)
	return pref_out.sort_values(["country", "wave", "year"]).reset_index(drop=True)


def load_keep_sheet_131(path: Path) -> pd.DataFrame:
	"""Load the 131-core QuestionsCode catalog."""
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

	for col in ["is_preference", "is_imf", "is_idawb", "is_unsc"]:
		raw[col] = raw[col].fillna(0).astype(float).astype(bool)
	raw["re_evaluation"] = raw["re_evaluation"].astype(str).str.strip().str.lower()

	kept = raw[raw["keep_score"] >= 2].copy()
	kept = kept[~kept["variable"].isin(EXCLUDED_VARS_131)].reset_index(drop=True)

	return kept[["variable", "title", "is_preference", "is_imf", "is_idawb", "is_unsc", "confidence", "re_evaluation"]]


def collapse_to_country_wave(df: pd.DataFrame, index_cols: List[str]) -> pd.DataFrame:
	agg = df.groupby(["country", "wave", "year"], as_index=False).agg(
		n_respondents=(index_cols[0], "count"),
		**{c: (c, "mean") for c in index_cols},
	)
	return agg.sort_values(["country", "wave", "year"]).reset_index(drop=True)


def build_question_catalog(keep131: pd.DataFrame) -> pd.DataFrame:
	keep_vars = set(keep131["variable"].dropna().tolist())

	ordinal_rows = keep131[
		~keep131["variable"].isin(CATEGORICAL_SOURCE_VARS_131)
	][["variable", "title", "is_preference", "is_imf", "is_idawb", "is_unsc"]].copy()

	indicator_rows = []
	for ind in CATEGORICAL_INDICATORS_131:
		if any(v in keep_vars for v in ind["source_vars"]):
			indicator_rows.append({
				"variable": ind["name"],
				"title": ind["name"],
				"is_preference": ind["is_preference"],
				"is_imf": ind["is_imf"],
				"is_idawb": ind["is_idawb"],
				"is_unsc": ind["is_unsc"],
			})

	catalog = pd.concat([ordinal_rows, pd.DataFrame(indicator_rows)], ignore_index=True)
	if len(catalog) != 124:
		raise RuntimeError(f"Expected 124 final catalog components after categorical conversion, got {len(catalog)}")
	catalog["display_title"] = catalog["title"].fillna(catalog["variable"])
	return catalog


def prepare_question_frame(df: pd.DataFrame, item: pd.Series) -> pd.DataFrame:
	z_col = f"z_{item['variable']}"
	if z_col not in df.columns:
		return pd.DataFrame(columns=["country", "wave", "year", "index_all", "index_imf", "index_idawb", "index_unsc"])

	out = df[["country", "wave", "year", z_col]].copy()
	out = out.rename(columns={z_col: "index_all"})
	out["index_imf"] = out["index_all"] if bool(item["is_imf"]) else np.nan
	out["index_idawb"] = out["index_all"] if bool(item["is_idawb"]) else np.nan
	out["index_unsc"] = out["index_all"] if bool(item["is_unsc"]) else np.nan
	return out


def zscore_single_question(df: pd.DataFrame, variable: str) -> pd.DataFrame:
	"""Z-score one question within wave and return the derived column only."""
	return zscore_within_wave(df.copy(), [variable], reverse_code=REVERSE_CODE_131)


def plot_question_page(pdf: PdfPages, question_num: int, item: pd.Series,
					   sweep: pd.DataFrame) -> None:
	fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
	axes = axes.flatten()

	if sweep.empty:
		for ax, domain in zip(axes, DOMAIN_COLS):
			ax.set_title(DOMAIN_TITLES[domain])
			ax.axis("off")
			ax.text(0.5, 0.5, "Variable not present in WVS data", ha="center", va="center")

		fig.suptitle(
			f"Question {question_num}/131: {item['variable']}\n"
			f"{item['display_title']}",
			fontsize=12,
			y=0.99,
		)
		plt.tight_layout(rect=[0, 0, 1, 0.96])
		pdf.savefig(fig, dpi=300)
		plt.close(fig)
		return

	for ax, domain in zip(axes, DOMAIN_COLS):
		if not bool(item[DOMAIN_FLAG_BY_COL[domain]]):
			ax.set_title(DOMAIN_TITLES[domain])
			ax.axis("off")
			ax.text(0.5, 0.5, "Not included in this domain", ha="center", va="center")
			continue

		domain_sweep = sweep[sweep["wave"].between(3, 7)].copy()

		for wave, group in domain_sweep.groupby("wave"):
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
	fig.suptitle(
		f"Question {question_num}/131: {item['variable']}\n"
		f"{item['display_title']}",
		fontsize=12,
		y=0.99,
	)
	plt.tight_layout(rect=[0, 0, 1, 0.96])
	pdf.savefig(fig, dpi=300)
	plt.close(fig)


def main() -> None:
	print("Loading 131-question catalog and WVS data...")
	keep131 = load_keep_sheet_131(QUESTIONS_131_FILE)
	catalog = build_question_catalog(keep131)

	needed_vars = sorted(keep131["variable"].tolist())

	df = load_wvs_data(WVS_FILE, needed_vars)
	df = recode_to_nan(df)
	df = build_categorical_indicators(df, CATEGORICAL_INDICATORS_131)

	gdp = pd.read_csv(GDP_FILE)
	gdp["year"] = pd.to_numeric(gdp["year"], errors="coerce")
	gdp = gdp[gdp["year"].between(GDP_YEAR_MIN, GDP_YEAR_MAX)].copy()

	indicator_names = {ind["name"] for ind in CATEGORICAL_INDICATORS_131}
	print(f"  Building temporary question-level sweeps for {len(catalog)} components...")
	with PdfPages(PDF_PATH) as pdf:
		for question_num, (_, item) in enumerate(catalog.iterrows(), start=1):
			var = item["variable"]
			if var in indicator_names:
				question_pref = prepare_question_frame(df, item)
			elif var not in df.columns:
				question_pref = pd.DataFrame(columns=["country", "wave", "year", "index_all", "index_imf", "index_idawb", "index_unsc"])
			else:
				question_df = df[["country", "wave", "year", var]].copy()
				question_df = zscore_single_question(question_df, var)
				question_pref = prepare_question_frame(question_df, item)
			question_pref = collapse_to_country_wave(question_pref, index_cols=DOMAIN_COLS)
			question_pref = collapse_colombia_wave3_for_question(question_pref, DOMAIN_COLS)
			question_sweep = compute_sweep(question_pref, gdp, "index_all", balanced=BALANCED_PANEL)
			plot_question_page(pdf, question_num, item, question_sweep)

	print(f"Saved PDF: {PDF_PATH}")


if __name__ == "__main__":
	main()
