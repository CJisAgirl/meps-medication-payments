# Supplementary age, insurance and payment analyses

**MEPS 2024 · Follow-up specified 11 October 2026**

This extension examines finer age groups, monthly insurance histories and recorded payment sources, including the limits of linking insurance to individual medicine acquisitions. The [analysis methods](../METHODS.md#supplementary-analyses) records choices after seeing the first analysis and age-by-insurance counts, before estimating follow-up outcomes. It is not an original preregistration. The first-run estimates remain available unchanged.

The [current main report](research-brief.md) answers who paid and how self/family payments were distributed. The analyses below are supplementary. Legacy gates are retained for reproducibility, not asserted to be universally appropriate; withheld values are not deleted people.

## 1. Detailed age and annual coverage

The five age bins and reporting gates were fixed before extension outcome estimation. “Any private” retains the MEPS convention including TRICARE/CHAMPVA and mixed public/private coverage. OOP is annual self/family spending among observed users, including zero payments. Confidence intervals are survey-design intervals; blank/withheld results are not zero.

![Detailed age and annual insurance estimates](detailed-age.png)

| Age | Annual coverage | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | --- | ---: | ---: | ---: |
| 18-34 | All coverage | 41 / 3163 | 1.45 (1.03–2.03) | Withheld: RSE > 30% |
| 18-34 | Any private incl. TRICARE | 24 / 2028 | Withheld: user n < 30 | Withheld: user n < 30 |
| 18-34 | Public only | 16 / 758 | Withheld: user n < 30 | Withheld: user n < 30 |
| 18-34 | Uninsured all year | 1 / 377 | Withheld: user n < 30 | Withheld: user n < 30 |
| 35-49 | All coverage | 126 / 3361 | 3.68 (3.01–4.50) | 175 (98–252) |
| 35-49 | Any private incl. TRICARE | 97 / 2357 | 4.12 (3.26–5.18) | 200 (107–293) |
| 35-49 | Public only | 26 / 604 | Withheld: user n < 30 | Withheld: user n < 30 |
| 35-49 | Uninsured all year | 3 / 400 | Withheld: user n < 30 | Withheld: user n < 30 |
| 50-64 | All coverage | 310 / 3652 | 8.63 (7.49–9.93) | 326 (237–414) |
| 50-64 | Any private incl. TRICARE | 214 / 2581 | 8.68 (7.36–10.23) | 355 (247–463) |
| 50-64 | Public only | 95 / 790 | 12.02 (9.48–15.13) | Withheld: RSE > 30% |
| 50-64 | Uninsured all year | 1 / 281 | Withheld: user n < 30 | Withheld: user n < 30 |
| 65-74 | All coverage | 221 / 2815 | 8.35 (7.23–9.64) | 514 (370–658) |
| 65-74 | Any private incl. TRICARE | 104 / 1192 | 8.80 (7.21–10.70) | 405 (251–559) |
| 65-74 | Public only | 117 / 1613 | 8.03 (6.51–9.87) | 614 (374–855) |
| 65-74 | Uninsured all year | 0 / 10 | Withheld: adult n < 100 | Withheld: adult n < 100 |
| 75+ | All coverage | 102 / 2135 | 4.93 (4.01–6.05) | 549 (376–722) |
| 75+ | Any private incl. TRICARE | 33 / 751 | 4.21 (2.93–6.03) | Withheld: RSE > 30% |
| 75+ | Public only | 69 / 1379 | 5.37 (4.20–6.85) | 611 (384–838) |
| 75+ | Uninsured all year | 0 / 5 | Withheld: adult n < 100 | Withheld: adult n < 100 |

## 2. Monthly histories, without inventing purchase dates

The unchanged monthly tables and figure are now in the [coverage-methods appendix](coverage-appendix.md). They are not evidence of purchase-specific reimbursement.

## 3. Actual recorded payment sources

Aggregate all ten edited/imputed source-payment variables over each person's target-drug records. The six displayed components are exhaustive before suppression. “Other” combines VA/CHAMPVA, other federal, state/local, workers' compensation and other insurance. TRICARE is shown separately even though annual INSCOV24 groups it with any-private coverage.

The denominator for annual component means is **all observed adult users**, including those with zero payment from that source; it is not only people paid for by that payer. The share denominator is weighted total target-drug payments. Source-specific outputs require at least 30 users with positive payment from that component in addition to the original precision gate. Positive-payer users can overlap across sources.

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
| Self/family | 590 | 343 (286–400) | 4.80 (4.08–5.52) |
| Private insurance | 351 | 3,790 (3,313–4,268) | 52.99 (47.72–58.26) |
| Medicare | 307 | 2,245 (1,906–2,583) | 31.38 (27.24–35.52) |
| Medicaid | 102 | 653 (456–850) | 9.13 (6.41–11.85) |
| TRICARE | 20 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Other sources | 41 | 83 (45–120) | 1.16 (0.62–1.69) |

![Payment sources, all adult users](payment-sources.png)

Do not add displayed confidence bounds or renormalize visible components to 100% when another component is withheld. A payment of zero does not establish no drug benefit or a denial. Payments exclude manufacturer rebates to payers; medicine names and amounts may be edited/imputed. These are survey records, not raw adjudicated claims.

## 4. Age-adjusted association: observed use only

Use a survey-weighted quasibinomial model with a natural cubic spline of age (3 df, internal knots [44, 65], boundaries 18 and top-coded 85) and annual coverage. There is no age-by-coverage interaction. Standardize predictions to the combined survey-weighted age distribution of 14,053 any-private/public-only adults (795 users). Uninsured adults are outside this model, not dropped from the original descriptive estimates.

The support diagnostic is recorded in the audit and support table. Small cells can be withheld as standalone estimates while still contributing to a pooled model that explicitly imposes a smooth common age relationship, if the prespecified model-support gate passes. This adds modeling assumptions; it does not create more observations.

| Group or comparison | Metric | Estimate (95% CI) |
| --- | --- | ---: |
| Any private incl. TRICARE | age_adjusted_use_pct | 4.99 (4.51–5.51) |
| Public only | age_adjusted_use_pct | 6.02 (5.19–6.97) |
| Public only minus any private | age_adjusted_difference_pp | 1.03 (-0.01–2.08) |

The signed difference is public-only minus any-private, in percentage points. Its interval uses the covariance of both margins, rather than assuming they are independent. The RSE gate applies to the margins, not to a signed contrast near zero. Intervals use the residual design degrees of freedom (155); margin intervals use a logit-delta transformation. Model convergence, rank, support and finite covariance are checked. survey::svypredmeans combines model and standardized-prediction distribution variance components; both are independently reconstructed when the model is estimated.

Only age is adjusted. Disease burden, indication, income, drug mix, coverage timing and selection remain potential differences. No claim is made about how much of the crude gap age “explains.” An adjusted spending model is not fitted; the distribution of spending and selection into observed use need a separate plan.

## Validation and reproduction

Run `python3 run.py` from the project directory to reproduce both the original analysis and this extension. The extension adds six Python unit tests (12 across the original and extension analyses, plus four SAS-input Python tests), 120 independently recomputed point estimates and Taylor SEs, manual predictive-margin point/covariance checks, and an intercept-only comparison against crude survey means. Payment components reconcile to event totals and independently to SQL/person sums. The original 71 checks also remain in the full run.

Read [cohort audit](extension-cohort-audit.json), [design audit](extension-design-audit.json), [aggregate results](extension-estimates.csv), [model support](age-adjustment-support.csv), [adjusted use](age-adjusted-use.csv). The extension contains 122 descriptive result rows: 59 reportable and 63 withheld under fixed gates.

Primary documentation: [HC-256 insurance](https://meps.ahrq.gov/data_stats/download_data/pufs/h256/h256doc.shtml), [HC-254A timing/payments](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml), [survey predictive margins](https://r-survey.r-forge.r-project.org/pkgdown/docs/reference/svypredmeans.html).


## Appendix: payer components by age

Every age-specific mean uses all users in that age group, including zero payments from the particular source. Apply contributor and precision gates separately to each component; the underlying people need not be distinct across payment sources.

### 18-34

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
| Self/family | 23 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Private insurance | 24 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Medicare | 1 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Medicaid | 16 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| TRICARE | 0 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Other sources | 1 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |

### 35-49

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
| Self/family | 97 | 175 (98–252) | 2.66 (1.50–3.82) |
| Private insurance | 89 | 5,063 (3,968–6,158) | 76.98 (67.39–86.57) |
| Medicare | 6 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Medicaid | 26 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| TRICARE | 1 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Other sources | 5 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |

### 50-64

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
| Self/family | 221 | 326 (237–414) | 4.34 (3.23–5.45) |
| Private insurance | 190 | 5,356 (4,554–6,158) | 71.30 (64.54–78.06) |
| Medicare | 51 | 788 (454–1,123) | 10.49 (6.30–14.68) |
| Medicaid | 53 | 931 (547–1,315) | 12.39 (7.35–17.43) |
| TRICARE | 10 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Other sources | 12 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |

### 65-74

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
| Self/family | 173 | 514 (370–658) | 6.97 (5.11–8.84) |
| Private insurance | 40 | 1,531 (826–2,235) | 20.79 (11.95–29.63) |
| Medicare | 165 | 4,979 (4,151–5,806) | 67.61 (58.59–76.64) |
| Medicaid | 5 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| TRICARE | 6 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Other sources | 13 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |

### 75+

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
| Self/family | 76 | 549 (376–722) | 6.87 (4.87–8.87) |
| Private insurance | 8 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Medicare | 84 | 6,859 (5,192–8,527) | 85.89 (79.88–91.89) |
| Medicaid | 2 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| TRICARE | 3 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Other sources | 10 | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
