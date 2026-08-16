# WVS Preference Index (131 Build)

This repository builds and documents a preference index using the World Values Survey (WVS). Items are selected when they are preference-relevant and map to one of three policy domains: IMF, IDA/WB, and UNSC, yielding an initial 131-question specification. The implementation then applies exclusion rules and categorical-to-indicator transformations to ensure that the retained items have a defensible scoring structure. The current analysis is restricted primarily to WVS Waves 3 through 7 because earlier waves have limited country coverage and weak representation of world GDP, as shown in the diagnostics output.

## Repository layout

```text
.
├── data/
│   ├── country_year_gdp_nominal.csv
│   ├── WVS_Time_Series_1981-2022_csv_v5_0.csv
│   └── wvs_wave_1-7_questions_categorized-UPDATED.xlsx
│ 
├── results/
│   └── index_131/
│       ├── preference_it_131.csv
│       ├── diagnostics/
│       ├── exercise2/
│       ├── balanced_countries_exercise2/
│       ├── balanced_questions_exercise2/
│       └── individual_question_build/

├── scripts/
│   └── 131_question_build/
│       ├── build_index_131.py
│       ├── exercise2_131.py
│       ├── wvs_data_diagnostics_131.py
│       ├── gdp_coverage_by_wave_131.py
│       ├── visualize_exercise2_131.py
│       ├── individual_question_build/
│       │   └── visualize_individual_exercise2_131.py
│       ├── balance_countries_build_3_to_7/
│       │   ├── balanced_countries_exercise2_131.py
│       │   └── balanced_countries_visualize_exercise2_131.py
│       └── balance_questions_build_3_to_7/
│           ├── balanced_questions_build_index_131.py
│           ├── balanced_questions_exercise2_131.py
│           └── balanced_questions_visualize_exercise2_131.py
├── README.md
├── requirements.txt
├── build_index_131_calculations.md
├── exercise2_131_calculations.md
└── .venv/
```

## Data folder

The `data/` folder holds the raw inputs used across the pipeline.

- `country_year_gdp_nominal.csv`: GDP series used in exercise-2 weighting and coverage checks. Pulled from JMSLab / WorldOrder. 
- `WVS_Time_Series_1981-2022_csv_v5_0.csv`: main WVS respondent-level survey file.
- `wvs_wave_1-7_questions_categorized-UPDATED.xlsx`: question dictionary, and domain coding/categorization file. 

## Main script families

### 1) Core 131-question build

These scripts define the main production pipeline for the 131 preference index.

- `scripts/131_question_build/build_index_131.py`
  - Reads the WVS microdata and question catalog.
  - Recodes missing values to `NaN`.
  - Converts ordinal variables to wave-standardized z-scores.
  - Builds categorical indicator variables from nominal questions and z-scores them within wave.
  - Combines variables into domain-specific indices (`all`, `imf`, `idawb`, `unsc`).
  - Applies the final exclusion logic and produces the country-wave-year composite file.
  - Writes the main output in `results/index_131/preference_it_131.csv`.

- `scripts/131_question_build/exercise2_131.py`
  - Loads the final country-wave-year index file.
  - Applies the Colombia Wave 3 adjustment.
  - Runs the GDP-weighted variance sweep across weighting years.
  - Produces the exercise-2 output tables under `results/index_131/exercise2/`.

- `scripts/131_question_build/wvs_data_diagnostics_131.py`
  - Produces diagnostics on coverage, missingness, country representation, and response counts.
  - Writes files under `results/index_131/diagnostics/`.

- `scripts/131_question_build/gdp_coverage_by_wave_131.py`
  - Checks GDP coverage by country and wave.
  - Writes coverage diagnostics. 

- `scripts/131_question_build/visualize_exercise2_131.py`
  - Produces plots for the exercise-2 GDP variance sweeps. 

  For more info on calculations of `build_index_131.py` and `exercise2_131.py`, see `build_index_131_calculations.md` and `exercise2_131_calculations.md`. 

### 2) Per-question diagnostics

These scripts are meant for question-by-question analysis of exercise-2, and results in a PDF export rather than altering the core production build.

- `scripts/131_question_build/individual_question_build/individual_exercise2_131.py`
  - Mirrors the final retained universe of the main build.
  - Uses the same exclusion logic as the production script.
  - Uses the derived categorical indicators instead of raw source variables.
  - Loops over the retained question components and writes a multi-page PDF on exercise-2 where every page is restricted to one question.
  - Output: `results/index_131/individual_question_build/individual_question_exercise2_131.pdf`

### 3) Balance-check variants

These folders contain the scripts for robustness checks that are parallel to the main pipeline by restricting to a balanced panel of questions or countries. The structure of these scripts are very similar to `build_index_131.py` and `exercise2_131.py` and `visualize_exercise2_131.py`. Note that a similar file to `build_index_131.py` is not needed to build out the analysis on balanced countries. 

- `scripts/131_question_build/balance_countries_build_3_to_7/`
  - Focused on balanced country coverage within waves 3 to 7. 
  - More info on questions included in `diagnostics/countries_present_all_waves_3_to_7.csv`
  - Contains scripts for the balanced-country exercise-2 analysis and visualization.

- `scripts/131_question_build/balance_questions_build_3_to_7/`
  - Focused on balanced question coverage within waves 3 to 7.  
  - More info on questions included in `diagnostics/questions_present_all_waves_3_to_7.csv`
  - Contains scripts for balanced-question build, exercise-2 analysis, and plotting.


## Results folder

The `results/index_131/` directory is the main analysis output area.

- `preference_it_131.csv`: primary collapsed country-wave-year index file.
- `diagnostics/`: data-quality and coverage checks.
- `exercise2/`: GDP-weighted variance sweep outputs.
- `balanced_countries_exercise2/`: outputs for the balanced-country robustness check.
- `balanced_questions_exercise2/`: outputs for the balanced-question robustness check.
- `individual_question_build/`: question-level diagnostic PDF. 
- `figures/`: summary graphs and plotting output.

## Recommended run order

```bash
python3 scripts/131_question_build/build_index_131.py
python3 scripts/131_question_build/exercise2_131.py
python3 scripts/131_question_build/visualize_exercise2_131.py
```

## Method summary

The core build does the following:

1. Reads WVS responses and question metadata.
2. Recodes invalid or missing codes such as `-1` through `-5` to `NaN`.
3. Standardizes ordinal questions within wave using z-scores.
4. Reverses the sign for variables flagged as reverse-coded.
5. Expands nominal/categorical variables into binary indicators, then z-scores those indicators within wave.
6. Builds domain-specific average indices for each respondent.
7. Aggregates respondent-level indices to country-wave-year means.
8. Runs GDP-weighted variance sweeps in the exercise-2 analysis.

## Important implementation notes

- The production logic lives in `build_index_131.py`; the helper scripts in `individual_question_build/` and the balance folders are downstream diagnostics or robustness checks.
- The individual-question PDF script is intentionally aligned with the main build’s exclusions and categorical indicator handling so that the plotted item universe matches the actual analytic universe.
- Excluded variables remain excluded from the diagnostic and final catalog even when they are conceptually relevant; this helps maintain consistency with final index specification.

## Calculation conventions

### Missingness and recoding

If a variable value is one of the standard missing codes (`-1`, `-2`, `-3`, `-4`, `-5`), it is converted to `NaN` before scoring. Some variable-specific recodes are also applied where the original coding requires them.

### Ordinal wave z-score

For a respondent-level value `x_{r,v}` for question `v` in wave `w`, the score is standardized within wave:

$$
z_{r,v} = \frac{x_{r,v} - \mu_{w,v}}{\sigma_{w,v}}
$$

If a variable is in the reverse-coding map, the sign is flipped before aggregation.

### Categorical indicator logic

Categorical variables are not treated as raw values in the final build. Instead, each categorical question is converted to one or more binary indicators and those indicators are standardized within wave before being included in the composite index.

### Domain index construction

For each retained respondent and each domain (`all`, `imf`, `idawb`, `unsc`), the final index is the average of the available standardized variable scores for that respondent in that domain.

### Country-wave-year collapse

After the respondent-level index is computed, the data are collapsed to country-wave-year means. The result is the main output file used by the exercise-2 and diagnostic analyses.

### 5) Additional sweep diagnostics

For each $(w,j,g)$ row, the script also stores:

$$
n\_countries = |\mathcal{C}_{w,j,g}|
$$

$$
	{top1\_share}
=
\max_{c\in\mathcal{C}_{w,j,g}}
\frac{q_c}{\sum_{k\in\mathcal{C}_{w,j,g}} q_k}
$$

So `top1_share` is the GDP share of the largest-weight country in that
wave/index/weighting-year calculation; higher values mean the weighted variance
is more concentrated in one country.

and a boolean flag `balanced_panel`.

### 6) Unweighted baseline variance by wave (implemented in main production build)

For each wave $w$ and index $j$, the script also outputs the ordinary sample variance
across countries (pandas default `var`, i.e. `ddof=1`):

$$
\mathrm{Var}^{(unw)}_{w,j}
=
\frac{1}{N_{w,j}-1}
\sum_{c\in\mathcal{C}_{w,j}}
\left(x_c-\bar{x}_{w,j}\right)^2
$$

where $\mathcal{C}_{w,j}$ is the set of countries with non-missing $I_{c,w,j}$ and
$N_{w,j}=|\mathcal{C}_{w,j}|$.

### 7) Output Files from "Re-evaluation" Check

The script then writes two convenience views by renaming the 8 indices into 4 generic names:

- `preference_it_reeval_ym_127.csv` maps
  `index_all_ym,index_imf_ym,index_idawb_ym,index_unsc_ym`
  to `index_all,index_imf,index_idawb,index_unsc`.
- `preference_it_reeval_y_86.csv` maps
  `index_all_y,index_imf_y,index_idawb_y,index_unsc_y`
  to `index_all,index_imf,index_idawb,index_unsc`.

## Detailed variable configuration (current 131 build)

This section mirrors the active configuration in `scripts/131_question_build/build_index_131.py`.

### Reverse-coded variables

`REVERSE_CODE_131` is the active full list in the current build.

Reverse-coded variables (grouped only for readability):

- `E117`, `E124`, `E225`, `E228`, `E143`
- `E069_02`, `E069_19`, `E069_20`, `E069_21`, `E069_22`
- `E069_26`, `E069_27`, `E069_30`, `E069_40`, `E069_41`, `E069_43`
- `E036`, `E037`, `E039`

- `E007`, `E009`, `E059`
- `E105`, `E106`, `E107`, `E109`, `E110`
- `E123`, `E127`, `E129`, `E129A`, `E129D`
- `E184`, `E185`, `E186`, `E198`
- `E207`, `E208`, `E214`, `E215`, `E216`
- `E233B`
- `E242`, `E243`, `E244`, `E245`, `E246`, `E247`
- `E266`, `E267`, `E290`
- `F114E`, `F136`
- `E069_25`, `E069_28`, `E069_34`, `E069_35`, `E069_42`, `E069_45`
- `E069_46`, `E069_55`, `E069_56`, `E069_57`, `E069_59`, `E069_61`
- `E069_62`, `E069_63`, `E069_65`, `E069_66`, `E069_67`
- `G055`, `G057`, `G059`, `G060`

### Categorical indicator construction

The following source variables are treated as categorical inputs and converted into binary indicators before z-scoring.

- `chose_defence`: source `E001,E002`, category `2`, domain flags: preference=1, IMF=0, IDA/WB=0, UNSC=1
- `chose_growth`: source `E001,E002`, category `1`, domain flags: preference=1, IMF=1, IDA/WB=0, UNSC=0
- `chose_prices`: source `E003,E004`, category `3`, domain flags: preference=1, IMF=1, IDA/WB=0, UNSC=0
- `chose_order`: source `E003,E004`, category `1`, domain flags: preference=1, IMF=0, IDA/WB=0, UNSC=1
- `chose_stable_economy`: source `E005,E006`, category `1`, domain flags: preference=1, IMF=1, IDA/WB=0, UNSC=0
- `chose_growth_B008`: source `B008`, category `2`, domain flags: preference=1, IMF=0, IDA/WB=1, UNSC=0

- `chose_import`: source `E062`, category `1`, domain flags: preference=1, IMF=1, IDA/WB=0, UNSC=0
- `believes_reforms_improve_lives`: source `E204`, category `2`, domain flags: preference=1, IMF=1, IDA/WB=0, UNSC=0
- `who_decide_un_peacekeeping`: source `E135`, category `[2,3]`, domain flags: preference=1, IMF=0, IDA/WB=0, UNSC=1
- `who_decide_un_aid`: source `E137`, category `[2,3]`, domain flags: preference=1, IMF=0, IDA/WB=1, UNSC=0
- `who_decide_un_refugees`: source `E138`, category `[2,3]`, domain flags: preference=1, IMF=0, IDA/WB=0, UNSC=1
- `who_decide_un_human_rights`: source `E139`, category `[2,3]`, domain flags: preference=1, IMF=0, IDA/WB=0, UNSC=1
- `chose_poverty_world`: source `E238,E239`, category `1`, domain flags: preference=1, IMF=0, IDA/WB=1, UNSC=0
- `chose_poverty_country`: source `E240,E241`, category `1`, domain flags: preference=1, IMF=0, IDA/WB=1, UNSC=0

### Excluded variables (`EXCLUDED_VARS_131`)

- `E115`, `E057`, `E111_01`, `E278`

### Data recodes (`RECODE_TO_NAN`)

- `E133`: recode value `4` to `NaN`
- `E134`: recode value `4` to `NaN`

### Using "Re-evaluation" check, the subset indices now generated in build: 

`build_index_131.py` now computes:

- `index_all_ym`, `index_imf_ym`, `index_idawb_ym`, `index_unsc_ym`
- `index_all_y`, `index_imf_y`, `index_idawb_y`, `index_unsc_y`

with expected subset counts (after accounting for categorical indicators and excluded variables): 

- `Re-evaluation in {y,m}`: 127 questions
- `Re-evaluation == y`: 86 questions

## Why variables were adjusted

This section summarizes the rationale for each adjustment category in the current build.

### 1) Exclusions (`EXCLUDED_VARS_131`)

| Variable | Why excluded |
|---|---|
| `E115` | Ambiguous technocracy/democracy interpretation. |
| `E057` | Ambiguous: could reflect dissatisfaction with status quo or support for reform. |
| `E111_01` | Not present as a usable column in the WVS file. |
| `E278` | No single direction is valid across IMF/IDA-WB/UNSC domains. |

### 2) Recodes to missing (`RECODE_TO_NAN`)

| Variable | Recode | Why |
|---|---|---|
| `E133` | `4 -> NaN` | Category 4 is "other answer" (residual category), not ordinal scale content. |
| `E134` | `4 -> NaN` | Same rationale as `E133`. |

### 3) Reverse-coding rationale (`REVERSE_CODE_131`)

- General rule: reverse items whose source scale direction is opposite to the target preference direction used in index construction.
- Confidence items (`E069_*` listed in `REVERSE_CODE_131`) are reversed because source coding is `1 = most confidence`.
- Immigration adjustment: negative-effects items (`G055`, `G057`, `G059`, `G060`) are reversed; positive-effects items are not.

### 4) Categorical-to-binary indicator rationale (`CATEGORICAL_INDICATORS_131`)

- Categorical source variables are converted to binary indicators before z-scoring because their numeric codes are category labels, not an ordinal distance scale.
- `E204` uses category `2` for `believes_reforms_improve_lives` because the conceptual "improves lives" choice is not the middle numeric code.
- UN governance items (`E135`, `E137`, `E138`, `E139`) use category set `[2,3]` to capture UN-only or UN-coordinated preference choices.
