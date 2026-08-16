## Calculation applied in `exercise2_131.py`

Notation:

- `c`: country
- `w`: WVS wave
- `t`: survey year in `preference_it_131.csv`
- `g`: GDP weighting year
- `j`: one of the 8 index columns

### 1) Manual COL Wave 3 adjustment (for Exercise 2)

Colombia (COL) is the only country that surveyed two years in one wave (Wave 3). Before Exercise 2 calculations, the script manually adjusts COL Wave 3 by combining
the two rows (1997 and 1998) into one row labeled 1997.

Let $R_{COL,3}$ be the set of COL Wave 3 rows in the input file. The adjusted row is:

$$
t^*_{COL,3} = \min_{r\in R_{COL,3}} t_r = 1997
$$

$$
n^*_{COL,3} = \sum_{r\in R_{COL,3}} n_r
$$

Here, $n_r$ is respondent count in each original COL Wave 3 row, and $n^*_{COL,3}$ is the combined respondent count in the adjusted single COL Wave 3 row.

For each index column $j$:

$$
I^*_{COL,3,j}
=
\frac{\sum_{r\in R_{COL,3}} n_r I_{r,j}}{\sum_{r\in R_{COL,3}} n_r}
$$

Here, $I_{r,j}$ is the value of index column $j$ in original COL Wave 3 row $r$, and $I^*_{COL,3,j}$ is the adjusted single-row value after combining 1997 and 1998.

If the denominator is 0 or all relevant values are missing, $I^*_{COL,3,j}=\mathrm{NaN}$.

All other country-wave rows are unchanged.

### 2) GDP-year admissible set

Only nominal GDP values with years in $[1974, 2025]$ are used:

$$
\mathcal{G} = \{(c,g): 1974 \le g \le 2025,\ \mathrm{GDP}_{c,g}\ \text{is observed}\}
$$

The sweep x-axis is the sorted set of observed weighting years:

$$
\mathcal{Y} = \{g : \exists c\ \text{with}\ (c,g)\in\mathcal{G}\}
$$

### 3) Country set used inside each wave-year variance

For wave $w$, index $j$, and weighting year $g$, define the usable country set:

$$
\mathcal{C}_{w,j,g} = \{c : I_{c,w,j}\ \text{observed and}\ \mathrm{GDP}_{c,g}\ \text{observed}\}
$$

The script default is `BALANCED_PANEL=False`, so $\mathcal{C}_{w,j,g}$ is allowed to vary by $g$.
If `BALANCED_PANEL=True`, countries are restricted to those with GDP observed in every year in
$\mathcal{Y}$ before building $\mathcal{C}_{w,j,g}$.

Implementation guardrail: within each wave and index, Exercise 2 expects at most one row per
country after preprocessing; duplicate countries raise an error rather than being silently dropped.

### 4) GDP-weighted mean and population-style weighted variance

For fixed $(w,j,g)$, write $x_c = I_{c,w,j}$ and $q_c = \mathrm{GDP}_{c,g}$ for
$c\in\mathcal{C}_{w,j,g}$.

Weighted mean:

$$
\bar{x}_{w,j,g} = \frac{\sum_{c\in\mathcal{C}_{w,j,g}} q_c x_c}{\sum_{c\in\mathcal{C}_{w,j,g}} q_c}
$$

Population-style weighted variance used in output:

$$
\mathrm{Var}^{(GDP)}_{w,j,g}
=
\frac{\sum_{c\in\mathcal{C}_{w,j,g}} q_c \left(x_c-\bar{x}_{w,j,g}\right)^2}{\sum_{c\in\mathcal{C}_{w,j,g}} q_c}
$$

If fewer than 2 countries are usable or total weight is 0, variance is set to `NaN`.

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

### 6) Unweighted baseline variance by wave

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

### 7) Output Files from "Re-evaluation"
 
The script then writes two convenience views by renaming the 8 indices into 4 generic names:

- `preference_it_reeval_ym_127.csv` maps
  `index_all_ym,index_imf_ym,index_idawb_ym,index_unsc_ym`
  to `index_all,index_imf,index_idawb,index_unsc`.
- `preference_it_reeval_y_86.csv` maps
  `index_all_y,index_imf_y,index_idawb_y,index_unsc_y`
  to `index_all,index_imf,index_idawb,index_unsc`.