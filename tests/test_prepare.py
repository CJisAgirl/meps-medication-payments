"""Failure-oriented checks for person denominators and drug/payment integrity."""
import sys
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare import classify, aggregate


class CohortTests(unittest.TestCase):
    def setUp(self):
        self.p = pd.DataFrame({"DUPERSID":["a","b","c"],"AGELAST":[40,50,16],
            "PERWT24F":[2.,3.,4.],"VARSTR":[1,1,1],"VARPSU":[1,2,2],"INSCOV24":[1,2,3]})
        self.e = pd.DataFrame({"DUPERSID":["a","a","a","c"],"RXRECIDX":["r1","r2","r3","r4"],
            "ingredient":["semaglutide","semaglutide","tirzepatide","other"],
            "primary_flag":[1,1,1,0],"brand_flag":[1,0,1,0],
            "RXSF24X":[10.,0.,20.,5.],"RXXP24X":[100.,100.,200.,10.]})

    def test_repeat_fills_switching_and_nonusers(self):
        out=aggregate(self.p,self.e).set_index("DUPERSID")
        self.assertEqual(len(out),3)
        self.assertEqual(out.loc["a","user"],1)
        self.assertEqual(out.loc["a","fills"],3)
        self.assertEqual(out.loc["a","oop"],30)
        self.assertEqual(out.loc["a","total"],400)
        self.assertEqual(out.loc["a","brand_total"],300)
        self.assertEqual(out.loc["a","semaglutide_user"],1)
        self.assertEqual(out.loc["a","tirzepatide_user"],1)
        self.assertEqual(out.loc["b","user"],0)
        self.assertEqual(out.loc["c","oop"],0)
        adults=out[out.AGELAST>=18]
        self.assertAlmostEqual((adults.user*adults.PERWT24F).sum()/adults.PERWT24F.sum(),.4)

    def test_duplicate_records_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            aggregate(self.p,pd.concat([self.e,self.e.iloc[[0]]]))

    def test_missing_negative_and_excess_payments_rejected(self):
        for value in [-7,float("nan"),101]:
            bad=self.e.copy();bad.loc[0,"RXSF24X"]=value
            with self.assertRaises(ValueError): aggregate(self.p,bad)

    def test_unmatched_person_rejected(self):
        bad=self.e.copy();bad.loc[0,"DUPERSID"]="unmatched"
        with self.assertRaisesRegex(ValueError,"missing from"):
            aggregate(self.p,bad)

    def test_identity_conflict_and_unknown_candidate_rejected(self):
        for generic,name in [("SEMAGLUTIDE","MOUNJARO"),("METFORMIN","OZEMPIC"),("SEMAGLUTIDE COMPOUND","OTHER")]:
            with self.assertRaises(ValueError): classify(generic,name)

    def test_insulin_combo_excluded_and_nonbrand_retained(self):
        self.assertEqual(classify("INSULIN DEGLUDEC;LIRAGLUTIDE","XULTOPHY")[1],0)
        self.assertEqual(classify("SEMAGLUTIDE","SEMA/METHYL")[1:3],(1,0))
        self.assertEqual(classify("-9","OZEMPIC")[:3],("semaglutide",1,1))
        self.assertEqual(classify("METFORMIN","METFORMIN")[1],0)


if __name__=="__main__": unittest.main()
