"""Add monthly histories and payment components without altering the base cohort."""
from pathlib import Path
import json
import sqlite3
import numpy as np
import pandas as pd
from prepare import classify

ROOT = Path(__file__).resolve().parents[1]
MONTHS = ['JA', 'FE', 'MA', 'AP', 'MY', 'JU', 'JL', 'AU', 'SE', 'OC', 'NO', 'DE']
SOURCES = {'private': ('PRI', '24'), 'tricare': ('TRI', '24X'),
           'medicare': ('MCR', '24X'), 'medicaid': ('MCD', '24X'),
           'va': ('VAP', '24'), 'other_public': ('GVA', '24')}
PAYMENTS = {'pay_self': ['RXSF24X'], 'pay_private': ['RXPV24X'],
            'pay_medicare': ['RXMR24X'], 'pay_medicaid': ['RXMD24X'],
            'pay_tricare': ['RXTR24X'],
            'pay_other': ['RXVA24X', 'RXOF24X', 'RXSL24X', 'RXWC24X', 'RXOT24X']}
INS_COLS = [f'INS{m}24X' for m in MONTHS]
SOURCE_COLS = [f'{prefix}{m}{suffix}' for prefix, suffix in SOURCES.values() for m in MONTHS]


def insurance_history(frame):
    """Explicit known-month categories; -1/out of scope never becomes uninsured."""
    ins = frame[INS_COLS]
    source = frame[SOURCE_COLS]
    allowed = [-1, -7, -8, -9, -15, 1, 2]
    for block in (ins, source):
        if not (block.isin(allowed) | block.isna()).all().all():
            raise ValueError('Unexpected monthly insurance code')
    complete = ins.isin([1, 2]).all(axis=1)
    covered = ins.eq(1).sum(axis=1)
    # Independently cross-check any-coverage against all six observed sources.
    for m in MONTHS:
        cols = [f'{prefix}{m}{suffix}' for prefix, suffix in SOURCES.values()]
        known = frame[cols].isin([1, 2]).all(axis=1) & frame[f'INS{m}24X'].isin([1, 2])
        if (frame.loc[known, cols].eq(1).any(axis=1) != frame.loc[known, f'INS{m}24X'].eq(1)).any():
            raise ValueError('Monthly any-coverage contradicts source flags')
    history = pd.Series('incomplete', index=frame.index)
    history.loc[complete & covered.eq(12)] = 'all_12'
    history.loc[complete & covered.between(1, 11)] = 'some_months'
    history.loc[complete & covered.eq(0)] = 'none_12'
    source_complete = source.isin([1, 2]).all(axis=1)
    # A bitmask preserves overlapping coverage, including Medicare plus private.
    patterns = pd.DataFrame({m: sum((frame[f'{prefix}{m}{suffix}'].eq(1).astype(int) * 2**j)
                            for j, (prefix, suffix) in enumerate(SOURCES.values())) for m in MONTHS})
    mix = pd.Series('not_all_12', index=frame.index)
    mix.loc[history.eq('all_12')] = 'source_unknown'
    eligible = history.eq('all_12') & source_complete
    mix.loc[eligible & patterns.nunique(axis=1).eq(1)] = 'stable_sources'
    mix.loc[eligible & patterns.nunique(axis=1).gt(1)] = 'changed_sources'
    return pd.DataFrame({'monthly_history': history, 'source_history': mix,
                         'known_insurance_months': ins.isin([1, 2]).sum(axis=1),
                         'covered_months': covered.where(complete, -1),
                         'out_of_scope_months': ins.eq(-1).sum(axis=1)}, index=frame.index)


def aggregate_payments(events):
    """Target-only payer aggregation and independent SQL/pandas reconciliation."""
    raw_cols = sum(PAYMENTS.values(), [])
    if events.RXRECIDX.isna().any() or events.RXRECIDX.duplicated().any():
        raise ValueError('Missing/duplicate prescription ID')
    if events.DUPERSID.isna().any():
        raise ValueError('Missing person ID')
    amounts = events[raw_cols + ['RXXP24X']]
    if not np.isfinite(amounts.to_numpy()).all() or amounts.lt(0).any().any():
        raise ValueError('Missing/negative payer payment')
    residual = events[raw_cols].sum(axis=1) - events.RXXP24X
    if residual.abs().gt(.06000001).any():
        raise ValueError('Payment sources do not sum to total')
    e = events.copy()
    for dest, cols in PAYMENTS.items():
        e[dest] = e[cols].sum(axis=1)
    grouped = e.groupby('DUPERSID')[list(PAYMENTS) + ['RXXP24X']].sum()
    with sqlite3.connect(':memory:') as conn:
        e[['DUPERSID'] + raw_cols + ['RXXP24X']].to_sql('rx', conn, index=False)
        expressions = [f"SUM({' + '.join(cols)}) AS {dest}" for dest, cols in PAYMENTS.items()]
        query = 'SELECT DUPERSID, ' + ', '.join(expressions) + ', SUM(RXXP24X) AS RXXP24X FROM rx GROUP BY DUPERSID'
        sql = pd.read_sql_query(query, conn).set_index('DUPERSID').sort_index()
    if not np.allclose(sql.to_numpy(), grouped.sort_index().to_numpy(), atol=1e-8, rtol=1e-10):
        raise AssertionError('SQL/pandas payer totals disagree')
    return grouped, float(residual.abs().max()) if len(residual) else 0.0


def main():
    base = pd.read_csv(ROOT/'data/processed/persons.csv', dtype={'DUPERSID': str})
    p = pd.read_stata(ROOT/'data/raw/h256.dta', columns=['DUPERSID'] + INS_COLS + SOURCE_COLS,
                      convert_categoricals=False)
    p.DUPERSID = p.DUPERSID.astype(str)
    if p.DUPERSID.duplicated().any() or set(p.DUPERSID) != set(base.DUPERSID):
        raise ValueError('Extension person membership differs from base')
    histories = pd.concat([p[['DUPERSID']], insurance_history(p)], axis=1)
    e = pd.read_stata(ROOT/'data/raw/h254a.dta', columns=['DUPERSID', 'RXRECIDX', 'RXDRGNAM', 'RXNAME', 'RXXP24X'] + sum(PAYMENTS.values(), []), convert_categoricals=False)
    e.DUPERSID = e.DUPERSID.astype(str)
    if not set(e.DUPERSID).issubset(set(base.DUPERSID)):
        raise ValueError('Unknown prescription person')
    flags = [classify(g, n)[1] for g, n in zip(e.RXDRGNAM, e.RXNAME)]
    e = e.loc[np.array(flags) == 1].copy()
    pay, max_residual = aggregate_payments(e)
    out = base.merge(histories, on='DUPERSID', validate='one_to_one', how='left')
    out = out.merge(pay.drop(columns='RXXP24X'), left_on='DUPERSID', right_index=True, validate='one_to_one', how='left')
    out[list(PAYMENTS)] = out[list(PAYMENTS)].fillna(0)
    if not np.allclose(out.pay_self, out.oop, atol=1e-8, rtol=1e-10):
        raise AssertionError('Self payments changed from base')
    check_total = pay.RXXP24X.reindex(out.DUPERSID, fill_value=0).to_numpy()
    if not np.allclose(check_total, out.total, atol=1e-8, rtol=1e-10):
        raise AssertionError('Total payments changed from base')
    if not out.loc[out.user.eq(0), list(PAYMENTS)].eq(0).all().all():
        raise AssertionError('Non-user has target payment')
    out.to_csv(ROOT/'data/processed/extension-persons.csv', index=False)
    adults = out.loc[(out.PERWT24F > 0) & (out.AGELAST >= 18)]
    audit = {'adult_n': len(adults), 'user_n': int(adults.user.sum()),
             'monthly_history_counts': adults.groupby('monthly_history').agg(adults=('user', 'size'), users=('user', 'sum')).to_dict('index'),
             'source_history_counts': adults.groupby('source_history').agg(adults=('user', 'size'), users=('user', 'sum')).to_dict('index'),
             'incomplete_history_with_out_of_scope_months': int(((adults.monthly_history == 'incomplete') & (adults.out_of_scope_months > 0)).sum()),
             'max_event_payment_reconciliation_usd': max_residual,
             'sql_vs_pandas_components': 'PASS', 'base_cohort_reconciliation': 'PASS',
             'monthly_source_consistency': 'PASS'}
    (ROOT/'results/extension-cohort-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
