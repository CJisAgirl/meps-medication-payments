# Appendix: what monthly insurance histories can and cannot establish

**Historical exploratory results; not a purchase-specific coverage analysis.**

The main study now focuses on [actual payment sources and user spending](research-brief.md). These categories describe insurance continuity, but cannot date every refill or establish drug-benefit eligibility. Sparse groups also limit comparisons. The original numerical estimates and people are retained, not discarded as invalid data.

The legacy 30-user gate remains here for historical reproducibility. It is a project rule, not a mathematical boundary or a uniform AHRQ requirement. The new payment distribution uses estimand-specific rules documented in [payment methods](../METHODS.md#payment-distribution); changing a reporting rule cannot recover missing purchase dates.

## 2. Monthly histories, without inventing purchase dates

Require all 12 INS monthly indicators to be explicitly yes/no. “Covered in every month” means coverage at some point in each month, not coverage on every day. “Some fully uninsured months” means 1–11 months with any coverage and at least one month without coverage. Out-of-scope and unknown values are never converted to uninsured. The complete-history restriction changes the analysis population.

195 adults, including 2 users, have incomplete monthly histories and are excluded only from the complete-history comparisons. They remain in the original all-adult results. 195 incomplete histories include out-of-scope months. Uninsured-all-12 counts therefore differ from the original annual-category counts based on eligible months.

| Monthly history | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | ---: | ---: | ---: |
| Covered in every month | 764 / 12686 | 5.68 (5.23–6.17) | 349 (288–409) |
| Some fully uninsured months | 29 / 1194 | Withheld: user n < 30 | Withheld: user n < 30 |
| Uninsured in all 12 months | 5 / 1051 | Withheld: user n < 30 | Withheld: user n < 30 |

Among people covered in all 12 months, a second comparison uses the monthly combination of private, TRICARE/CHAMPVA, Medicare, Medicaid/SCHIP, VA and other public indicators. Multiple simultaneous sources are preserved. A changed combination does not necessarily mean a period without insurance, and a constant combination does not rule out changing plans within one source type. These are descriptive comparisons; health status and age may differ between groups.

| Source history among all-month-covered adults | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | ---: | ---: | ---: |
| Same source mix each month | 661 / 11253 | 5.54 (5.05–6.08) | 357 (291–424) |
| Source mix changed | 103 / 1433 | 6.96 (5.58–8.65) | 284 (163–405) |

![Monthly insurance and source histories](monthly-insurance.png)

**No month-of-purchase linkage is claimed.** PURCHRD identifies the survey round; RXBEGMM/RXBEGYRX identify first use and can be carried forward to subsequent records. They do not date every refill. Annual payments are not allocated evenly across months. No drug formulary, denial or unmet-need measure is inferred.


Sources: [HC-256 insurance](https://meps.ahrq.gov/data_stats/download_data/pufs/h256/h256doc.shtml), [HC-254A timing](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml).
