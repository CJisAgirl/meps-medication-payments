# SAS implementation: MEPS medication payments

[Open the complete program](run_meps.sas)

This directory provides SAS source code and input conversion for the main analysis. The published research results are generated and checked by the Python/SQL/R pipeline. Run the SAS program using the steps below to produce its output tables and reference comparisons.

## Scope

The program implements the main 2024 adult medication-use and payment analysis:

- **DATA step:** read original person and prescription fields, normalize drug names, check ingredient/brand agreement, exclude insulin combinations, and validate payment components.
- **PROC SQL:** aggregate repeated prescription records by person and left-join to the person file, retaining nonusers and zero payments.
- **PROC SURVEYMEANS:** specify `PERWT24F`, `VARSTR`, and `VARPSU`; use `DOMAIN` for adult prevalence and adult-user annual spending, payment-band proportions, payer ratios and weighted quantiles.
- **Quality control:** stop for duplicate identifiers, unmatched records, invalid payments, unexpected cohort counts or disagreement with the saved reference estimates.

This covers the main adult population. The age and monthly insurance-history supplements remain in R. Drug use is observed use regardless of indication, not a diagnosis-based diabetes cohort.

## Run

1. Clone this repository and install its Python requirements using the root [reproduction steps](../README.md#reproduce). R is not required just to prepare the SAS input files.
2. From the repository directory, run:

   ```sh
   python scripts/prepare_sas_inputs.py
   ```

   This downloads the original AHRQ archives if absent, verifies their pinned hashes, and exports two CSV files under `data/sas-inputs/`: `person_source.csv` and `rx_source.csv`. It only projects source columns and verifies a lossless round trip; it does not classify medications, aggregate people or compute statistics. An input manifest records dimensions and file hashes. SAS performs the analytical steps independently.
3. Open a licensed SAS environment with SAS/STAT, such as [SAS OnDemand for Academics](https://www.sas.com/en_us/software/on-demand-for-academics.html). Upload both CSVs and `run_meps.sas` to SAS Studio. Browser-based SAS does not require a local Mac installation.
4. At the top of `run_meps.sas`, change `input_dir` to the uploaded CSV folder's **server path**, not the Mac path. Run the entire program in a fresh SAS session. The default output location is the session's temporary WORK folder; alternatively set `output_dir` to an existing writable folder on the SAS server.
5. Save the complete log and aggregate CSV outputs before closing the session. Accept a run only after inspecting the log for errors and unexplained warnings and confirming the completion marker `MEPS_SAS_REFERENCE_POINT_AND_SE_CHECKS_PASSED`. A submitted program or populated output window alone does not establish a successful run.

The reference source files contain 19,140 person records and 204,550 prescription records. The pinned cohort has 18,683 positive-weight respondents, 15,126 adults, 800 adult users and 4,368 adult target-drug prescription records. The program checks these counts rather than silently accepting a different denominator.

## Outputs and comparison

| Output | Meaning |
| --- | --- |
| `sas_mean_checks.csv` | Seven estimates and Taylor standard errors: adult prevalence, mean annual self/family payments and five payment-band percentages |
| `inverse_cdf_checks.csv` | Median, 75th and 90th percentile points using the reference inverse weighted empirical CDF definition |
| `user_means.csv` | Adult-user mean payments, record counts and payment-band proportions, with SAS confidence intervals |
| `payer_shares.csv` | Ratios of weighted payment totals; sparse or imprecise components withheld under the existing payer gates |
| `native_quantiles.csv` | Native SAS survey quantiles and confidence intervals, for separate method review |

The first two tables are checked using `PROC COMPARE` against embedded values generated from the saved R aggregate tables, with absolute tolerance `1e-6`. They compare point estimates and mean/proportion standard errors only. They do not establish equivalence of every confidence interval or payer estimate.

R uses beta intervals for payment-band proportions and inverse-CDF quantiles with beta Woodruff intervals. SAS's native quantile and interval conventions, and domain degrees of freedom, can differ. The separate inverse-CDF calculation aligns quantile point definitions; it does not reproduce quantile confidence intervals. Review these distinctions before replacing any published result.

The full positive-weight survey design is retained for estimation. Filtering to users before `PROC SURVEYMEANS` would discard information needed for domain variances. The user-only sort is used solely for the independent quantile **point** calculation. A suppressed payer share is not zero, and visible shares must not be rescaled to 100%.

## Validation and data handling

Python tests cover source fingerprint rejection, CSV precision and identifier preservation, truncation rejection, and reference-table integrity. SAS execution produces the log and comparison tables described above; use those outputs to assess each run.

Only code and aggregate reference values belong in Git. Source CSVs, individual records, SAS datasets and local logs are ignored. Do not upload a SAS WORK library or any person-level file to the public repository.

References: [AHRQ sources](../SOURCES.md), [study methods](../METHODS.md), [SAS domain analysis](https://support.sas.com/documentation/cdl/en/statug/68162/HTML/default/statug_surveymeans_syntax05.htm), [SURVEYMEANS options](https://support.sas.com/documentation/cdl/en/statug/68162/HTML/default/statug_surveymeans_syntax01.htm), [ODS table names](https://support.sas.com/documentation/cdl/en/statug/68162/HTML/default/statug_surveymeans_details75.htm).
