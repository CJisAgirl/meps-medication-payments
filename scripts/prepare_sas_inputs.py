"""Export original MEPS columns for SAS; no drug classification or aggregation here."""
from pathlib import Path
import csv
import hashlib
import io
import json
import math
import re
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PERSON_COLUMNS = ['DUPERSID', 'AGELAST', 'INSCOV24', 'PERWT24F', 'VARSTR', 'VARPSU']
PAYER_COLUMNS = ['RXSF24X', 'RXPV24X', 'RXMR24X', 'RXMD24X', 'RXTR24X',
                 'RXVA24X', 'RXOF24X', 'RXSL24X', 'RXWC24X', 'RXOT24X']
RX_COLUMNS = ['DUPERSID', 'RXRECIDX', 'RXDRGNAM', 'RXNAME', 'PERWT24F', 'RXXP24X'] + PAYER_COLUMNS
CHAR_LENGTHS = {'DUPERSID': 10, 'RXRECIDX': 19, 'RXDRGNAM': 200, 'RXNAME': 200}


def read_source(root, name, columns):
    manifest = json.loads((root / 'results/source-manifest.json').read_text())
    archive = root / f'data/raw/{name}dta.zip'
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest[name]['sha256']:
        raise ValueError(f'Official source bytes changed: {name}')
    with zipfile.ZipFile(archive) as z:
        members = [m for m in z.namelist() if m.lower().endswith('.dta')
                   and not m.startswith('__MACOSX/') and not Path(m).name.startswith('._')]
        if len(members) != 1:
            raise ValueError('Expected exactly one Stata member')
        return pd.read_stata(io.BytesIO(z.read(members[0])), columns=columns, convert_categoricals=False)


def write_input(frame, columns, path):
    if list(frame.columns) != columns:
        frame = frame.loc[:, columns]
    for name, limit in CHAR_LENGTHS.items():
        if name in frame:
            s = frame[name].fillna('').astype(str)
            if s.str.len().gt(limit).any() or s.str.contains(r'[\r\n]').any():
                raise ValueError(f'{name}: value would be truncated or split by SAS input')
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format='%.17g', na_rep='')
    loaded = pd.read_csv(path, dtype={k: str for k in CHAR_LENGTHS if k in columns},
                         keep_default_na=False, float_precision='round_trip')
    if len(loaded) != len(frame) or list(loaded.columns) != columns:
        raise AssertionError('CSV serialization changed the input dimensions')
    for name in columns:
        if name in CHAR_LENGTHS:
            if not loaded[name].equals(frame[name].fillna('').astype(str).reset_index(drop=True)):
                raise AssertionError(f'Character values changed: {name}')
        else:
            observed = pd.to_numeric(loaded[name].mask(loaded[name].eq('')))
            expected = pd.to_numeric(frame[name]).reset_index(drop=True)
            if not ((observed == expected) | (observed.isna() & expected.isna())).all():
                raise AssertionError(f'Numeric values changed: {name}')
    return {'rows': len(frame), 'columns': columns,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def reference_block(root=ROOT):
    def read(name):
        with (root / 'results' / name).open() as f:
            return list(csv.DictReader(f))
    distribution = read('payment-distribution.csv')
    main = [r for r in read('estimates.csv') if r['drug'] == 'primary'
            and r['population'] == 'All adults' and r['insurance'] == 'All coverage']
    means = [(r['metric'], r['estimate'], r['se']) for r in distribution if r['kind'] != 'quantile']
    means += [('prevalence_pct', r['estimate'], r['se']) for r in main if r['metric'] == 'prevalence_pct']
    quantiles = [(r['metric'], r['estimate']) for r in distribution if r['kind'] == 'quantile']
    expected_means = {'mean_oop', 'zero_oop_pct', 'oop_0_100_pct', 'oop_100_500_pct',
                      'oop_500_1000_pct', 'oop_over_1000_pct', 'prevalence_pct'}
    expected_quantiles = {'median_oop', 'p75_oop', 'p90_oop'}
    if (len(means) != 7 or len(quantiles) != 3 or
            {r[0] for r in means} != expected_means or
            {r[0] for r in quantiles} != expected_quantiles):
        raise ValueError('Reference metric set changed')
    if any(not math.isfinite(float(v)) for row in means + quantiles for v in row[1:]):
        raise ValueError('Nonfinite reference value')
    lines = ['/* BEGIN R REFERENCES: generated from saved aggregate tables. */',
             'data r_mean_reference;', 'length metric $32;',
             'input metric $ estimate se;', 'datalines;']
    lines += [' '.join(row) for row in means]
    lines += [';', 'run;', 'data r_quantile_reference;', 'length metric $32;',
              'input metric $ estimate;', 'datalines;']
    lines += [' '.join(row) for row in quantiles]
    lines += [';', 'run;', '/* END R REFERENCES */']
    return '\n'.join(lines)


def main():
    # Download only when archives are absent; read and hash-check the original ZIPs.
    if any(not (ROOT / f'data/raw/{name}dta.zip').exists() for name in ('h256', 'h254a')):
        from download import main as download
        download()
    out = ROOT / 'data/sas-inputs'
    records = {}
    for name, columns, filename in [('h256', PERSON_COLUMNS, 'person_source.csv'),
                                     ('h254a', RX_COLUMNS, 'rx_source.csv')]:
        frame = read_source(ROOT, name, columns)
        records[filename] = write_input(frame, columns, out / filename)
    (out / 'input-manifest.json').write_text(json.dumps(
        {'status': 'source_projection_only_not_SAS_execution', 'files': records}, indent=2) + '\n')
    path = ROOT / 'sas/run_meps.sas'
    text = path.read_text()
    pattern = r'/\* BEGIN R REFERENCES.*?/\* END R REFERENCES \*/'
    updated, count = re.subn(pattern, lambda match: reference_block(), text, flags=re.S)
    if count != 1:
        raise ValueError('Expected one reference block in run_meps.sas')
    if updated != text:
        path.write_text(updated)
    print(f'Prepared two original-column CSV files in {out}; no classification or survey estimates computed.')


if __name__ == '__main__':
    main()
