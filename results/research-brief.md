# Payment Sources and Annual Out-of-Pocket Spending for GLP-1 Receptor Agonists and Tirzepatide

**Medical Expenditure Panel Survey, 2024**

This descriptive analysis included **800 adult users** with at least one recorded target-medicine acquisition among 15,126 sampled adults. Users were included regardless of treatment indication. Prescription payments were aggregated within person over calendar year 2024 and analyzed using the MEPS complex survey design. The source files were released in July and August 2026.

**Key findings:** Self/family payments accounted for 4.80% of total target-medicine payments. Mean annual self/family spending was $343.39, compared with a median of $88.03. An estimated 24.62% of users had no self/family payments, and 9.02% paid more than $1,000.

## 1. Payment sources

| Payment source | Share of all target payments, % (95% CI) | Annual USD per user (95% CI) |
| --- | ---: | ---: |
| Self/family | 4.80 (4.08–5.52) | 343 (286–400) |
| Private insurance | 52.99 (47.72–58.26) | 3,790 (3,313–4,268) |
| Medicare | 31.38 (27.24–35.52) | 2,245 (1,906–2,583) |
| Medicaid | 9.13 (6.41–11.85) | 653 (456–850) |
| TRICARE | 0.54 (0.24–0.85) | 39 (17–61) |
| Other sources | 1.16 (0.62–1.69) | 83 (45–120) |

Payment shares are ratios of survey-weighted source totals to total payments. Source-specific means include all 800 users, including zero payments; payment sources may overlap within individuals.

[Payment-source figure](payment-sources.png).

## 2. Annual self/family spending

| Summary of annual self/family payments | USD (95% CI) |
| --- | ---: |
| Mean | 343.39 (286.39–400.39) |
| Median (50th percentile) | 88.03 (60.00–120.00) |
| 75th percentile | 299.94 (270.00–345.00) |
| 90th percentile | 963.70 (675.00–1,282.96) |

Mean annual self/family spending was $343.39, compared with a median of $88.03, indicating a right-skewed distribution. The 75th and 90th percentiles were $299.94 and $963.70, respectively.

Estimates include zero payments and capture annual spending on the target medicines. Treatment duration was not standardized to 12 months.

## 3. Distribution of annual self/family spending

| Annual self/family payments | Sample users | Weighted share of users, % (95% CI) |
| --- | ---: | ---: |
| $0 | 210 | 24.62 (20.84–28.71) |
| Over $0 through $100 | 228 | 29.28 (25.53–33.25) |
| Over $100 through $500 | 227 | 30.16 (26.00–34.57) |
| Over $500 through $1,000 | 55 | 6.93 (5.05–9.23) |
| Over $1,000 | 80 | 9.02 (6.78–11.69) |

![Annual self/family payment distribution](selfpay-distribution.png)

Annual self/family spending was zero for 24.62% of users and exceeded $1,000 for 9.02%. Dollar bands describe spending levels; affordability relative to household income was not assessed.

## Study limitations

MEPS payment records undergo editing and imputation and do not capture the full claims-adjudication process. Manufacturer rebates to payers are not captured, so reported payments are not net payer costs after rebates. The analysis does not assess benefit eligibility, denial reasons, cost-related nonreceipt of medicines or treatment effectiveness. Insurance comparisons are descriptive associations.

Public-file timing variables do not support linking each medication acquisition to its purchase-month insurance coverage. Age-stratified payments and age-adjusted use estimates are reported in the [supplement](extension-note.md).

## Statistical methods and reproducibility

Estimates used person weights, strata and primary sampling units, with domain estimation retaining the full survey design. Mean and proportion standard errors used Taylor linearization. Proportions used beta confidence intervals; quantiles used the inverse weighted empirical distribution with beta-Woodruff intervals. Descriptive estimates followed the shared AHRQ-based reporting framework, with separate support checks for quantiles; specifications are provided in [Methods](../METHODS.md#reporting-framework).

The payment-distribution analysis was specified after reviewing the initial results and before estimating the quantiles and payment bands. The [analysis sequence](../METHODS.md#analysis-sequence) documents this exploratory development and subsequent reporting revisions.

Independent calculations checked weighted estimates, Taylor standard errors, confidence intervals and quantile points. The distribution analysis includes 9 point/standard-error checks, 9 interval checks and 3 quantile-point checks. [Reproduction instructions](../README.md#reproduce) and aggregate audit outputs are available below.

[Distribution results](payment-distribution.csv) · [Distribution audit](payment-distribution-audit.json) · [Cross-output audit](payment-verification.json) · [Methods](../METHODS.md) · [Sources](../SOURCES.md)
