# Shared scenarios

This folder holds shared/cross-system network examples, starting with
`dc_distribution.json`. System-specific examples belong under
`systems/<system>/scenarios/`.

Run from the repository root:

```bash
python3 -m engine network scenarios/dc_distribution.json --output studies/local-dc
```
