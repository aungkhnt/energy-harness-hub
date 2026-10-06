# Reference model specification, v1

Backbone v0.2 retains these physical assumptions, adds explicit unit conversion for
model parameters, and uses a shared bracketed root solver. Original and normalized
inputs are saved. See [backbone interfaces](backbone.md).

These models use a small standard-library implementation so their equations,
input validation, and numerical behavior can be inspected. They are not a
substitute for calibration or a whole-plant system model.

## Shared execution contract

`run(study)` accepts a JSON-compatible object with schema version `0.1.0`, a study
identifier, technology identifier, explicit parameters, and a nonempty assumptions
list. Solver and economics objects are optional. Unknown fields and unsupported
technologies are rejected. All physical inputs use SI except bandgap in eV.

Results contain metrics with units and scope; diagnostics; supported series;
limitations; the complete input snapshot; engine version; and SHA-256 digests of
the inputs and all engine Python source files. Runs are deterministic for identical
inputs and implementation. Costs and unsupported outputs remain explicit.

No random uncertainty, dynamic state, universal graph solver, or materials database
is implemented yet. Parameter provenance is currently recorded in the scenario's
assumptions; the richer per-parameter contract in the architecture is still planned.

## TPV

For wavelength lambda, the blackbody radiance is

`B_lambda(T) = 2 h c^2 / [lambda^5 (exp(h c / (lambda k T)) - 1)]`.

A uniform gray emitter multiplies this by a constant emissivity. The geometry
factor for parallel facing rectangles is

`G = integral_Ae integral_Ac d^2 / ((xe-xc)^2 + (ye-yc)^2 + d^2)^2 dAc dAe`.

Here `G` has units m² sr, so spectral power intercepted by the cell is
`epsilon * B_lambda * G`. Finite receiving and emitting areas and emitter offsets
are both included. There is no point-source switching rule.

Midpoint quadrature uses N and 2N samples per surface axis and compares the two
results. N defaults to 8, and the accepted relative difference defaults to 1%.
This refinement indicator is not a rigorous error bound. The accepted result must
also obey reciprocal view-factor bounds. Very small gaps or unresolved geometries
are rejected rather than silently accepted.

Spectral integration uses Simpson quadrature in log wavelength, including its
Jacobian. Defaults are 10 nm to 1 mm with 512 intervals. The above-bandgap interval
is integrated separately so a cutoff is not smeared across a spectral grid cell.
The full blackbody integral must recover Stefan–Boltzmann power within 0.5%.
The model conservatively requires separation >= 10 times the upper wavelength limit
to stay in its far-field scope. Inputs that need broader spectral windows or finer
quadrature must supply them explicitly.

The cell absorbs above-gap radiation and reflects subgap radiation. With constant
external quantum efficiency EQE above the gap,

`Iph = q * EQE * integral_above_gap [P_lambda / (h c / lambda)] d lambda`.

The electrical model is the ideal limit of the single-diode equation:

`I(V) = Iph - I0 * (exp(q V / (k Tcell)) - 1)`.

`I0` is the supplied saturation-current density times cell area. Ideality is one,
series resistance is zero, and shunt resistance is infinite. Saturation current
is an illustrative input at the selected temperature; no material calibration or
temperature-scaling law is implied. Maximum power is found by solving
`x + log(1+x) = log(1+Iph/I0)`, where `x=q Vmpp/(k Tcell)`.

The result must satisfy `Voc <= Eg/q` and electrical power <= absorbed radiation.
Those are necessary checks, not sufficient proof of physical realizability.
Conditioned gross electricity is DC output times conditioning efficiency; net
electricity subtracts the supplied auxiliary demand. Negative net output is retained.
Radiation-to-net efficiency is undefined (JSON null) when incident power is zero.

Energy accounting separates reflected subgap radiation, electrical output,
conditioning losses, auxiliaries, and an unresolved non-electrical remainder.
The remainder includes heat and radiative emission. It is obtained by subtraction,
so zero accounting residual is not independent validation of a thermal solution.

The emitter and cell temperatures are imposed. There is no source-heating budget,
back radiation, cooling model, photon recycling, nonuniform electrical response,
near-field electrodynamics, or series-connected cell model. The reported efficiency
is not whole-plant efficiency.

## Hydropower

`P_hydraulic = rho * g * Q * H`, with standard gravity `g=9.80665 m/s²`.

H is net available hydraulic head, Q is volume flow, and rho is water density.
Shaft power applies turbine efficiency, gross electricity applies generator
efficiency, and net power subtracts auxiliaries. All efficiencies are supplied
constants. Zero flow and negative net electrical power are valid operating points.

The model does not predict river flow, reservoir dispatch, hydraulic transients,
cavitation, turbine curves, environmental constraints, or annual availability.

## Illustrative economics

Each capital line item contains quantity, quantity unit, and cost per quantity unit.
Capital is charged at year zero; constant operating costs occur at year end;
decommissioning occurs at the end of the last year. A nonnegative real discount
rate is applied to both costs and energy. Price year, currency, region, lifetime,
and an explicit illustrative-data label are required.

`annual_kWh = net_power_W / 1000 * assumed_operating_hours_per_year`.

`LCOE = [capex + sum(opex/(1+r)^t) + decommission/(1+r)^N]`
`       / sum(annual_kWh/(1+r)^t)`.

The denominator requires positive net generation. This implementation is restricted
to a constant operating point and at most 8760 operating hours per year; it is not
a production forecast. It has no inflation, degradation, replacement schedule,
taxes, subsidy, construction-finance model, or evidence that the cost list is complete.
Example prices must never be presented as current market estimates.

## Verification

The test suite checks spectral power against Stefan–Boltzmann, spectral peaks
against Wien's law, geometry reciprocity and far-field behavior, mesh refinement,
maximum-power stationarity, zero illumination, prescribed hydropower, negative net
power, closed-form discounted-cost cases, schema errors, reproducibility, catalog
availability, and CLI output behavior.

Both saved examples include numerical diagnostics. Empirical validation remains
unperformed, and the examples are not a matched-service comparison.
