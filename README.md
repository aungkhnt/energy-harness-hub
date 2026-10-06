# Energy Harness Hub

A shared physics and mathematics engine for exploring energy generation, conversion,
electrical delivery, and economics. Individual energy systems live under `systems/`;
the reusable simulation infrastructure lives under `engine/`.

TPV is the first system, not the entire repository. Hydropower is the second runnable
reference system. The [technology catalog](catalog/plants.json) contains 26 entries;
most are planned, not implemented or commercially assessed.

## Repository structure

```text
energy-harness-hub/
├── engine/                     Shared solvers, units, registry, networks and reporting
├── systems/
│   ├── tpv/
│   │   ├── model.py            Current TPV radiation and electrical reference model
│   │   ├── parameters.py      Input units
│   │   ├── terminals.py       TPV network terminal law
│   │   ├── scenarios/         Reference, sweep and connected-load inputs
│   │   └── legacy/            Original TPV scripts and browser visualizations
│   └── hydropower/
│       ├── model.py           Head/flow reference model
│       ├── parameters.py      Input units
│       └── scenarios/         Reference and sweep inputs
├── scenarios/                  Shared/cross-system network examples
├── catalog/                    All technology families and implementation status
├── studies/                    Saved results and reports, including historical runs
├── evidence/                   Sources and known data gaps
├── docs/                       Architecture and model specifications
├── tests/                      Numerical, physical and interface checks
└── .github/workflows/          Automated test runs
```

These are ordinary folders in one Git repository. No submodules or separate clone
steps are required. New system families get their own folder when implementation
begins; planned technologies remain in the catalog rather than empty directories.

## Quick start

Python 3.10+ is sufficient for the current engine; it uses the standard library.
Run commands from the repository root:

```bash
git clone https://github.com/aungkhnt/energy-harness-hub.git
cd energy-harness-hub
python3 -m engine catalog
python3 -m engine describe tpv
python3 -m engine run systems/tpv/scenarios/tpv_reference.json --output studies/local-tpv
python3 -m engine run systems/hydropower/scenarios/hydropower_reference.json --output studies/local-hydro
python3 -m engine sweep systems/hydropower/scenarios/hydropower_sweep.json --output studies/local-hydro-grid
python3 -m engine network systems/tpv/scenarios/tpv_connected_load.json --output studies/local-tpv-load
python3 -m engine network scenarios/dc_distribution.json --output studies/local-dc-network
python3 -m unittest discover -s tests -v
```

Each execution writes JSON and a Markdown report. Output directories must be new;
choose a different name for subsequent runs. Local outputs named `studies/local-*`
are ignored by Git. The legacy TPV scripts have separate optional dependencies;
see [TPV system instructions](systems/tpv/README.md).

## Available capabilities

- Model registry, explicit unit conversions, input snapshots and implementation hashes.
- TPV radiation, idealized cell I–V and maximum power; prescribed-head hydropower.
- Linear/nonlinear steady DC networks and TPV load-selected operating points.
- Deterministic parameter sweeps and conservative within-model comparisons.
- Illustrative lifecycle economics and reproducible reports.

These are reference calculations, not empirically validated engineering designs.
Device calibration and coupled heat balance are deferred. Dynamic simulation,
propulsion, supply-chain forecasts, a website and most catalog technologies remain
planned. Example economic inputs are invented and labeled accordingly.

## Documentation and examples

- [TPV system](systems/tpv/README.md)
- [Hydropower system](systems/hydropower/README.md)
- [Repository layout and migration](docs/repository-layout.md)
- [Overall architecture](docs/architecture.md)
- [Engine backbone](docs/backbone.md)
- [Linear networks](docs/networks.md) and [nonlinear TPV networks](docs/nonlinear-networks.md)
- [Reference equations](docs/reference-models.md) and [evidence](evidence/references.md)
- [Connected TPV report](studies/tpv-connected-load/report.md)
- [Hydropower sweep report](studies/backbone-hydro-sweep/report.md)

Historical result JSON is retained without rewriting input snapshots or source hashes.
New runs hash both the shared engine and active system code.
