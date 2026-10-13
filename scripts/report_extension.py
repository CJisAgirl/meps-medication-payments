"""Readable extension evidence, generated from aggregate results only."""
from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((ROOT/'results/extension-estimates.csv').open()))
adjusted = list(csv.DictReader((ROOT/'results/age-adjusted-use.csv').open()))
cohort = json.loads((ROOT/'results/extension-cohort-audit.json').read_text())
design = json.loads((ROOT/'results/extension-design-audit.json').read_text())


def show(row, digits=2):
    if not (row['status']=='reportable' or row['status'].startswith('flagged:')):
        return 'Withheld: ' + row['status'].removeprefix('suppressed: ').removeprefix('withheld: ')
    suffix='*' if row['status'].startswith('flagged:') else ''
    return f"{float(row['estimate']):,.{digits}f} ({float(row['lower_95']):,.{digits}f}–{float(row['upper_95']):,.{digits}f}){suffix}"


def find(analysis, group, metric, age='All adults'):
    return next(r for r in rows if (r['analysis'],r['group'],r['metric'],r['age'])==(analysis,group,metric,age))


def pair_table(analysis):
    result=[]
    for r in rows:
        if r['analysis']!=analysis or r['metric']!='prevalence_pct': continue
        cost=find(analysis,r['group'],'annual_oop_usd',r['age'])
        lead=f"{r['age']} | " if analysis=='detailed_age' else ''
        result.append(f"| {lead}{r['group']} | {r['unweighted_users']} / {r['unweighted_adults']} | {show(r)} | {show(cost,0)} |")
    return '\n'.join(result)


def payer_table(age):
    result=[]
    for r in rows:
        if r['analysis']!='payment_sources' or r['metric']!='payment_share_pct' or r['age']!=age: continue
        amount=find('payment_sources',r['group'],'annual_payment_usd',age)
        result.append(f"| {r['group']} | {r['positive_payer_users']} | {show(amount,0)} | {show(r)} |")
    return '\n'.join(result)



model=design['age_adjustment']
metric_labels = {'age_adjusted_use_pct': 'Age-adjusted use, %',
                 'age_adjusted_difference_pp': 'Difference, percentage points'}
adjusted_table='\n'.join(f"| {r['group']} | {metric_labels[r['metric']]} | {show(r)} |" for r in adjusted)
model_note = '' if model['status'].startswith('estimated') else f" Model estimation status: {model['status']}."
age_payments='\n\n'.join(f"### {age}\n\n| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |\n| --- | ---: | ---: | ---: |\n{payer_table(age)}" for age in ['18-34','35-49','50-64','65-74','75+'])
rules='Estimates follow the [reporting framework](../METHODS.md#reporting-framework). Asterisks and triangular plot markers denote limited precision. Withheld estimates are identified by their sample-size or precision criterion.'
text=f'''# Supplementary age, insurance and payment analyses

These exploratory analyses extend the [main payment report](research-brief.md) to age and insurance subgroups. The questions were developed after reviewing initial results; their sequence is documented in [Methods](../METHODS.md#analysis-sequence).

## Reporting framework

{rules}

## Age and annual coverage

Age groups were 18–34, 35–49, 50–64, 65–74 and 75+. Under the MEPS definition, any-private annual coverage includes TRICARE/CHAMPVA and mixed private/public coverage. Use proportions are estimated among all adults in each group; spending means are estimated among medication users, including zero payments.

![Age and annual coverage](detailed-age.png)

| Age | Annual coverage | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | --- | ---: | ---: | ---: |
{pair_table('detailed_age')}

## Recorded payment sources

Ten edited/imputed source-payment fields were aggregated within person. Other sources combine VA/CHAMPVA, other federal, state/local, workers' compensation and other insurance. Means include all adult medication users, including zero payments; shares are ratios of weighted source totals to total payments. Counts indicate users with positive payments from each source and may overlap.

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
{payer_table('All adults')}

![Payment sources](payment-sources.png)

Payment shares retain the all-source denominator when individual estimates are withheld. Manufacturer rebates are not captured. The survey records support payment estimates rather than claim-level adjudication or denial assessment.

## Age-adjusted association

A survey-weighted quasibinomial model included a natural age spline (3 df) and annual coverage, without an interaction. Predictive margins were standardized to the combined weighted population of adults with any-private or public-only coverage. Uninsured adults were retained in descriptive analyses and excluded from this model.{model_note}

Model feasibility required at least 100 adults, 5 users and 5 nonusers per coverage-by-age cell, together with convergence, full rank and finite covariance. These checks were specified for the pooled spline model separately from descriptive reporting criteria.

| Group or comparison | Metric | Estimate (95% CI) |
| --- | --- | ---: |
{adjusted_table}

Marginal percentages use the shared denominator and precision criteria with model-based logit-delta intervals. The public-minus-private contrast incorporates covariance between margins and is reported when both margins meet the reporting criteria; no RSE threshold is applied to the signed contrast. Adjustment is limited to age. Disease burden, indication, income, medication mix and selection remain potential sources of confounding. The estimates represent age-adjusted associations; spending was not modeled.

## Checks

There are {design['extension_rows']} descriptive rows: {design['reportable']} displayed without a flag, {design['flagged']} displayed with a precision flag and {design['suppressed']} withheld. Independent calculations reconstruct {design['independent_mean_ratio_checks']} weighted points and full-design Taylor standard errors. See [design audit](extension-design-audit.json), [cohort audit](extension-cohort-audit.json), [aggregate estimates](extension-estimates.csv), [model support](age-adjustment-support.csv) and [adjusted results](age-adjusted-use.csv).

## Payer components by age

Age-specific means include all medication users within each group, including zero payments from the source. Reporting follows the shared precision framework.

{age_payments}
'''
(ROOT/'results/extension-note.md').write_text(text)
print('Generated current supplementary reports under the unified descriptive framework.')
