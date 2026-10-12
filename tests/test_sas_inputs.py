"""Input/reference integrity checks; these tests do not execute SAS."""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_sas_inputs import ROOT, read_source, write_input, reference_block


class SASInputTests(unittest.TestCase):
    def test_round_trip_preserves_ids_quotes_missing_and_float_precision(self):
        frame = pd.DataFrame({'DUPERSID': ['0000000001', '9999999999'],
                              'RXRECIDX': ['0000000000000000001', '9999999999999999999'],
                              'RXNAME': ['BRAND, "NAME"', ''],
                              'PERWT24F': [12345.678901234567, float('nan')],
                              'RXSF24X': [0., 0.12345678901234567]}, index=[8, 9])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.csv'
            manifest = write_input(frame, list(frame.columns), path)
            with path.open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]['DUPERSID'], '0000000001')
            self.assertEqual(rows[1]['RXRECIDX'], '9999999999999999999')
            self.assertEqual(rows[0]['RXNAME'], 'BRAND, "NAME"')
            self.assertEqual(rows[1]['PERWT24F'], '')
            self.assertEqual(float(rows[1]['RXSF24X']), frame.loc[9, 'RXSF24X'])
            self.assertEqual(manifest['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_truncation_or_multiline_text_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for column, value in [('DUPERSID', '1'*11), ('RXNAME', 'a'*201),
                                  ('RXNAME', 'A\nB'), ('RXNAME', 'A\rB')]:
                frame = pd.DataFrame({column: [value]})
                with self.assertRaisesRegex(ValueError, 'truncated or split'):
                    write_input(frame, [column], Path(tmp) / 'bad.csv')

    def test_original_zip_fingerprint_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data/raw').mkdir(parents=True)
            (root / 'results').mkdir()
            payload = io.BytesIO()
            pd.DataFrame({'DUPERSID': ['0000000001'], 'AGELAST': [42]}).to_stata(payload, write_index=False)
            archive = root / 'data/raw/h256dta.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                z.writestr('h256.dta', payload.getvalue())
            sha = hashlib.sha256(archive.read_bytes()).hexdigest()
            (root / 'results/source-manifest.json').write_text(json.dumps({'h256': {'sha256': sha}}))
            self.assertEqual(read_source(root, 'h256', ['DUPERSID']).iloc[0, 0], '0000000001')
            with archive.open('ab') as f:
                f.write(b'changed')
            with self.assertRaisesRegex(ValueError, 'bytes changed'):
                read_source(root, 'h256', ['DUPERSID'])

    def test_embedded_reference_is_current_and_missing_metric_fails(self):
        block = reference_block()
        self.assertIn(block, (ROOT / 'sas/run_meps.sas').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'results').mkdir()
            for name in ['payment-distribution.csv', 'estimates.csv']:
                shutil.copy(ROOT / 'results' / name, root / 'results' / name)
            path = root / 'results/payment-distribution.csv'
            path.write_text('\n'.join(path.read_text().splitlines()[:-1]) + '\n')
            with self.assertRaisesRegex(ValueError, 'metric set changed'):
                reference_block(root)


if __name__ == '__main__':
    unittest.main()
