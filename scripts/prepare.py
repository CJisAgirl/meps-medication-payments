"""Auditable drug identification and SQL aggregation; no microdata are published."""
from pathlib import Path
import json
import re
import sqlite3
import platform
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INGREDIENTS = {"SEMAGLUTIDE", "TIRZEPATIDE", "DULAGLUTIDE", "LIRAGLUTIDE",
               "EXENATIDE", "LIXISENATIDE", "ALBIGLUTIDE"}
BRANDS = {
    "OZEMPIC": "SEMAGLUTIDE", "WEGOVY": "SEMAGLUTIDE", "RYBELSUS": "SEMAGLUTIDE",
    "MOUNJARO": "TIRZEPATIDE", "ZEPBOUND": "TIRZEPATIDE",
    "ZEPBOUND 2.5MG/0.5 ML": "TIRZEPATIDE", "ZEPBOUND 2.5MG/0.5ML": "TIRZEPATIDE",
    "ZEPBOUND 5 MG/0.5 ML INJ": "TIRZEPATIDE", "ZEPBOUND INJ": "TIRZEPATIDE",
    "TRULICITY": "DULAGLUTIDE", "TRULICITY 0.75/0.5": "DULAGLUTIDE",
    "VICTOZA": "LIRAGLUTIDE", "SAXENDA": "LIRAGLUTIDE",
    "BYETTA": "EXENATIDE", "BYDUREON": "EXENATIDE", "BYDUREON BCISE": "EXENATIDE",
    "ADLYXIN": "LIXISENATIDE", "TANZEUM": "ALBIGLUTIDE",
}


def normalize(value):
    return re.sub(r"\s+", " ", str(value).upper().strip())


def classify(generic, name):
    generic, name = normalize(generic), normalize(name)
    named = BRANDS.get(name)
    if "INSULIN" in generic and any(i in generic for i in INGREDIENTS):
        return "insulin_combination", 0, 0, "excluded_insulin_combination"
    if name in {"SOLIQUA", "SOLIQUA 100/33", "XULTOPHY", "XULTOPHY 100/3.6"}:
        return "insulin_combination", 0, 0, "excluded_insulin_combination"
    if generic in INGREDIENTS:
        if named and named != generic:
            raise ValueError(f"Drug identity conflict: {generic} / {name}")
        return generic.lower(), 1, int(named is not None), "generic_exact"
    missing = generic in {"", "NAN", "-1", "-7", "-8", "-9", "-15"}
    if named:
        if not missing:
            raise ValueError(f"Brand conflicts with nonmissing generic: {generic} / {name}")
        return named.lower(), 1, 1, "brand_fallback"
    # A near-match must be reviewed; it must not silently become a non-user.
    if (any(i in generic or i in name for i in INGREDIENTS)
            or any(b.split()[0] in name for b in BRANDS)):
        raise ValueError(f"Unreviewed drug candidate: {generic} / {name}")
    return "other", 0, 0, "not_target"


def validate_inputs(persons, events):
    for df, key in [(persons, "DUPERSID"), (events, "RXRECIDX")]:
        if df[key].isna().any() or df[key].astype(str).str.strip().eq("").any() or df[key].duplicated().any():
            raise ValueError(f"Missing/duplicate key: {key}")
    if not set(events.DUPERSID).issubset(set(persons.DUPERSID)):
        raise ValueError("Prescription IDs missing from consolidated file")
    target = events.loc[events.primary_flag.eq(1)]
    dollars = target[["RXSF24X", "RXXP24X"]]
    if dollars.isna().any().any() or dollars.lt(0).any().any():
        raise ValueError("Missing or negative target-drug payments")
    if (target.RXSF24X > target.RXXP24X + 0.02).any():
        raise ValueError("Self/family payments exceed total payments")
    if persons[["PERWT24F", "VARSTR", "VARPSU", "AGELAST"]].isna().any().any():
        raise ValueError("Missing weight, survey design, or age")
    if (persons.loc[persons.PERWT24F.gt(0), "AGELAST"] < 0).any():
        raise ValueError("Unresolved age among positive-weight respondents")


def aggregate(persons, events):
    validate_inputs(persons, events)
    with sqlite3.connect(":memory:") as con:
        persons.to_sql("persons", con, index=False)
        events.to_sql("events", con, index=False)
        return pd.read_sql_query((ROOT / "cohort.sql").read_text(), con)


def main():
    processed = ROOT / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    person_cols = ["DUPERSID", "AGELAST", "INSCOV24", "PERWT24F", "VARSTR", "VARPSU"]
    event_cols = ["DUPERSID", "RXRECIDX", "RXDRGNAM", "RXNAME", "RXSF24X", "RXXP24X", "PERWT24F"]
    p = pd.read_stata(ROOT / "data/raw/h256.dta", columns=person_cols, convert_categoricals=False)
    e = pd.read_stata(ROOT / "data/raw/h254a.dta", columns=event_cols, convert_categoricals=False)
    e[["ingredient", "primary_flag", "brand_flag", "mapping_method"]] = pd.DataFrame(
        [classify(g, n) for g, n in zip(e.RXDRGNAM, e.RXNAME)], index=e.index)
    # The event-file weight must agree with the consolidated person-file weight.
    weights = e.merge(p[["DUPERSID", "PERWT24F"]], on="DUPERSID", how="left", validate="many_to_one")
    if not (weights.PERWT24F_x - weights.PERWT24F_y).abs().lt(0.0001).all():
        raise ValueError("Prescription/person weights disagree")
    cohort = aggregate(p, e)
    # Independent pandas recomputation checks SQL sums and left-join preservation.
    expected = e.loc[e.primary_flag.eq(1)].groupby("DUPERSID").RXSF24X.sum()
    actual = cohort.set_index("DUPERSID").oop
    if not (actual - expected.reindex(actual.index, fill_value=0)).abs().lt(0.0001).all():
        raise AssertionError("SQL/pandas expenditure disagreement")
    if len(cohort) != len(p) or cohort.DUPERSID.duplicated().any():
        raise AssertionError("Person denominator changed during aggregation")
    cohort.to_csv(processed / "persons.csv", index=False)
    # Aggregate audit only; never write person identifiers into results/.
    target = e.loc[e.mapping_method.ne("not_target")]
    audit = target.groupby(["RXDRGNAM", "RXNAME", "ingredient", "primary_flag", "brand_flag", "mapping_method"], dropna=False).agg(
        records=("RXRECIDX", "size"), unweighted_people=("DUPERSID", "nunique")).reset_index()
    audit.to_csv(ROOT / "results/drug-mapping-audit.csv", index=False)
    positive = cohort.PERWT24F.gt(0)
    adult = positive & cohort.AGELAST.ge(18)
    metadata = {
        "source_person_records": len(p), "source_prescription_records": len(e),
        "positive_weight_persons": int(positive.sum()),
        "positive_weight_prescription_records": int(e.PERWT24F.gt(0).sum()),
        "zero_weight_persons_excluded": int((~positive).sum()),
        "positive_weight_children": int((positive & cohort.AGELAST.lt(18)).sum()),
        "adult_persons": int(adult.sum()), "adult_primary_users": int(cohort.loc[adult, "user"].sum()),
        "adult_nonusers_retained": int(cohort.loc[adult, "user"].eq(0).sum()),
        "adult_target_records": int(cohort.loc[adult, "fills"].sum()),
        "adult_brand_only_users": int(cohort.loc[adult, "brand_user"].sum()),
        "insulin_combination_records": int(e.ingredient.eq("insulin_combination").sum()),
        "brand_fallback_records": int(e.mapping_method.eq("brand_fallback").sum()),
        "missing_generic_records_all_drugs": int(e.RXDRGNAM.map(normalize).isin(["", "NAN", "-1", "-7", "-8", "-9", "-15"]).sum()),
        "unresolved_insurance_adults": int((adult & ~cohort.INSCOV24.isin([1, 2, 3])).sum()),
        "unmatched_event_ids": 0, "duplicate_person_ids": 0, "duplicate_event_ids": 0,
        "sql_vs_pandas_oop": "PASS", "python": platform.python_version(), "pandas": pd.__version__,
    }
    (ROOT / "results/cohort-audit.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
