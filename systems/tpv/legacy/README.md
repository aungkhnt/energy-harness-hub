# TPV Energy Flux Simulation

Simulation of thermophotovoltaic energy harvesting from first principles — 
the energy-harvest module for a Dyson swarm energy system simulator.

Computes the full conversion chain: thermal emission (Planck spectrum) → 
spatial irradiance on a PV cell I(x,y) → gradient analysis and optimization — 
with multivariable calculus as the backbone (partial derivatives, chain rule, 
Lagrange multipliers, double integrals across coordinate systems).

Built as a Calc III honors project at CCSF, grounded in a real engineering 
application: each drone in a Dyson swarm runs this model to compute its 
power budget.

## What This Computes

Emitter (heat source) → thermal radiation → TPV cell → electricity 

- **Planck spectrum**: B(λ,T) — spectral radiance of the emitter
- **Irradiance field**: I(x,y) — spatial power distribution on the cell
- **Gradient analysis**: ∇I — direction and rate of irradiance change
- More stages (view factor, cell I-V, system efficiency) in progress

## Quick Start

```bash
pip install -r requirements.txt
python planckSpectrumModel.py
python Irradiance.py
python Gradient.py
```

## File Map

| File | What It Does |
|------|-------------|
| `TPVconfig.py` | Dataclass holding constants, geometry, material properties |
| `physics_utils.py` | Generic, Reusable Equations: Wien's law, Stefan-Boltzmann(M), steradian power(L),... |
| `planckSpectrumModel.py` | Planck spectral radiance + selective emitter |
| `Irradiance.py` | I(x,y) irradiance field (point-source + finite emitter) |
| `Gradient.py` | ∂I/∂x, ∂I/∂y, Hessian, hot spot detection |

## Status 

Phase 1 : Spectral Model + Irradiance -> Done. 