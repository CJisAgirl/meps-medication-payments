"""Cross-output acceptance checks for the complete extension."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    base = pd.read_csv(ROOT/'data/processed/persons.csv', dtype={'DUPERSID': str})
    extended = pd.read_csv(ROOT/'data/processed/extension-persons.csv', dtype={'DUPERSID': str})
    pd.testing.assert_frame_equal(base, extended[base.columns], check_exact=True)
    rows = pd.read_csv(ROOT/'results/extension-estimates.csv')
    old = pd.read_csv(ROOT/'results/estimates.csv')
    cohort = json.loads((ROOT/'results/extension-cohort-audit.json').read_text())
    design = json.loads((ROOT/'results/extension-design-audit.json').read_text())
    assert len(rows)==5*4*2 + 3*2 + 2*2 + 6*6*2
    assert not rows.duplicated(['analysis','age','group','metric']).any()
    fields=['estimate','se','lower_95','upper_95','rse']
    kept = rows.status.eq('reportable') | rows.status.str.startswith('flagged:')
    assert rows.loc[~kept, fields].isna().all().all()
    assert np.isfinite(rows.loc[kept, fields].to_numpy()).all()
    expected_n=np.where(rows.metric.eq('prevalence_pct'),rows.unweighted_adults,rows.unweighted_users)
    assert np.array_equal(rows.denominator_n,expected_n)
    assert rows.loc[kept,'denominator_n'].ge(60).all()
    assert rows.loc[kept,'design_df'].gt(0).all()
    assert rows.loc[rows.status.eq('reportable'),'rse'].lt(.30).all()
    flagged=rows.status.eq('flagged: low precision')
    assert rows.loc[flagged,'rse'].between(.30,.50).all()
    rare=rows.status.eq('flagged: rare, low precision')
    assert rows.loc[rare,'metric'].eq('prevalence_pct').all()
    assert rows.loc[rare,'rse'].gt(.50).all() and rows.loc[rare,'upper_95'].le(10).all()
    assert not rows.status.str.contains('positive-payer|adult n < 100|user n < 30').any()
    assert (rows.loc[kept,'lower_95']<=rows.loc[kept,'estimate']).all()
    assert (rows.loc[kept,'estimate']<=rows.loc[kept,'upper_95']).all()
    pct = kept & rows.metric.eq('prevalence_pct')
    assert rows.loc[pct,'lower_95'].ge(0).all() and rows.loc[pct,'upper_95'].le(100).all()
    for kind in ['adults','users']:
        total=sum(g[kind] for g in cohort['monthly_history_counts'].values())
        assert total==cohort['adult_n' if kind=='adults' else 'user_n']
        stable=sum(v[kind] for k,v in cohort['source_history_counts'].items() if k!='not_all_12')
        assert stable==cohort['monthly_history_counts']['all_12'][kind]
    for ins in ['All coverage','Any private incl. TRICARE','Public only','Uninsured all year']:
        z=rows.loc[(rows.analysis=='detailed_age') & (rows.group==ins) & (rows.metric=='prevalence_pct')]
        b=old.loc[(old.drug=='primary') & (old.population=='All adults') & (old.insurance==ins) & (old.metric=='prevalence_pct')].iloc[0]
        assert z.unweighted_adults.sum()==b.unweighted_adults
        assert z.unweighted_users.sum()==b.unweighted_users
    for newmetric,oldmetric in [('annual_payment_usd','annual_oop_usd'),('payment_share_pct','oop_share_pct')]:
        z=rows.loc[(rows.analysis=='payment_sources') & (rows.age=='All adults') & (rows.group=='Self/family') & (rows.metric==newmetric)].iloc[0]
        b=old.loc[(old.drug=='primary') & (old.population=='All adults') & (old.insurance=='All coverage') & (old.metric==oldmetric)].iloc[0]
        assert np.allclose(z[fields[:4]].astype(float), b[fields[:4]].astype(float),rtol=1e-10,atol=1e-10)
    p=extended.loc[extended.PERWT24F.gt(0)].copy()
    m=p.AGELAST.ge(18)&p.user.eq(1)
    source_cols=dict(zip(['Self/family','Private insurance','Medicare','Medicaid','TRICARE','Other sources'],
                         ['pay_self','pay_private','pay_medicare','pay_medicaid','pay_tricare','pay_other']))
    for source,col in source_cols.items():
        for metric in ['annual_payment_usd','payment_share_pct']:
            z=rows.loc[(rows.analysis=='payment_sources')&(rows.age=='All adults')&(rows.group==source)&(rows.metric==metric)].iloc[0]
            assert z.positive_payer_users==int((m&p[col].gt(0)).sum())
            if z.status.startswith('withheld:'): continue
            den=p.total*m if metric=='payment_share_pct' else m.astype(float)
            num=p[col]*m; W=(p.PERWT24F*den).sum(); e=(p.PERWT24F*num).sum()/W
            influence=p.PERWT24F*(num-e*den)/W
            totals=influence.groupby([p.VARSTR,p.VARPSU]).sum()
            variance=totals.groupby(level=0).agg(['count','var'])
            se=np.sqrt((variance['count']*variance['var']).sum())
            scale=100 if metric=='payment_share_pct' else 1
            assert np.allclose([z.estimate,z.se],[e*scale,se*scale],rtol=1e-9,atol=1e-9)
    tricare=rows.loc[(rows.analysis=='payment_sources')&(rows.age=='All adults')&(rows.group=='TRICARE')]
    assert tricare.positive_payer_users.eq(20).all()
    assert not tricare.status.str.contains('positive-payer').any()
    adj=pd.read_csv(ROOT/'results/age-adjusted-use.csv')
    if design['age_adjustment']['support_gate']:
        assert len(adj)==3
        valid=adj.status.eq('reportable') | adj.status.str.startswith('flagged:')
        assert adj.loc[~valid,['estimate','se','lower_95','upper_95']].isna().all().all()
        if valid.all():
            assert np.isclose(adj.iloc[2].estimate,adj.iloc[1].estimate-adj.iloc[0].estimate)
        assert (adj.loc[valid,'lower_95']<=adj.loc[valid,'estimate']).all() and (adj.loc[valid,'estimate']<=adj.loc[valid,'upper_95']).all()
        for key in ['point_reconstruction','two_component_covariance_reconstruction','intercept_only_crude_check']:
            assert design['age_adjustment'][key]=='PASS'
    assert design['extension_rows']==len(rows)
    assert design['reportable']==int(rows.status.eq('reportable').sum())
    assert design['flagged']==int(rows.status.str.startswith('flagged:').sum())
    assert design['displayed']==int(kept.sum())
    assert design['suppressed']==int((~kept).sum())
    for file in ['detailed-age.png','monthly-insurance.png','payment-sources.png']:
        assert (ROOT/'results'/file).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    print('PASS: base cohort equality, age/history partitions, payer denominators, suppression, CIs and model outputs.')


if __name__=='__main__':
    main()
