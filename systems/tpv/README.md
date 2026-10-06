# Thermophotovoltaic (TPV) system

This folder owns the active TPV reference model and its original prototype archive.

- `model.py`: radiation transport, idealized cell I–V and electrical accounting.
- `parameters.py`: declared canonical parameter units.
- `terminals.py`: cell terminal law for nonlinear DC networks.
- `scenarios/`: standalone reference, parameter sweep, and connected-load examples.
- `legacy/`: original TPV project, preserved without modifying its tracked file contents.

From the repository root:

```bash
python3 -m engine run systems/tpv/scenarios/tpv_reference.json --output studies/local-tpv
python3 -m engine sweep systems/tpv/scenarios/tpv_sweep.json --output studies/local-tpv-grid
python3 -m engine network systems/tpv/scenarios/tpv_connected_load.json --output studies/local-tpv-network
python3 -m engine transient systems/tpv/scenarios/tpv_capacitor_startup.json --output studies/local-tpv-startup
```

Read the [model specification](../../docs/reference-models.md) and
[network assumptions](../../docs/nonlinear-networks.md). Device calibration and
coupled heat balance remain deferred; this is not a complete thermal plant model.

The capacitor-startup scenario evolves electrical storage at fixed temperatures.
See [transient limits and energy accounting](../../docs/transient-networks.md).

## Original prototype

The original [README](legacy/README.md), scripts and `viz/` pages live in `legacy/`.
These scripts retain their original imports and should be run from that directory:

```bash
cd systems/tpv/legacy
python3 -m pip install -r requirements.txt
mkdir -p plots
python3 planckSpectrumModel.py
```

The active engine does not import or execute the legacy scripts. Their historical
limitations have not been repaired as part of this repository migration. There is
no nested Git repository in this folder: its files are tracked by the hub repository.
