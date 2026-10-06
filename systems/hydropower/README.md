# Hydropower system

`model.py` implements prescribed net head and flow, turbine/generator efficiencies,
and auxiliary consumption. `parameters.py` declares canonical input units.

Run from the repository root:

```bash
python3 -m engine run systems/hydropower/scenarios/hydropower_reference.json --output studies/local-hydro
python3 -m engine sweep systems/hydropower/scenarios/hydropower_sweep.json --output studies/local-hydro-grid
```

The [model specification](../../docs/reference-models.md) records assumptions and
limits. Inputs prescribe the water resource; reservoir dynamics, turbine curves and
an electrical terminal adapter are not implemented. Example costs are illustrative.
