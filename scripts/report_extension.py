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



missing=cohort['monthly_history_counts'].get('incomplete',{'adults':0,'users':0})
model=design['age_adjustment']
adjusted_table='\n'.join(f"| {r['group']} | {r['metric']} | {show(r)} |" for r in adjusted)
age_payments='\n\n'.join(f"### {age}\n\n| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |\n| --- | ---: | ---: | ---: |\n{payer_table(age)}" for age in ['18-34','35-49','50-64','65-74','75+'])
rules="All descriptive means, ratios and person proportions use one AHRQ-based reporting framework. Require at least 60 unweighted people in the relevant analysis denominator, positive survey-design degrees of freedom, and finite estimates and uncertainty. For observed-use proportions the denominator is adults; for conditional spending and payer amounts/ratios it is medication users, including zero payments. Positive-payer counts remain diagnostics, with no separate minimum. RSE below 30% is reportable; 30% through 50% is displayed with an asterisk; above 50% is withheld. Only person proportions can use the AHRQ rare-proportion exception (95% upper bound at most 10%, displayed with an asterisk). A payer share is a ratio of dollars and never uses that exception. Boundary/degenerate estimates require review. An asterisk indicates limited precision, not statistical significance. No records are removed because an estimate is withheld."
appendix=f'''# Appendix: monthly insurance histories

These descriptive histories cannot date every refill or establish drug-specific reimbursement. Read the [main payment report](research-brief.md) for observed payment sources.

{rules}

## Complete monthly histories

All 12 monthly insurance indicators must be explicitly known. Coverage at some time in every month does not establish coverage on every day. Unknown and out-of-scope values are never converted to uninsured. {missing['adults']} adults, including {missing['users']} users, have incomplete histories and are excluded only from these complete-history comparisons; they remain in the main cohort. {cohort['incomplete_history_with_out_of_scope_months']} incomplete histories include out-of-scope months.

| Monthly history | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | ---: | ---: | ---: |
{pair_table('monthly_history')}

## Source combinations among people covered in every month

Preserve simultaneous private, TRICARE/CHAMPVA, Medicare, Medicaid/SCHIP, VA and other public sources. A changed combination is not necessarily a lapse in coverage, and a constant combination does not exclude a change of plan within one source type.

| Source history | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | ---: | ---: | ---: |
{pair_table('source_changes')}

![Monthly insurance histories](monthly-insurance.png)

Triangles and asterisks indicate limited precision. Withheld values are not zero. A use proportion can be displayed while the corresponding user-only spending mean is withheld because their denominators differ.

PURCHRD identifies a survey round; RXBEGMM/RXBEGYRX identify first use and can carry forward across records. They cannot date every refill. Annual payments are not spread evenly across months. These results do not identify formularies, denials, unmet need or causal effects.

Sources: [HC-256 insurance](https://meps.ahrq.gov/data_stats/download_data/pufs/h256/h256doc.shtml), [HC-254A timing](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml), [AHRQ precision](https://meps.ahrq.gov/survey_comp/precision_guidelines.shtml).
'''
text=f'''# Supplementary age, insurance and payment analyses

The [main report](research-brief.md) focuses on payment sources and user spending. These supplementary estimates use the same descriptive reporting framework. The age and monthly-history questions were developed after examining initial results; they are not original preregistrations.

## Reporting framework

{rules}

## Age and annual coverage

The five age groups are 18–34, 35–49, 50–64, 65–74 and 75+. Any-private annual coverage includes TRICARE/CHAMPVA and mixed private/public coverage under the MEPS definition. Use proportions include all adults in each group; spending means include observed users and retain zero payments. These denominators differ, so one outcome may be displayed while another is withheld.

![Age and annual coverage](detailed-age.png)

| Age | Annual coverage | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | --- | ---: | ---: | ---: |
{pair_table('detailed_age')}

## Monthly histories

See the [coverage appendix](coverage-appendix.md). These categories do not establish purchase-specific drug coverage.

## Recorded payment sources

Sum ten edited/imputed source-payment fields over target prescriptions within each person. Other sources combine VA/CHAMPVA, other federal, state/local, workers' compensation and other insurance. Source-specific means include all observed adult users, including zero payments. Shares divide each weighted source total by weighted total payments. Positive-payment contributors can overlap and are diagnostic counts, not separate reporting gates.

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
{payer_table('All adults')}

![Payment sources](payment-sources.png)

Do not add confidence limits or renormalize visible shares if a component is withheld. Zero payment does not establish denial. Payments exclude manufacturer rebates to payers; these edited/imputed survey records are not raw adjudicated claims.

## Age-adjusted association

The separate survey quasibinomial model uses a natural age spline (3 df) and annual coverage with no interaction. It standardizes any-private and public-only predictions to their combined weighted adult population; uninsured adults remain in descriptive estimates but are outside this model. Model status: {model['status']}.

The model retains its prespecified support checks (at least 100 adults, 5 users and 5 nonusers per coverage-by-age cell), convergence, rank and finite covariance checks. Those are model-feasibility diagnostics, not descriptive reporting thresholds. Small descriptive cells can contribute to a pooled model with a smooth common age relationship. The model does not create new observations.

| Group or comparison | Metric | Estimate (95% CI) |
| --- | --- | ---: |
{adjusted_table}

Marginal percentages use the unified denominator/precision framework, with model-based logit-delta intervals. The public-minus-private contrast uses both margins' covariance and is not screened by RSE because a signed difference can legitimately be near zero. Both margins must be displayable. Only age is adjusted; disease burden, indication, income, drug mix and selection can differ. No causal insurance effect or adjusted spending model is estimated.

## Checks

There are {design['extension_rows']} descriptive rows: {design['reportable']} displayed without a flag, {design['flagged']} displayed with a precision flag and {design['suppressed']} withheld. Independent calculations reconstruct {design['independent_mean_ratio_checks']} weighted points and full-design Taylor standard errors. See [design audit](extension-design-audit.json), [cohort audit](extension-cohort-audit.json), [aggregate estimates](extension-estimates.csv), [model support](age-adjustment-support.csv) and [adjusted results](age-adjusted-use.csv).

## Payer components by age

Every mean includes all users in its age group, including zero source payments. Display decisions use the same descriptive rules.

{age_payments}
'''
(ROOT/'results/coverage-appendix.md').write_text(appendix)
(ROOT/'results/extension-note.md').write_text(text)
print('Generated current supplementary reports under the unified descriptive framework.')
