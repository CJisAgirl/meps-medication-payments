# Primary sources and provenance

Checked 2026-10-09 UTC. Data describe 2024; release year is 2026.

1. AHRQ, [HC-256 overview](https://meps.ahrq.gov/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-256), [documentation](https://meps.ahrq.gov/data_stats/download_data/pufs/h256/h256doc.shtml), [codebook](https://meps.ahrq.gov/data_stats/download_data_files_codebook.jsp?PUFId=H256). Released August 2026. Demographics, summary insurance coverage and variance sections establish person definitions.
2. AHRQ, [HC-254A overview](https://meps.ahrq.gov/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-254A), [documentation](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml), [codebook](https://meps.ahrq.gov/data_stats/download_data_files_codebook.jsp?PUFId=H254A). Released July 2026. Sections C.2.6, C.4 and C.5 describe drug identifiers, payments, imputation, person denominators and survey variance. Payments exclude manufacturer rebates to payers.
3. FDA, [January 2024 communication, Table 1](https://www.fda.gov/drugs/drug-safety-communications/update-fdas-ongoing-evaluation-reports-suicidal-thoughts-or-actions-patients-taking-certain-type). Used solely for brand/ingredient mappings, insulin combinations and tirzepatide's dual receptor action; no safety conclusion is taken from this superseded communication. Observed generics are semaglutide, tirzepatide, dulaglutide and liraglutide. The candidate list also includes albiglutide, with no matched records.
4. FDA, [2024 Mounjaro label](https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/215866s010s015s022lbl.pdf) and [2024 Ozempic label](https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/209637s032lbl.pdf), for ingredient identity. No respondent's indication is inferred.
5. R survey author documentation: [domain subsetting](https://r-survey.r-forge.r-project.org/survey/html/subset.survey.design.html), [proportion CIs](https://r-survey.r-forge.r-project.org/pkgdown/docs/reference/svyciprop.html). Checked package version: 4.5.

Direct download URLs, first retrieval times, byte counts and SHA-256 fingerprints are in results/source-manifest.json. Source revisions require explicit review and new provenance.

Data citation: Agency for Healthcare Research and Quality. Medical Expenditure Panel Survey, 2024 Full Year Consolidated Data File (HC-256) and 2024 Prescribed Medicines (HC-254A). Released 2026.

## Extension checks — 11 October 2026

Re-read HC-256 C.2.5.11 (monthly insurance and source indicators) and HC-254A C.2.5–2.6 / C.4 (purchase round, carried-forward first-use month, ten payment sources, imputation). Checked actual variable labels in the pinned Stata files. No new dataset or release was substituted. Consulted [survey predictive margins](https://r-survey.r-forge.r-project.org/pkgdown/docs/reference/svypredmeans.html), and inspected the installed survey 4.5 function for its model and standardized-prediction covariance components. Method reference: Graubard and Korn (1999), Predictive Margins with Survey Data, Biometrics 55:652–659.

## Payment distribution checks — 11 October 2026

- [AHRQ MEPS-HC precision guidelines](https://meps.ahrq.gov/survey_comp/precision_guidelines.shtml): denominator sample requirements, mean/proportion RSE flags and rare-proportion exception. Applied to new mean/proportion outputs; not presented as AHRQ certification of quantile rules.
- [survey quantile documentation](https://www.stat.ethz.ch/CRAN/web/packages/survey/refman/survey.html#svyquantile) and [quantile rules vignette](https://stat.ethz.ch/CRAN/web/packages/survey/vignettes/qrule.pdf). Also read installed survey 4.5 help and source for beta-Woodruff intervals, inverse-CDF ties, degrees of freedom and approximate CI-width SEs.
