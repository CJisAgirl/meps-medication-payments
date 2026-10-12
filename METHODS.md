# Survey Analysis Methods

## Cohort and medication definition

Link the MEPS full-year person file to prescribed medicines using DUPERSID. Build the full positive-weight survey design before selecting adults and observed medication users. People without a target record remain in observed-use denominators; spending summaries are conditional on observed use and retain zero payments.

The primary medication definition uses exact normalized generic names for GLP-1 receptor agonists and tirzepatide, excluding insulin combinations. Brand names are checked against an explicit whitelist; missing generic names and conflicting labels are treated separately. An insulin combination is not reclassified by a brand fallback. The mapping audit preserves observed labels and decisions. Indication, authenticity and compounded status cannot be established from these fields. A recognized-brand sensitivity rebuilds both user flags and spending from the restricted events.

Aggregate distinct prescription records within each person using SQL. Reconcile ten source-payment fields to the recorded total within the cent-rounding tolerance, and collapse them to self/family, private insurance, Medicare, Medicaid, TRICARE and other sources. Unresolved negative payment codes, duplicate event IDs and inconsistent totals stop preparation.

## Payment distribution

The main estimands are source shares of total target-medicine payments, mean annual payments per user, weighted self/family payment quantiles and the proportions in fixed dollar bands. Source shares are ratios of weighted sums, not averages of individual copayment percentages. A source-specific mean includes every observed user, including those with zero payment from that source.

Annual amounts are nominal 2024 dollars. Zero, over zero through $100, over $100 through $500, over $500 through $1,000, and over $1,000 form mutually exclusive bands. These are presentation boundaries, not financial-hardship definitions. The weighted median and upper quantiles are inverse empirical-CDF thresholds; tied values mean that the proportion above a quantile need not equal its nominal upper tail.

Use person weights PERWT24F, strata VARSTR and clustered PSUs VARPSU. Domain estimation retains the full survey structure. Means and ratio components use Taylor linearization with domain degrees of freedom. Main proportions use bounded beta intervals. Quantiles use the inverse weighted CDF and beta-Woodruff intervals; the reported interval-width standard error is an approximation.

For the new means and proportions, require at least 60 users in the denominator, finite estimates and intervals, and positive design degrees of freedom. RSE below 30% is reportable, 30–50% is flagged, and above 50% is withheld; a rare-proportion exception flags an estimate when its upper confidence bound is at most 10%. Boundary estimates require review. Quantiles additionally require at least 30 observed users on each inclusive side of the point estimate and ordered finite bounds. Quantile support rules are project rules, not an AHRQ certification. No participant is removed simply because an estimate is withheld.

Payer-component and supplementary outputs retain their earlier gates: at least 100 adults, 30 users, RSE at most 30%, positive design degrees of freedom, and at least 30 positive contributors for a payer component. Withheld components are not zero; visible shares must not be rescaled to sum to 100%.

## Supplementary analyses

Descriptive age and annual insurance comparisons retain their original definitions. Any-private coverage includes TRICARE/CHAMPVA and mixed private/public coverage under the MEPS convention. Complete monthly comparisons require all monthly insurance indicators to be known; incomplete records remain in the main cohort. Coverage at some time in every month does not establish continuous daily coverage or drug-specific reimbursement. First-use month and purchase round do not date each refill.

An age-only survey quasibinomial model uses a fixed natural age spline and annual coverage without an interaction. Predictive margins standardize private and public-only groups to their combined weighted age distribution. Support, convergence, rank and covariance are checked; no significance-based model selection is performed. This is an age-adjusted association, not a causal insurance effect. No adjusted spending model is fitted.

## Analysis sequence

The initial use and annual-coverage analysis was specified before outcome estimation. The age and monthly-coverage follow-up followed inspection of initial results and cell counts. The main payment-distribution analysis followed those earlier results but was specified before estimating the new quantiles and bands. These follow-ups are not original preregistrations. Earlier numerical estimates and reporting gates are retained in the aggregate reference outputs; the main report focuses on payments because monthly coverage cannot answer purchase-specific reimbursement questions.

## Verification

Tests exercise exact medication classification, conflicting names, repeated records, zero payments, overlapping insurance, missing monthly histories, payment reconciliation, band boundaries, unequal weights and tied quantiles. Analysis scripts independently reconstruct selected point estimates, full-design PSU-based Taylor variances, bounded intervals and quantile inversion. Supplementary predictive margins and their covariance components are checked by a separate calculation. Cross-output checks confirm cohort equality, denominator partitions and unchanged reference means.

Only aggregate outputs are published. The official files and intermediate records are downloaded or generated locally and excluded from version control. Source revisions require review rather than silently accepting changed inputs.

## Field dictionary

| Field | Source / definition | Handling |
| --- | --- | --- |
| DUPERSID | Both files: person ID | Local join key; HC-256 must be unique |
| RXRECIDX | HC-254A event ID | Unique; multiple different events per person expected |
| AGELAST | HC-256 age last eligible | Adult >=18; age top-coded at 85; strata 18–64 and 65+ |
| INSCOV24 | HC-256 annual coverage | 1 any private including TRICARE/CHAMPVA; 2 public only; 3 uninsured throughout eligible months |
| PERWT24F | Final person weight | Positive weights enter design; event weights must match people |
| VARSTR / VARPSU | Public variance strata / PSUs | Full design before adult/user domain selection |
| RXDRGNAM | Edited/imputed Multum generic name | Exact ingredient whitelist; insulin combinations excluded |
| RXNAME | Edited/imputed medicine name | Exact brand audit and sensitivity restriction; conflicts trigger review |
| RXSF24X | Edited/imputed self/family payments | Nonnegative 2024 dollars summed over target events |
| RXXP24X | Edited/imputed all-source payments | Nonnegative 2024 dollars; self/family cannot exceed total beyond rounding tolerance |
| user | Any primary target-drug event | Binary per person; absent target events imply zero observed use |
| oop / total / fills | Target-event sums and count | One row per person, not one row per prescription |
| semaglutide_* / tirzepatide_* | Ingredient-specific variables | Users can overlap; ingredient counts are not additive |
| brand_* | Brand-event restriction | All sums and any-use flags rebuilt using restricted records |

All adult non-users enter prevalence denominators. Spending is conditional on observed use, including zero self/family payments. Events include initial acquisitions and refills that cannot always be distinguished; record counts are not standardized 30-day supplies.

Mean annual self/family payment = sum(weight × person target-drug out-of-pocket spending) / sum(weight among users).

Aggregate out-of-pocket share = sum(weight × target-drug out-of-pocket spending) / sum(weight × target-drug total payments). This is not the mean of individual payment shares.

Negative reserved codes are not dollar amounts or valid ages. The pipeline fails on unresolved target payment, age or design values. Unknown insurance would remain in the overall denominator but be audited separately. Missing generic names across all medicines are counted because their identities may be unknown.

### Insurance and payment fields

| Field | Definition and handling |
| --- | --- |
| INSmm24X | Monthly any hospital/medical insurance: 1 yes, 2 no. Require 12 known months for complete-history comparisons; negative/out-of-scope values are not uninsured. Month abbreviations run JA through DE. |
| PRImm24 / TRImm24X / MCRmm24X / MCDmm24X / VAPmm24 / GVAmm24 | Private, TRICARE/CHAMPVA, Medicare, Medicaid/SCHIP, VA and other public monthly flags. Preserve all simultaneous types and compare 12 source combinations. |
| monthly_history | all_12, some_months (1–11 covered months), none_12, or incomplete. Any coverage in every month does not guarantee uninterrupted daily coverage. |
| source_history | Within all_12: stable_sources, changed_sources, or source_unknown; otherwise not_all_12. This does not identify changes of plan within a source. |
| RXPV24X / RXMR24X / RXMD24X / RXTR24X | Edited/imputed private, Medicare, Medicaid and TRICARE payments per prescription record. |
| RXVA24X / RXOF24X / RXSL24X / RXWC24X / RXOT24X | Other components, combined as pay_other; together with the above and RXSF24X reconcile to RXXP24X. |
| pay_self / pay_private / pay_medicare / pay_medicaid / pay_tricare / pay_other | Target-record annual person totals. Means include every observed user, including zero component payment; payer shares are ratios of weighted sums. Positive-payer contributor counts are not mutually exclusive. |
| age_band | 18–34, 35–49, 50–64, 65–74, 75+ using AGELAST. Age 85 represents the top-coded older ages. |
| age_adjusted_use_pct | Survey predictive margin standardized over combined any-private/public-only adults; age-only spline model, not a causal or fully adjusted insurance effect. |
| age_adjusted_difference_pp | Public-only margin minus any-private margin, in percentage points, with covariance accounted for. No RSE threshold for this signed contrast; both margin gates and model diagnostics must pass. |

PURCHRD is a survey round, and RXBEGMM/RXBEGYRX describe first use; they are not used to create monthly purchase dates. RXDAYSUP exists but is not analyzed in this extension; missingness, special codes and consistency would need separate checks before standardizing supply duration.

### Distribution outputs

- All new measures use the same 800 adult users, including zero self/family and zero total payments. Mean OOP remains the original weighted mean.
- zero_oop_pct and four positive-dollar bands partition annual person-level oop at 0, 100, 500 and 1,000 dollars; upper bounds belong to the lower band. Their denominator is all users, not only those in a band.
- median_oop, p75_oop, p90_oop are inverse weighted-CDF thresholds, not means among high-payment users. Each carries a beta-Woodruff 95% CI and a labelled approximate interval-width SE.
- payment-distribution.csv stores counts, denominators, units, uncertainty method and reportability. Dollar cutoffs are not financial-hardship thresholds. No mean individual oop/total ratio is added; one user has zero total payments.
