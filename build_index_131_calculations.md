## Calculation applied in `build_index_131.py`

Notation:

- `r`: respondent
- `w`: wave
- `c`: country
- `t`: year
- `q`: question

### 1) Missing-value treatment

- If a value is in `{-1, -2, -3, -4, -5}`, it is recoded to `NaN`.
- Additional recodes:

$$
E133 = 4 \rightarrow \mathrm{NaN}, \qquad E134 = 4 \rightarrow \mathrm{NaN}
$$ 

### 2) Wave-based z-score for ordinal questions

For each kept ordinal question `q` in wave `w`:

$$
z_{r,q,w,c,t} = \frac{x_{r,q,w,c,t} - \mu_{w,q,t}}{\sigma_{w,q,t}}
$$

where $\mu_{w,q}$ and $\sigma_{w,q}$ are the sample mean and sample standard deviation of question `q` in wave `w` (pandas default, `ddof=1`, Bessel's Correction)

If `q` is in `REVERSE_CODE_131`, then:

$$
z_{r,q} \leftarrow -z_{r,q}
$$

### 3) Categorical indicator construction and z-score

For indicator `k` with sourced-question set (the set of WVS questions being converted into categorical indicators) $S_k$ and target category set (the set of accepted response codes in the raw WVS data that correspond to a positive indication for that indicator) $C_k$:

- If all sourced questions are missing for respondent `r`, then $I_{r,k}=\mathrm{NaN}$.
- Otherwise:

$$
I_{r,k}=
\begin{cases}
1 & \text{if } \exists s\in S_k: x_{r,s}\in C_k \\
0 & \text{otherwise}
\end{cases}
$$

Then within each wave:

$$
z_{r,k} = \frac{I_{r,k} - \mu_{w,k}}{\sigma_{w,k}}
$$

To answer Jesse's question, this method of z-scoring standardizes any questions that uses a binary indicator. 

### 4) Re-evaluation subset index formulas (8 output indices)

Subsets are defined from post-exclusion Keep>=2 questions:

- `ym` subset: `Re-evaluation in {y, m}` (expected count 122)
- `y` subset: `Re-evaluation == y` (expected count 82)

For subset $s\in\{ym,y\}$ and domain $d\in\{all,imf,idawb,unsc\}$, let $Q_{s,d}$ be the question set (ordinal questions plus applicable derived indicators). An index entry is the average of multiple z-scores. For respondent `r`:

$$
\mathrm{index}_{r,s,d}
=
\frac{1}{|A_{r,s,d}|}
\sum_{q\in A_{r,s,d}} z_{r,q},
\quad
A_{r,s,d}=\{q\in Q_{s,d}: z_{r,q}\text{ is available}\}
$$

This produces exactly:

- `index_all_ym`, `index_imf_ym`, `index_idawb_ym`, `index_unsc_ym`
- `index_all_y`, `index_imf_y`, `index_idawb_y`, `index_unsc_y`

### 5) Collapse to country-wave-year

Final output is grouped by `(country, wave, year)`. Every row contains the average of the respondent indices within a country, wave, year for the different domains/index columns. For each index column `j`:


Let $R_{c,w,t} = \{{r: c(r) = c, w(r) = w, t(r) = t}\}$ where $R_{c,w,t}$ is the set of respondents in country $c$, wave $w$, year $t$. 

$$
\mathrm{preference}_{c,w,t,j}
=
\frac{1}{N_{c,w,t,j}}
\sum_{r\in R_{c,w,t},\ \mathrm{index}_{r,j}\neq\mathrm{NaN}}
\mathrm{index}_{r,j}
$$

`n_respondents` is the non-missing count of the first output index column (`index_all_ym`) inside each `(country, wave, year)` group.
