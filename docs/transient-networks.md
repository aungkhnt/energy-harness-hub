# Capacitor states and transient DC networks — v0.5

The engine can now integrate small RC networks with fixed independent sources and
optional fixed-temperature TPV cells. This adds electrical state evolution; device
calibration and coupled heat balance remain deferred.

## Run

From the repository root:

```bash
python3 -m engine transient scenarios/rc_charging.json --output studies/local-rc
python3 -m engine transient systems/tpv/scenarios/tpv_capacitor_startup.json --output studies/local-tpv-startup
```

The command saves `transient.json` (all samples, accounting and provenance) and a
Markdown summary. The output folder must be new. Existing `network` commands remain
steady solves and explicitly reject capacitors rather than silently opening them.

## Input and state contract

A transient study contains `schema_version: "0.1.0"`, `study_id`, an embedded
`network` using the existing network schema, and `time` with positive `duration_s`
and `step_s`. Time quantities accept seconds or milliseconds. The time origin is
zero; at most 2000 steps are allowed. The last step is shortened to end at the
specified duration when necessary.

Add a capacitor module with its normal positive/negative node terminals:

```json
{
  "id": "storage",
  "type": "capacitor",
  "positive": "storage_bus",
  "negative": "ground",
  "parameters": {
    "capacitance_f": {"value": 10, "unit": "mF"},
    "initial_voltage_v": 0
  }
}
```

Capacitance must be positive. F, mF and uF are supported; initial voltage is signed
positive-terminal minus negative-terminal voltage. It is required, never silently
assumed zero. At least one capacitor is required. Voltage/current source values,
resistances, TPV illumination, and temperatures remain constant during a run.

The physical state of each capacitor is its terminal voltage. Node potentials and
ideal-source currents remain algebraic unknowns determined by the network equations.
This is a restricted implicit network integrator, not a general DAE solver.

## Initialization

Each capacitor's specified initial voltage is introduced as an algebraic constraint
with an unknown initial current. The augmented network solves the initial node
voltages and all currents using the same linear/nonlinear machinery as steady runs.
The t=0 sample represents the right-hand initial state; it is not a pre-switch state.

Conflicting or underdetermined constraints are rejected. In particular, capacitor
loops or a capacitor directly parallel to an ideal voltage source may be rejected
even when their voltages agree, because this initial-current formulation can be
rank deficient. It does not silently discard redundant constraints, project initial
conditions, or invent impulse currents. Such topologies need a more general
initialization method before being supported.

Initial source limits and TPV operating-domain checks apply immediately. A circuit
cannot evade a source rating simply because its steady demand is lower than its
startup demand.

## Time integration

Backward Euler uses

`Icap_new = C * (Vcap_new - Vcap_previous) / dt`.

For each step, the assembler stamps conductance `C/dt` and a history-current term
into the network's KCL equations. Linear networks use the existing direct solver.
Networks containing a TPV cell use the analytic-Jacobian damped Newton solver,
starting from the previous solved electrical state. TPV radiation is prepared once,
not recalculated at every Newton iteration or time step.

Every successful sample contains node voltages, branch currents and powers, capacitor
energies, KCL/power residuals and algebraic solver diagnostics. Step records include
dt, stored-energy change, numerical damping and discrete energy residual. The saved
result also includes original inputs, normalized modules, state definitions, the
static equation system and the implicit capacitor law, plus input/source hashes.

A step failure stops the run with its index and time. The CLI does not write a
completed result for a failed trajectory. No adaptive stepping, automatic retry with
smaller dt, switching-event localization or source interpolation is implemented.

## Energy accounting

Physical stored capacitor energy is `E = 0.5 * C * V^2`. Branch powers are calculated
from solved voltage and current, as in steady networks. Noncapacitor energy transfers
use right-endpoint quadrature consistent with the implicit integration step.

Backward Euler satisfies the discrete identity

`Vnew * Icap_new * dt = (Enew - Eprevious) + 0.5 * C * (Vnew - Vprevious)^2`.

The extra nonnegative term is numerical damping. It is explicitly separated from
physical resistor dissipation. It is not a heat prediction, device inefficiency,
or a quantity to hide in a physical loss term.

The integrated budget is

`net input to storage = change in stored energy + numerical damping + residual`.

Here net input means negative total absorbed energy in noncapacitor branches, so
resistor consumption has already been subtracted from source delivery. The report
retains each noncapacitor branch's signed absorbed energy separately.

Instantaneous power uses the existing network threshold. Each step's discrete energy
residual must satisfy `abs(residual) <= 1e-9 J + 1e-8 * energy_scale`, where the scale
sums absolute noncapacitor transfers, absolute stored-energy change, and damping.

A closed discrete budget is not a time-accuracy estimate. Backward Euler is first
order and dissipative. Run refined step sizes and check quantities of interest;
no automatic error tolerance or accuracy certificate is provided in this version.

## Examples and verification

- The RC example has a 10 V source, 10 ohm resistor and 10 mF capacitor. Its time
  constant is 0.1 s. Tests compare the trajectory against `10*(1-exp(-t/0.1))` and
  verify error decreases with step refinement.
- Discharge, a constant-current linear voltage ramp, an isolated charged capacitor,
  non-reference terminal connections, inconsistent initialization, and source limits
  have dedicated tests.
- The TPV example places a capacitor across the existing resistive load. Tests verify
  startup approaches the independent steady operating point and numerical damping
  decreases with smaller steps. This remains an uncalibrated electrical reference.

Historical examples are retained separately. Current saved reports are
[RC charging](../studies/rc-charging/report.md) and
[TPV startup](../studies/tpv-capacitor-startup/report.md).

## Next seams

Time-varying input profiles and explicit event handling, network-level parameter
studies, improved initial-condition handling, and converter/storage terminal models
can build on this interface. Inductors, AC analysis, controller training and thermal
dynamics remain unimplemented. Capacitors here are ideal electrical storage elements,
not battery models.
