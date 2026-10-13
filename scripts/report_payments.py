"""Focused English report generated only from checked aggregate outputs."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = {r['metric']: r for r in csv.DictReader((ROOT/'results/payment-distribution.csv').open())}
payers = list(csv.DictReader((ROOT/'results/extension-estimates.csv').open()))
audit = json.loads((ROOT/'results/payment-distribution-audit.json').read_text())


def show(row, digits=2):
    if row['status'].startswith('withheld:'):
        return 'Withheld: ' + row['status'].removeprefix('withheld: ')
    if row['status'].startswith('suppressed:'):
        return 'Withheld: ' + row['status'].removeprefix('suppressed: ')
    suffix = '*' if row['status'].startswith('flagged:') else ''
    return (f"{float(row['estimate']):,.{digits}f} "
            f"({float(row['lower_95']):,.{digits}f}–{float(row['upper_95']):,.{digits}f}){suffix}")


def payer(source, metric):
    return next(r for r in payers if (r['analysis'], r['age'], r['group'], r['metric']) ==
                ('payment_sources', 'All adults', source, metric))


sources = ['Self/family', 'Private insurance', 'Medicare', 'Medicaid', 'TRICARE', 'Other sources']
en_payers = '\n'.join(f"| {s} | {show(payer(s,'payment_share_pct'))} | {show(payer(s,'annual_payment_usd'),0)} |" for s in sources)
payer_precision_note = (
    ' *Limited precision under the reporting criteria in Methods.'
    if any(payer(s, metric)['status'].startswith('flagged:')
           for s in sources for metric in ['payment_share_pct', 'annual_payment_usd'])
    else ''
)
quantiles = [('median_oop','Median (50th percentile)'),
             ('p75_oop','75th percentile'),('p90_oop','90th percentile')]
en_distribution = f"| Mean | {show(rows['mean_oop'])} |\n" + '\n'.join(f"| {en} | {show(rows[k])} |" for k,en in quantiles)
bands = [('zero_oop_pct','$0'), ('oop_0_100_pct','Over $0 through $100'),
         ('oop_100_500_pct','Over $100 through $500'),
         ('oop_500_1000_pct','Over $500 through $1,000'),
         ('oop_over_1000_pct','Over $1,000')]
en_bands = '\n'.join(f"| {en} | {rows[k]['sample_in_category']} | {show(rows[k])} |" for k,en in bands)

# Fail explicitly if an unsupported primary finding would otherwise enter prose.
assert all(rows[k]['status']=='reportable' for k in ['mean_oop','median_oop','p75_oop','p90_oop','zero_oop_pct','oop_over_1000_pct'])
mean = float(rows['mean_oop']['estimate'])
median = float(rows['median_oop']['estimate'])
zero = float(rows['zero_oop_pct']['estimate'])
high = float(rows['oop_over_1000_pct']['estimate'])
self_share = float(payer('Self/family','payment_share_pct')['estimate'])

brief = f'''# Payment Sources and Annual Out-of-Pocket Spending for GLP-1 Receptor Agonists and Tirzepatide

**Medical Expenditure Panel Survey, 2024**

This descriptive analysis included **{audit['adult_users']} adult users** with at least one recorded target-medicine acquisition among 15,126 sampled adults. Users were included regardless of treatment indication. Prescription payments were aggregated within person over calendar year 2024 and analyzed using the MEPS complex survey design. The source files were released in July and August 2026.

**Key findings:** Self/family payments accounted for {self_share:.2f}% of total target-medicine payments. Mean annual self/family spending was ${mean:,.2f}, compared with a median of ${median:,.2f}. An estimated {zero:.2f}% of users had no self/family payments, and {high:.2f}% paid more than $1,000.

## 1. Payment sources

| Payment source | Share of all target payments, % (95% CI) | Annual USD per user (95% CI) |
| --- | ---: | ---: |
{en_payers}

Payment shares are ratios of survey-weighted source totals to total payments. Source-specific means include all {audit['adult_users']} users, including zero payments; payment sources may overlap within individuals.{payer_precision_note}

[Payment-source figure](payment-sources.png).

## 2. Annual self/family spending

| Summary of annual self/family payments | USD (95% CI) |
| --- | ---: |
{en_distribution}

Mean annual self/family spending was ${mean:,.2f}, compared with a median of ${median:,.2f}, indicating a right-skewed distribution. The 75th and 90th percentiles were ${float(rows['p75_oop']['estimate']):,.2f} and ${float(rows['p90_oop']['estimate']):,.2f}, respectively.

Estimates include zero payments and capture annual spending on the target medicines. Treatment duration was not standardized to 12 months.

## 3. Distribution of annual self/family spending

| Annual self/family payments | Sample users | Weighted share of users, % (95% CI) |
| --- | ---: | ---: |
{en_bands}

![Annual self/family payment distribution](selfpay-distribution.png)

Annual self/family spending was zero for {zero:.2f}% of users and exceeded $1,000 for {high:.2f}%. Dollar bands describe spending levels; affordability relative to household income was not assessed.

## Study limitations

MEPS payment records undergo editing and imputation and do not capture the full claims-adjudication process. Manufacturer rebates to payers are not captured, so reported payments are not net payer costs after rebates. The analysis does not assess benefit eligibility, denial reasons, cost-related nonreceipt of medicines or treatment effectiveness. Insurance comparisons are descriptive associations.

Public-file timing variables do not support linking each medication acquisition to its purchase-month insurance coverage. Age-stratified payments and age-adjusted use estimates are reported in the [supplement](extension-note.md).

## Statistical methods and reproducibility

Estimates used person weights, strata and primary sampling units, with domain estimation retaining the full survey design. Mean and proportion standard errors used Taylor linearization. Proportions used beta confidence intervals; quantiles used the inverse weighted empirical distribution with beta-Woodruff intervals. Descriptive estimates followed the shared AHRQ-based reporting framework, with separate support checks for quantiles; specifications are provided in [Methods](../METHODS.md#reporting-framework).

The payment-distribution analysis was specified after reviewing the initial results and before estimating the quantiles and payment bands. The [analysis sequence](../METHODS.md#analysis-sequence) documents this exploratory development and subsequent reporting revisions.

Independent calculations checked weighted estimates, Taylor standard errors, confidence intervals and quantile points. The distribution analysis includes {audit['independent_mean_proportion_point_se_checks']} point/standard-error checks, {audit['independent_interval_checks']} interval checks and {audit['independent_quantile_point_checks']} quantile-point checks. [Reproduction instructions](../README.md#reproduce) and aggregate audit outputs are available below.

[Distribution results](payment-distribution.csv) · [Distribution audit](payment-distribution-audit.json) · [Cross-output audit](payment-verification.json) · [Methods](../METHODS.md) · [Sources](../SOURCES.md)
'''

(ROOT/'results/research-brief.md').write_text(brief)
print('Generated results/research-brief.md.')
