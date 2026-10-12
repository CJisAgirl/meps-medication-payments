"""Single entry point. Run from any working directory with Python and R installed."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
commands = [
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    [os.environ.get("MEPS_RSCRIPT", "Rscript"), "tests/test_payments.R"],
    [sys.executable, "scripts/download.py"],
    [sys.executable, "scripts/prepare.py"],
    [os.environ.get("MEPS_RSCRIPT", "Rscript"), "scripts/analyze.R"],
    [sys.executable, "scripts/prepare_extension.py"],
    [os.environ.get("MEPS_RSCRIPT", "Rscript"), "scripts/analyze_extension.R"],
    [sys.executable, "scripts/report_extension.py"],
    [sys.executable, "scripts/verify_extension.py"],
    [os.environ.get("MEPS_RSCRIPT", "Rscript"), "scripts/analyze_payments.R"],
    [sys.executable, "scripts/report_payments.py"],
    [sys.executable, "scripts/verify_payments.py"],
]
if __name__ == "__main__":
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)
    print("Complete. Read results/research-brief.md.")
