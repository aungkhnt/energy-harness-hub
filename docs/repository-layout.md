# Repository layout and migration

The `energy-harness-hub` repository is the single project root. TPV and hydropower
are ordinary folders under `systems/`. Git tracks their files directly; no Git
submodules, nested repositories or separate clone steps are required.

## Ownership

| Path | Owns |
|---|---|
| `engine/` | Shared numerics, units, contracts, registry, network/study execution, economics and reports |
| `systems/tpv/` | Active TPV model, declared units, terminal adapter and scenarios |
| `systems/tpv/legacy/` | Original tracked TPV scripts, README and visualization files |
| `systems/hydropower/` | Active hydropower model, declared units and scenarios |
| `scenarios/` | Shared or cross-system scenarios |
| `catalog/` | Discoverable families, including planned technologies |
| `studies/` | Saved result artifacts; local runs use ignored `local-*` names |
| `docs/`, `evidence/` | Architecture, assumptions, sources and data gaps |
| `tests/` | Verification across the engine and systems |

Physics modules are Python packages imported from the checkout root. No installable
wheel or published package is introduced. `python3 -m engine` remains the command.
`engine/models.py` and `engine/terminals.py` retain compatibility imports for existing
Python callers; new implementation belongs in the system folders.

## What moved

- The GitHub repository's original root TPV files → `systems/tpv/legacy/`.
- Local `engine/models.py` physics implementations → each system's `model.py`.
- Model parameter-unit maps → each system's `parameters.py`.
- TPV terminal implementation → `systems/tpv/terminals.py`.
- `scenarios/tpv_*.json` → `systems/tpv/scenarios/`.
- `scenarios/hydropower_*.json` → `systems/hydropower/scenarios/`.
- Shared field/metric helpers → `engine/validation.py`.

The original TPV tracked file contents are preserved exactly. Existing remote commit
history is retained; this is a new restructuring commit, not a history rewrite.
The root README describes the whole hub, while the original README stays with the
legacy scripts. Active documentation, catalog paths, imports and test fixtures use
the new layout.

Historical saved results are not modified. Their old hashes describe the code at
the time they ran. New implementation digests include `engine/` and active Python
code under `systems/`, excluding `legacy/`; moving/changing a system therefore
changes the digest. Old and new implementation versions remain distinguishable.

## Adding another system

1. Add `systems/<id>/` with a model, unit declarations, README and reproducible inputs.
2. Reuse shared numerical routines and validation helpers from `engine/`.
3. Add its definition to `engine/registry.py` and update the catalog status accurately.
4. Add physical/numerical reference tests and document validity limits.
5. Supply a terminal law separately if it can participate in an electrical network.

A catalog listing is not an implementation. Avoid empty model folders or placeholder
outputs for technologies that are still planned.

## Verification

The restructuring preserved behavior with 65 tests at migration time. The test
suite continues to grow as capabilities are added. Run it from the repository root. GitHub Actions runs the suite on Python 3.10 and 3.13 without installing the
legacy optional dependencies. The archived prototype is not claimed to be validated.
