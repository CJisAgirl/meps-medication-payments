"""Independent weighted distribution and cross-output checks (no microdata output)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
p = pd.read_csv(ROOT/'data/processed/extension-persons.csv',dtype={'DUPERSID':str})
p = p.loc[p.PERWT24F.gt(0)].copy()
mask = p.AGELAST.ge(18) & p.user.eq(1)
u = p.loc[mask]
assert len(u)==800 and not p.DUPERSID.duplicated().any()
assert np.allclose(u.oop,u.pay_self,atol=1e-8,rtol=0)
result = pd.read_csv(ROOT/'results/payment-distribution.csv').set_index('metric')
assert result.index.is_unique and len(result)==9
assert result.denominator_users.eq(len(u)).all()
visible = ~result.status.str.startswith('withheld:')
assert result.loc[~visible,['estimate','se','lower_95','upper_95']].isna().all().all()
assert np.isfinite(result.loc[visible,['estimate','se','lower_95','upper_95']]).all().all()
assert (result.loc[visible,'lower_95']<=result.loc[visible,'estimate']).all()
assert (result.loc[visible,'estimate']<=result.loc[visible,'upper_95']).all()

def manual(x):
    denom = p.loc[mask,'PERWT24F'].sum()
    estimate = (p.PERWT24F*x*mask).sum()/denom
    influence = p.PERWT24F*mask*(x-estimate)/denom
    totals = influence.groupby([p.VARSTR,p.VARPSU]).sum()
    variances = totals.groupby(level=0).agg(['count','var'])
    return estimate, np.sqrt((variances['count']*variances['var']).sum())

metrics = {'mean_oop':p.oop, 'zero_oop_pct':p.oop.eq(0),
           'oop_0_100_pct':p.oop.gt(0)&p.oop.le(100),
           'oop_100_500_pct':p.oop.gt(100)&p.oop.le(500),
           'oop_500_1000_pct':p.oop.gt(500)&p.oop.le(1000),
           'oop_over_1000_pct':p.oop.gt(1000)}
checks = 0
for metric,x in metrics.items():
    row = result.loc[metric]
    point,se = manual(x.astype(float))
    scale = 1 if metric=='mean_oop' else 100
    if visible.loc[metric]:
        assert np.allclose([row.estimate,row.se],np.array([point,se])*scale,rtol=1e-9,atol=1e-9)
        checks += 1
    if metric!='mean_oop':
        assert row.sample_in_category==int(x[mask].sum())
bands = result.loc[result.kind.eq('proportion')]
assert bands.sample_in_category.sum()==len(u)
if (~bands.status.str.startswith('withheld:')).all():
    assert np.isclose(bands.estimate.sum(),100)
    assert bands.lower_95.ge(0).all() and bands.upper_95.le(100).all()

# Independent implementation: combine equal dollar values before CDF inversion.
weighted = u.groupby('oop').PERWT24F.sum().sort_index()
cumulative = weighted.cumsum()/weighted.sum()
for metric,prob in [('median_oop',.5),('p75_oop',.75),('p90_oop',.9)]:
    row = result.loc[metric]
    expected = cumulative.index[np.flatnonzero(cumulative.to_numpy()>=prob)[0]]
    if visible.loc[metric]:
        assert np.isclose(row.estimate,expected,rtol=0,atol=1e-9)
        assert row.users_at_or_below==int(u.oop.le(expected).sum())
        assert row.users_at_or_above==int(u.oop.ge(expected).sum())
        assert row.users_at_or_below>=30 and row.users_at_or_above>=30

original = pd.read_csv(ROOT/'results/estimates.csv')
old = original.loc[(original.drug=='primary') & (original.population=='All adults') &
                   (original.insurance=='All coverage') & (original.metric=='annual_oop_usd')].iloc[0]
fields = ['estimate','se','lower_95','upper_95']
assert np.allclose(result.loc['mean_oop',fields].astype(float),old[fields].astype(float),rtol=1e-10,atol=1e-10)
assert (ROOT/'results/selfpay-distribution.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
main = (ROOT/'results/research-brief.md').read_text()
assert 'coverage-appendix.md' in main and 'monthly-insurance.png' not in main
appendix = (ROOT/'results/coverage-appendix.md').read_text()
assert 'monthly-insurance.png' in appendix and '1194' in appendix
assert '88.03' in main and '24.62' in main and '9.02' in main
assert (ROOT/'METHODS.md').is_file() and (ROOT/'README.md').is_file()
audit = {'status':'PASS','independent_python_point_and_se_checks':checks,
         'independent_python_quantile_checks':3,'band_counts_partition_users':True,
         'same_original_mean_ci_and_se':True,'zero_total_users_retained':int(u.total.eq(0).sum()),
         'main_and_appendix_navigation':'PASS'}
(ROOT/'results/payment-verification.json').write_text(json.dumps(audit,indent=2)+'\n')
print('PASS: independent Python distribution/quantiles, full-design SEs, denominators, old mean and report navigation.')
