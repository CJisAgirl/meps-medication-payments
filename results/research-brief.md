# Who paid for GLP-1 medicines and tirzepatide, and what did users pay themselves?

**MEPS 2024 | Recorded payment sources and annual self/family payments**

The population is adults with at least one recorded target-medicine purchase/receipt: **800 sampled users** from 15,126 sampled adults. Records are aggregated within person before survey weighting; repeated fills do not become independent people. The data were released in July/August 2026 and describe 2024.

**Main finding:** self/family payments represented 4.80% of weighted target-medicine payments, while users' annual self/family payments had a mean of $343 and a median of $88.03. An estimated 24.62% of users had zero self/family payments and 9.02% paid more than $1,000. The aggregate payment share and the distribution across people answer different questions; neither establishes affordability.

## 1. Who paid the recorded medicine costs?

| Payment source | Share of all target payments, % (95% CI) | Annual USD per user (95% CI) |
| --- | ---: | ---: |
| Self/family | 4.80 (4.08–5.52) | 343 (286–400) |
| Private insurance | 52.99 (47.72–58.26) | 3,790 (3,313–4,268) |
| Medicare | 31.38 (27.24–35.52) | 2,245 (1,906–2,583) |
| Medicaid | 9.13 (6.41–11.85) | 653 (456–850) |
| TRICARE | Withheld: positive-payer users < 30 | Withheld: positive-payer users < 30 |
| Other sources | 1.16 (0.62–1.69) | 83 (45–120) |

Shares divide each source's weighted total by the weighted total from all sources. They are not the average of each person's copayment percentage. Component means include **all 800 users**, including zeros from that source. Payers may overlap for one person. Existing payer rules are retained; TRICARE has 20 positive-payment users and is withheld. Do not rescale visible shares to 100% or add their confidence bounds.

These are edited/imputed survey payment records, not raw adjudicated claims or a measure of benefit eligibility. Payments exclude manufacturer rebates to payers. [Payment-source figure](payment-sources.png).

## 2. How much did an individual user pay over the year?

| Summary of annual self/family payments | USD (95% CI) |
| --- | ---: |
| Mean | 343.39 (286.39–400.39) |
| Median (50th percentile) | 88.03 (60.00–120.00) |
| 75th percentile | 299.94 (270.00–345.00) |
| 90th percentile | 963.70 (675.00–1,282.96) |

The median is the first dollar amount where the weighted cumulative proportion reaches 50%; the 75th and 90th percentiles use 75% and 90%. Ties mean the percentage strictly above a percentile need not be exactly 50%, 25% or 10%. These thresholds are not average costs among the highest-spending users. The mean exceeds the median because the payment distribution has a substantial upper tail; the mean alone does not describe a typical user.

All summaries include zero self/family payments. They measure recorded calendar-year payments, not the price of 12 continuous treatment months, a monthly copay, or spending on all medical care.

## 3. How common were zero or larger self/family payments?

| Annual self/family payments | Sample users | Weighted share of users, % (95% CI) |
| --- | ---: | ---: |
| $0 | 210 | 24.62 (20.84–28.71) |
| Over $0 through $100 | 228 | 29.28 (25.53–33.25) |
| Over $100 through $500 | 227 | 30.16 (26.00–34.57) |
| Over $500 through $1,000 | 55 | 6.93 (5.05–9.23) |
| Over $1,000 | 80 | 9.02 (6.78–11.69) |

![Annual self/family payment distribution](selfpay-distribution.png)

The five bands are mutually exclusive and include all 800 users; raw counts and weighted percentages need not match by simple division. $1,000 is a presentation cutoff, not a validated financial-hardship threshold. Zero self/family payments do not necessarily mean an insurer paid the entire bill: 1 user has zero recorded total payments across all target records and remains in the denominator.

## What these results can and cannot answer

They describe **observed payment sources and the distribution of dollar payments among recorded users**. They do not identify people who did not obtain a medicine because of price, denial reasons, prescription-benefit terms, income-relative hardship, treatment effectiveness, or a causal effect of insurance. A lower mean in one insurance group would not by itself establish better coverage.

Monthly insurance histories cannot be aligned to each refill's purchase month in these public files. Their unchanged results are now a [coverage-methods appendix](coverage-appendix.md), not evidence of purchase-specific reimbursement. Detailed ages and the age-only use model remain [supplementary analyses](extension-note.md).

## Methods, checks and reproduction

The [analysis methods](../METHODS.md#analysis-sequence) was written after prior results were seen and before the new distribution was estimated. This is not an original preregistration. Use the full stratified, clustered survey design, then the adult-user domain; mean/proportion SEs use Taylor linearization, proportions have beta CIs, and quantiles use inverse weighted CDFs with beta-Woodruff CIs. New mean/proportion rules use the relevant denominator and AHRQ precision categories; quantile support is assessed separately. Legacy results retain their earlier rules. No person is deleted because an estimate is withheld.

The full run includes 16 Python tests and 8 R payment-helper tests; the new distribution has 9 independent point/Taylor-SE checks, 9 interval checks and 3 quantile point checks. Python independently checks weighted bands/quantiles, denominators and reconciliation. Original numerical estimates remain unchanged. See the [reproduction instructions](../README.md#reproduce).


[Distribution results](payment-distribution.csv) · [Distribution audit](payment-distribution-audit.json) · [Cross-output audit](payment-verification.json) · [Methods](../METHODS.md) · [Sources](../SOURCES.md)
