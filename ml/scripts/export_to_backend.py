"""
Export ML artifacts from ml/outputs/ to backend/app/ml_artifacts/.

The ML team runs this after train.py / predict.py regenerates outputs.
Backend must NEVER read from ml/ directly — always from this mirror.

Usage:
    python ml/scripts/export_to_backend.py
    python ml/scripts/export_to_backend.py --dry-run
"""
import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ML_OUTPUTS = REPO / "ml" / "outputs"
BACKEND_ARTIFACTS = REPO / "backend" / "app" / "ml_artifacts"

# Each tuple: (relative source under ml/outputs/, destination filename)
ARTIFACTS = [
    ("predictions/predictions.csv",       "predictions.csv"),
    ("predictions/hotspot_rankings.csv",  "hotspot_rankings.csv"),
    ("predictions/hotspots.geojson",      "hotspots.geojson"),
    ("dashboard_metrics.json",            "dashboard_metrics.json"),
    ("analytics_report.json",             "analytics_report.json"),
    ("feature_importance.csv",            "feature_importance.csv"),
    ("shap/shap_values.parquet",          "shap_values.parquet"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would be copied without copying.")
    args = parser.parse_args()

    if not ML_OUTPUTS.is_dir():
        print(f"ERROR: missing source dir: {ML_OUTPUTS}", file=sys.stderr)
        return 1

    BACKEND_ARTIFACTS.mkdir(parents=True, exist_ok=True)

    copied, missing, skipped = 0, 0, 0
    for rel_src, dst_name in ARTIFACTS:
        src = ML_OUTPUTS / rel_src
        dst = BACKEND_ARTIFACTS / dst_name
        if not src.is_file():
            print(f"  MISSING  {src.relative_to(REPO)}")
            missing += 1
            continue
        if args.dry_run:
            print(f"  would copy  {src.relative_to(REPO)}  ->  backend/app/ml_artifacts/{dst_name}")
            continue
        shutil.copy2(src, dst)
        print(f"  copied  {src.relative_to(REPO)}  ->  backend/app/ml_artifacts/{dst_name}")
        copied += 1

    print()
    print(f"Summary: copied={copied} missing={missing} dry_run={args.dry_run}")
    if missing and not args.dry_run:
        print("Some artifacts are missing. Re-run training/prediction, then this script.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
