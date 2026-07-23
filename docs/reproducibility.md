# Reproducibility

## Configuration Snapshot

Every run saves a `config_snapshot.yaml` file containing the full configuration used.

## Environment Record

Every run saves an `environment.json` file with:
- Python version
- Platform info
- Package version
- Timestamp

## Data Fingerprinting

- Raw data is fingerprinted with SHA256
- Training and OOS data have independent fingerprints
- Fingerprints are verified to be different (no overlap)

## Random Seed

A fixed random seed (default: 42) ensures deterministic:
- Synthetic data generation
- Truncation test date selection
- Quality check sampling

## SHA256 Checksums

Every run generates `SHA256SUMS.txt` containing checksums for all output files.

## Run Manifest

Contains:
- Training data fingerprint
- OOS data fingerprint
- Row counts
- Symbol counts

## How to Reproduce

```bash
# Use the same config and seed
python -m cogalpha_mvp.cli run-all --config configs/demo.yaml --seed 42

# Check the SHA256SUMS in results/<run_id>/SHA256SUMS.txt
```
