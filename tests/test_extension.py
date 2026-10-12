"""Tests for changes in coverage, missing months and payer denominators."""
import unittest
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_extension import insurance_history, aggregate_payments, INS_COLS, SOURCE_COLS, PAYMENTS, MONTHS


class ExtensionTests(unittest.TestCase):
    def history(self):
        frame = pd.DataFrame(2, index=range(6), columns=INS_COLS + SOURCE_COLS)
        # All-year private, switch private->Medicare, overlapping private+Medicare.
        for i in [0, 1, 2]:
            frame.loc[i, INS_COLS] = 1
            frame.loc[i, [f'PRI{m}24' for m in MONTHS]] = 1
        for m in MONTHS[6:]:
            frame.loc[1, f'PRI{m}24'] = 2
            frame.loc[1, f'MCR{m}24X'] = 1
        frame.loc[2, [f'MCR{m}24X' for m in MONTHS]] = 1
        # One covered month then none; no coverage; out-of-scope month.
        frame.loc[3, ['INSJA24X', 'PRIJA24']] = 1
        frame.loc[5, 'INSJA24X'] = -1
        return frame

    def test_monthly_switching_and_overlap(self):
        out = insurance_history(self.history())
        self.assertEqual(out.monthly_history.tolist(), ['all_12', 'all_12', 'all_12', 'some_months', 'none_12', 'incomplete'])
        self.assertEqual(out.source_history[:3].tolist(), ['stable_sources', 'changed_sources', 'stable_sources'])
        self.assertEqual(out.loc[5, 'covered_months'], -1)

    def test_missing_source_preserves_known_any_coverage(self):
        f = self.history(); f.loc[0, 'PRIJA24'] = -8
        out = insurance_history(f)
        self.assertEqual(out.loc[0, 'monthly_history'], 'all_12')
        self.assertEqual(out.loc[0, 'source_history'], 'source_unknown')

    def test_unknown_is_not_uninsured_and_bad_code_fails(self):
        for value in [-7, -8, -9, -15, float('nan')]:
            f = self.history(); f.loc[4, 'INSJA24X'] = value
            self.assertEqual(insurance_history(f).loc[4, 'monthly_history'], 'incomplete')
        f = self.history(); f.loc[4, 'INSJA24X'] = 99
        with self.assertRaisesRegex(ValueError, 'code'): insurance_history(f)

    def test_inconsistent_monthly_sources_fail(self):
        f = self.history(); f.loc[4, 'PRIJA24'] = 1
        with self.assertRaisesRegex(ValueError, 'contradicts'): insurance_history(f)

    def payments(self):
        e = pd.DataFrame(0., index=range(3), columns=sum(PAYMENTS.values(), []) + ['RXXP24X'])
        e['DUPERSID'] = ['a', 'a', 'b']; e['RXRECIDX'] = ['r1', 'r2', 'r3']
        e.loc[0, ['RXSF24X', 'RXPV24X', 'RXXP24X']] = [10, 90, 100]
        e.loc[1, ['RXMR24X', 'RXXP24X']] = [200, 200]
        e.loc[2, ['RXVA24X', 'RXXP24X']] = [50, 50]
        return e

    def test_repeated_records_zero_oop_and_other_payers(self):
        out, residual = aggregate_payments(self.payments())
        self.assertEqual(out.loc['a', 'pay_self'], 10)
        self.assertEqual(out.loc['a', 'RXXP24X'], 300)
        self.assertEqual(out.loc['b', 'pay_self'], 0)
        self.assertEqual(out.loc['b', 'pay_other'], 50)
        self.assertEqual(residual, 0)

    def test_payer_corruption_and_duplicate_fail(self):
        for value in [-7, float('nan'), float('inf'), 900]:
            e = self.payments(); e.loc[0, 'RXPV24X'] = value
            with self.assertRaises(ValueError): aggregate_payments(e)
        e = self.payments(); e.loc[1, 'RXRECIDX'] = 'r1'
        with self.assertRaisesRegex(ValueError, 'duplicate'): aggregate_payments(e)


if __name__ == '__main__':
    unittest.main()
