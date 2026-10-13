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
    suffix = ' [low precision]' if row['status'].startswith('flagged:') else ''
    return (f"{float(row['estimate']):,.{digits}f} "
            f"({float(row['lower_95']):,.{digits}f}–{float(row['upper_95']):,.{digits}f}){suffix}")


def payer(source, metric):
    return next(r for r in payers if (r['analysis'], r['age'], r['group'], r['metric']) ==
                ('payment_sources', 'All adults', source, metric))


sources = ['Self/family', 'Private insurance', 'Medicare', 'Medicaid', 'TRICARE', 'Other sources']
en_payers = '\n'.join(f"| {s} | {show(payer(s,'payment_share_pct'))} | {show(payer(s,'annual_payment_usd'),0)} |" for s in sources)
quantiles = [('median_oop','Median (50th percentile)'),
             ('p75_oop','75th percentile'),('p90_oop','90th percentile')]
en_distribution = f"| Mean | {show(rows['mean_oop'])} |\n" + '\n'.join(f"| {en} | {show(rows[k])} |" for k,en in quantiles)
bands = [('zero_oop_pct','$0'), ('oop_0_100_pct','Over $0 through $100'),
         ('oop_100_500_pct','Over $100 through $500'),
         ('oop_500_1000_pct','Over $500 through $1,000'),
         ('oop_over_1000_pct','Over $1,000')]
en_bands = '\n'.join(f"| {en} | {rows[k]['sample_in_category']} | {show(rows[k])} |" for k,en in bands)

# Fail explicitly if an unsupported primary finding would otherwise enter prose.
assert all(rows[k]['status']=='reportable' for k in ['mean_oop','median_oop','zero_oop_pct','oop_over_1000_pct'])
mean = float(rows['mean_oop']['estimate'])
median = float(rows['median_oop']['estimate'])
zero = float(rows['zero_oop_pct']['estimate'])
high = float(rows['oop_over_1000_pct']['estimate'])
self_share = float(payer('Self/family','payment_share_pct')['estimate'])

brief = f'''# Who paid for GLP-1 medicines and tirzepatide, and what did users pay themselves?

**MEPS 2024 | Recorded payment sources and annual self/family payments**

The population is adults with at least one recorded target-medicine purchase/receipt: **{audit['adult_users']} sampled users** from 15,126 sampled adults. Records are aggregated within person before survey weighting; repeated fills do not become independent people. The data were released in July/August 2026 and describe 2024.

**Main finding:** self/family payments represented {self_share:.2f}% of weighted target-medicine payments, while users' annual self/family payments had a mean of ${mean:,.0f} and a median of ${median:,.2f}. An estimated {zero:.2f}% of users had zero self/family payments and {high:.2f}% paid more than $1,000. The aggregate payment share and the distribution across people answer different questions; neither establishes affordability.

## 1. Who paid the recorded medicine costs?

| Payment source | Share of all target payments, % (95% CI) | Annual USD per user (95% CI) |
| --- | ---: | ---: |
{en_payers}

Shares divide each source's weighted total by the weighted total from all sources. They are not the average of each person's copayment percentage. Component means include **all {audit['adult_users']} users**, including zeros from that source. Payers may overlap for one person. Existing payer rules are retained; TRICARE has 20 positive-payment users and is withheld. Do not rescale visible shares to 100% or add their confidence bounds.

These are edited/imputed survey payment records, not raw adjudicated claims or a measure of benefit eligibility. Payments exclude manufacturer rebates to payers. [Payment-source figure](payment-sources.png).

## 2. How much did an individual user pay over the year?

| Summary of annual self/family payments | USD (95% CI) |
| --- | ---: |
{en_distribution}

The median is the first dollar amount where the weighted cumulative proportion reaches 50%; the 75th and 90th percentiles use 75% and 90%. Ties mean the percentage strictly above a percentile need not be exactly 50%, 25% or 10%. These thresholds are not average costs among the highest-spending users. The mean exceeds the median because the payment distribution has a substantial upper tail; the mean alone does not describe a typical user.

All summaries include zero self/family payments. They measure recorded calendar-year payments, not the price of 12 continuous treatment months, a monthly copay, or spending on all medical care.

## 3. How common were zero or larger self/family payments?

| Annual self/family payments | Sample users | Weighted share of users, % (95% CI) |
| --- | ---: | ---: |
{en_bands}

![Annual self/family payment distribution](selfpay-distribution.png)

The five bands are mutually exclusive and include all {audit['adult_users']} users; raw counts and weighted percentages need not match by simple division. $1,000 is a presentation cutoff, not a validated financial-hardship threshold. Zero self/family payments do not necessarily mean an insurer paid the entire bill: {audit['zero_total_payment_users']} user has zero recorded total payments across all target records and remains in the denominator.

## What these results can and cannot answer

They describe **observed payment sources and the distribution of dollar payments among recorded users**. They do not identify people who did not obtain a medicine because of price, denial reasons, prescription-benefit terms, income-relative hardship, treatment effectiveness, or a causal effect of insurance. A lower mean in one insurance group would not by itself establish better coverage.

Monthly insurance histories cannot be aligned to each refill's purchase month in these public files. Their unchanged results are now a [coverage-methods appendix](coverage-appendix.md), not evidence of purchase-specific reimbursement. Detailed ages and the age-only use model remain [supplementary analyses](extension-note.md).

## Methods, checks and reproduction

The [analysis methods](../METHODS.md#analysis-sequence) was written after prior results were seen and before the new distribution was estimated. This is not an original preregistration. Use the full stratified, clustered survey design, then the adult-user domain; mean/proportion SEs use Taylor linearization, proportions have beta CIs, and quantiles use inverse weighted CDFs with beta-Woodruff CIs. New mean/proportion rules use the relevant denominator and AHRQ precision categories; quantile support is assessed separately. Legacy results retain their earlier rules. No person is deleted because an estimate is withheld.

The full run includes 16 Python tests and 8 R payment-helper tests; the new distribution has {audit['independent_mean_proportion_point_se_checks']} independent point/Taylor-SE checks, {audit['independent_interval_checks']} interval checks and {audit['independent_quantile_point_checks']} quantile point checks. Python independently checks weighted bands/quantiles, denominators and reconciliation. Original numerical estimates remain unchanged. See the [reproduction instructions](../README.md#reproduce).


[Distribution results](payment-distribution.csv) · [Distribution audit](payment-distribution-audit.json) · [Cross-output audit](payment-verification.json) · [Methods](../METHODS.md) · [Sources](../SOURCES.md)
'''
(ROOT/'results/research-brief.md').write_text(brief)
print('Generated results/research-brief.md.')
