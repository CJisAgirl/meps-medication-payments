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
    if row['status'] != 'reportable':
        return 'Withheld: ' + row['status'].removeprefix('suppressed: ')
    return f"{float(row['estimate']):,.{digits}f} ({float(row['lower_95']):,.{digits}f}–{float(row['upper_95']):,.{digits}f})"


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


private=find('payment_sources','Private insurance','payment_share_pct')
medicare=find('payment_sources','Medicare','payment_share_pct')
medicaid=find('payment_sources','Medicaid','payment_share_pct')
selfpay=find('payment_sources','Self/family','payment_share_pct')
missing=cohort['monthly_history_counts'].get('incomplete',{'adults':0,'users':0})
adjusted_table='\n'.join(f"| {r['group']} | {r['metric']} | {show(r)} |" for r in adjusted)
model=design['age_adjustment']
if all(r['status']=='reportable' for r in adjusted):
    a,b,d=adjusted
    includes_zero=float(d['lower_95'])<=0<=float(d['upper_95'])
    interval_sentence=('The interval includes zero; this does not establish equality.' if includes_zero
                       else 'The interval excludes zero under this age-only model; this does not establish causation.')
    adjusted_summary=(f"Age-only standardized use was {show(a)}% for any-private coverage and {show(b)}% for public-only coverage. "
                      f"The public-minus-private difference was {show(d)} percentage points. {interval_sentence} The model does not identify a causal insurance effect.")
    adjusted_zh=(f"把两组放到相同参考年龄分布下，模型估计的使用比例为私人保险{show(a)}%、公共保险{show(b)}%。"
                 f"差值为{show(d)}个百分点。括号为95%置信区间。"
                 + ('差值区间包含0，不表示已证明完全相同。' if includes_zero else '差值区间不包含0，但仍然不是因果效果。'))
else:
    adjusted_summary='The age-only standardized comparison was withheld because its model/support or margin reporting gate failed.'
    adjusted_zh='本轮模型支持或结果报告门槛未通过，因此暂不报告年龄调整后的比较。'
model_description=(f"Use a survey-weighted quasibinomial model with a natural cubic spline of age (3 df, internal knots {model.get('spline_knots')}, boundaries 18 and top-coded 85) and annual coverage. There is no age-by-coverage interaction. Standardize predictions to the combined survey-weighted age distribution of {model.get('reference_adults'):,} any-private/public-only adults ({model.get('reference_users'):,} users)." if model['support_gate'] else 'Model support was insufficient for the planned age-only comparison.')
age_payments='\n\n'.join(f"### {age}\n\n| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |\n| --- | ---: | ---: | ---: |\n{payer_table(age)}" for age in ['18-34','35-49','50-64','65-74','75+'])
text=f'''# Finer age groups, monthly insurance histories and who paid

**MEPS 2024 · Follow-up specified 11 October 2026**

This extension examines finer age groups, monthly insurance histories and recorded payment sources, including the limits of linking insurance to individual medicine acquisitions. The [analysis methods](../METHODS.md#supplementary-analyses) records choices after seeing the first analysis and age-by-insurance counts, before estimating follow-up outcomes. It is not an original preregistration. The first-run estimates remain available unchanged.

## Findings and practical limits

- Finer age groups reveal where estimates are supported and where they are not. The 18–34 any-private and public-only samples contain 24 and 16 users; the 35–49 public-only sample contains 26. Those cells fail the existing user-count gate. Sample counts are not weighted national estimates.
- In the complete 12-month histories, 764 users had coverage in every month, 29 had some fully uninsured months, and 5 were uninsured in all 12 months. The latter two outcome estimates are withheld. We do not lower the 30-user gate because a group has 29 users.
- Of estimated target-medicine payments, private insurance accounted for {show(private)}%, Medicare {show(medicare)}%, Medicaid {show(medicaid)}%, and self/family {show(selfpay)}%. These are ratios of weighted payment sums, not average personal copayment percentages. The TRICARE component is withheld because only 20 users had a positive TRICARE payment.
- {adjusted_summary}

## 1. Detailed age and annual coverage

The five age bins and reporting gates were fixed before extension outcome estimation. “Any private” retains the MEPS convention including TRICARE/CHAMPVA and mixed public/private coverage. OOP is annual self/family spending among observed users, including zero payments. Confidence intervals are survey-design intervals; blank/withheld results are not zero.

![Detailed age and annual insurance estimates](detailed-age.png)

| Age | Annual coverage | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | --- | ---: | ---: | ---: |
{pair_table('detailed_age')}

## 2. Monthly histories, without inventing purchase dates

Require all 12 INS monthly indicators to be explicitly yes/no. “Covered in every month” means coverage at some point in each month, not coverage on every day. “Some fully uninsured months” means 1–11 months with any coverage and at least one month without coverage. Out-of-scope and unknown values are never converted to uninsured. The complete-history restriction changes the analysis population.

{missing['adults']} adults, including {missing['users']} users, have incomplete monthly histories and are excluded only from the complete-history comparisons. They remain in the original all-adult results. {cohort['incomplete_history_with_out_of_scope_months']} incomplete histories include out-of-scope months. Uninsured-all-12 counts therefore differ from the original annual-category counts based on eligible months.

| Monthly history | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | ---: | ---: | ---: |
{pair_table('monthly_history')}

Among people covered in all 12 months, a second comparison uses the monthly combination of private, TRICARE/CHAMPVA, Medicare, Medicaid/SCHIP, VA and other public indicators. Multiple simultaneous sources are preserved. A changed combination does not necessarily mean a period without insurance, and a constant combination does not rule out changing plans within one source type. These are descriptive comparisons; health status and age may differ between groups.

| Source history among all-month-covered adults | Sample users / adults | Observed use, % (95% CI) | Annual OOP per user, USD (95% CI) |
| --- | ---: | ---: | ---: |
{pair_table('source_changes')}

![Monthly insurance and source histories](monthly-insurance.png)

**No month-of-purchase linkage is claimed.** PURCHRD identifies the survey round; RXBEGMM/RXBEGYRX identify first use and can be carried forward to subsequent records. They do not date every refill. Annual payments are not allocated evenly across months. No drug formulary, denial or unmet-need measure is inferred.

## 3. Actual recorded payment sources

Aggregate all ten edited/imputed source-payment variables over each person's target-drug records. The six displayed components are exhaustive before suppression. “Other” combines VA/CHAMPVA, other federal, state/local, workers' compensation and other insurance. TRICARE is shown separately even though annual INSCOV24 groups it with any-private coverage.

The denominator for annual component means is **all observed adult users**, including those with zero payment from that source; it is not only people paid for by that payer. The share denominator is weighted total target-drug payments. Source-specific outputs require at least 30 users with positive payment from that component in addition to the original precision gate. Positive-payer users can overlap across sources.

| Payment source | Users with positive payment | Annual USD per user (95% CI) | Share of payments, % (95% CI) |
| --- | ---: | ---: | ---: |
{payer_table('All adults')}

![Payment sources, all adult users](payment-sources.png)

Do not add displayed confidence bounds or renormalize visible components to 100% when another component is withheld. A payment of zero does not establish no drug benefit or a denial. Payments exclude manufacturer rebates to payers; medicine names and amounts may be edited/imputed. These are survey records, not raw adjudicated claims.

## 4. Age-adjusted association: observed use only

{model_description} Uninsured adults are outside this model, not dropped from the original descriptive estimates.

The support diagnostic is recorded in the audit and support table. Small cells can be withheld as standalone estimates while still contributing to a pooled model that explicitly imposes a smooth common age relationship, if the prespecified model-support gate passes. This adds modeling assumptions; it does not create more observations.

| Group or comparison | Metric | Estimate (95% CI) |
| --- | --- | ---: |
{adjusted_table}

The signed difference is public-only minus any-private, in percentage points. Its interval uses the covariance of both margins, rather than assuming they are independent. The RSE gate applies to the margins, not to a signed contrast near zero. Intervals use the residual design degrees of freedom ({model.get('df','not available')}); margin intervals use a logit-delta transformation. Model convergence, rank, support and finite covariance are checked. survey::svypredmeans combines model and standardized-prediction distribution variance components; both are independently reconstructed when the model is estimated.

Only age is adjusted. Disease burden, indication, income, drug mix, coverage timing and selection remain potential differences. No claim is made about how much of the crude gap age “explains.” An adjusted spending model is not fitted; the distribution of spending and selection into observed use need a separate plan.

## Validation and reproduction

Run `python3 run.py` from the project directory to reproduce both the original analysis and this extension. The extension adds six unit tests (12 total), {design['independent_mean_ratio_checks']} independently recomputed point estimates and Taylor SEs, manual predictive-margin point/covariance checks, and an intercept-only comparison against crude survey means. Payment components reconcile to event totals and independently to SQL/person sums. The original 71 checks also remain in the full run.

Read [cohort audit](extension-cohort-audit.json), [design audit](extension-design-audit.json), [aggregate results](extension-estimates.csv), [model support](age-adjustment-support.csv), [adjusted use](age-adjusted-use.csv). The extension contains {design['extension_rows']} descriptive result rows: {design['reportable']} reportable and {design['suppressed']} withheld under fixed gates.

Primary documentation: [HC-256 insurance](https://meps.ahrq.gov/data_stats/download_data/pufs/h256/h256doc.shtml), [HC-254A timing/payments](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml), [survey predictive margins](https://r-survey.r-forge.r-project.org/pkgdown/docs/reference/svypredmeans.html). Independent analysis of AHRQ public-use data.


## Appendix: payer components by age

Every age-specific mean uses all users in that age group, including zero payments from the particular source. Apply contributor and precision gates separately to each component; the underlying people need not be distinct across payment sources.

{age_payments}
'''
# Keep old links usable, but move monthly histories out of the main narrative.
monthly_heading = "## 2. Monthly histories, without inventing purchase dates"
start = text.index(monthly_heading)
end = text.index("## 3. Actual recorded payment sources", start)
monthly = text[start:end]
appendix = """# Appendix: what monthly insurance histories can and cannot establish

**Historical exploratory results; not a purchase-specific coverage analysis.**

The main study now focuses on [actual payment sources and user spending](research-brief.md). These categories describe insurance continuity, but cannot date every refill or establish drug-benefit eligibility. Sparse groups also limit comparisons. The original numerical estimates and people are retained, not discarded as invalid data.

The legacy 30-user gate remains here for historical reproducibility. It is a project rule, not a mathematical boundary or a uniform AHRQ requirement. The new payment distribution uses estimand-specific rules documented in [payment methods](../METHODS.md#payment-distribution); changing a reporting rule cannot recover missing purchase dates.

""" + monthly + "\nSources: [HC-256 insurance](https://meps.ahrq.gov/data_stats/download_data/pufs/h256/h256doc.shtml), [HC-254A timing](https://meps.ahrq.gov/data_stats/download_data/pufs/h254a/h254adoc.shtml).\n"
(ROOT/'results/coverage-appendix.md').write_text(appendix)
text = text[:start] + monthly_heading + "\n\nThe unchanged monthly tables and figure are now in the [coverage-methods appendix](coverage-appendix.md). They are not evidence of purchase-specific reimbursement.\n\n" + text[end:]
first = text.index("## Findings and practical limits")
end = text.index("## 1. Detailed age and annual coverage")
text = text[:first] + "The [current main report](research-brief.md) answers who paid and how self/family payments were distributed. The analyses below are supplementary. Legacy gates are retained for reproducibility, not asserted to be universally appropriate; withheld values are not deleted people.\n\n" + text[end:]
text = text.replace("# Finer age groups, monthly insurance histories and who paid", "# Supplementary age, insurance and payment analyses")
text = text.replace("six unit tests (12 total)", "six Python unit tests (12 Python tests across the original and extension workflows)")
(ROOT/'results/extension-note.md').write_text(text)
print('Generated the age supplement and coverage appendix.')
