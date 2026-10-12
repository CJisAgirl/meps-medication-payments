"""Download public AHRQ MEPS files; preserve provenance and fail on changed bytes."""
from pathlib import Path
import hashlib
import json
import urllib.request
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "h256": "https://meps.ahrq.gov/data_files/pufs/h256/h256dta.zip",
    "h254a": "https://meps.ahrq.gov/data_files/pufs/h254a/h254adta.zip",
}


def main():
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    provenance = ROOT / "results/source-manifest.json"
    previous = json.loads(provenance.read_text()) if provenance.exists() else {}
    manifest = {}
    for name, url in SOURCES.items():
        target = raw / f"{name}dta.zip"
        if not target.exists():
            temp = target.with_suffix(".part")
            with urllib.request.urlopen(url, timeout=120) as response:
                temp.write_bytes(response.read())
            temp.rename(target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if name in previous and digest != previous[name]["sha256"]:
            raise RuntimeError(f"Source changed: {name}; review and version the manifest explicitly")
        with zipfile.ZipFile(target) as z:
            members = [m for m in z.namelist() if m.lower().endswith(".dta")
                       and not m.startswith("__MACOSX/") and not Path(m).name.startswith("._")]
            if len(members) != 1:
                raise ValueError(f"Expected one Stata file: {members}")
            (raw / f"{name}.dta").write_bytes(z.read(members[0]))
        manifest[name] = previous.get(name) or {
            "url": url, "sha256": digest, "bytes": target.stat().st_size,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "overview": "https://meps.ahrq.gov/data_stats/download_data_files_detail.jsp?cboPufNumber=HC-" + name[1:].upper(),
        }
        print(f"{name}: {target.stat().st_size:,} bytes, SHA-256 {digest}")
    provenance.parent.mkdir(exist_ok=True)
    provenance.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
