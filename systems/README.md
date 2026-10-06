# Energy systems

Each implemented energy family owns its physics model, input-unit declarations,
optional terminal adapters, examples, and documentation here.

| System | Implementation | Scenarios |
|---|---|---|
| [TPV](tpv/README.md) | Fixed-temperature radiation and idealized cell, nonlinear terminal adapter | [Inputs](tpv/scenarios) |
| [Hydropower](hydropower/README.md) | Prescribed head/flow and constant efficiencies | [Inputs](hydropower/scenarios) |

The wider [catalog](../catalog/plants.json) lists planned families. Implemented systems
use shared numerical utilities, contracts and execution from `engine/`. Register a
new model in `engine/registry.py`; keep system-specific equations in its own module.

These are ordinary Python packages and Git folders, not Git submodules. The legacy
TPV archive is excluded from engine implementation hashes and has separate dependencies.
