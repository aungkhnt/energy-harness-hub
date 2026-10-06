# Nonlinear DC networks and TPV terminal integration — v0.4

Update: [v0.5 capacitor transients](transient-networks.md) now supports a restricted
RC/TPV time-integration mode. Earlier roadmap statements below describe the prior
version; general dynamics and thermal coupling remain deferred.


The network engine now supports a nonlinear `tpv_cell` module. Its photocurrent is
computed by the existing radiation model once before electrical solving; its
terminal equation then participates in network KCL. The connected load determines
voltage and current. Device calibration and coupled heat balance remain deferred.

## Run the example

```bash
python3 -m engine network systems/tpv/scenarios/tpv_connected_load.json --output studies/local-tpv-load
```

The supplied example connects a cell, a 0.005 ohm lead, and a 0.05 ohm load. Inspect
the saved [example report](../studies/tpv-connected-load/report.md) for the resulting
voltages, currents, losses, actual DC output, and independently computed MPP.

## TPV module input and physical scope

A `tpv_cell` uses the standard positive/negative terminals. Its parameters contain
`tpv_parameters` (the existing TPV model inputs, including quantity objects) and an
optional `radiation_solver` object with the existing spectral/geometry options.

This represents a bare cell: `conditioning_efficiency` must be 1 and
`auxiliary_power_w` must be 0. Nontrivial values are rejected rather than silently
ignored. There is no implicit MPPT, converter, auxiliary consumption or whole-plant
power accounting. Separate terminal laws will be required for those modules.

The adapter obtains `Iph`, `I0`, and `Vthermal = k*Tcell/q` from the existing TPV
implementation. Using the network's positive-absorbed-current convention:

`Iabsorbed(V) = I0 * expm1(V / Vthermal) - Iph`

`dIabsorbed/dV = (I0 / Vthermal) * exp(V / Vthermal)`.

The radiation model and its assumptions are reused without new fitted parameters.
Their normalized inputs, numerical diagnostics, model identifier and limitations
are saved with the module. The single-diode law remains an idealized, uncalibrated
reference at a fixed cell temperature.

Final operating points must lie in the generating range `0 <= V <= Voc`, with
1e-9 V numerical slack. No reverse-breakdown or externally powered forward-bias
behavior is claimed. Intermediate Newton trials can leave that interval; final
physical-domain checks remain mandatory. Delivered DC power is also checked against
the independently computed maximum power, with 1e-8 W numerical slack.

## Equation assembly

The saved linear matrix contains resistors, ideal voltage-source constraints and
independent current-source terms as before. Nonlinear cell currents are added to
the positive node's KCL residual and subtracted at the negative node. Analytic
conductance terms are stamped into the Jacobian with the same sign convention.

Thus the residual is `R(x) = A*x - b + nonlinear_currents(x)`; `A*x=b` alone is not
the nonlinear network equation. The JSON includes `nonlinear_terms` with terminal
identities, law and numerical parameters so the saved system can be reconstructed.

## Solver contract

`solve_nonlinear(evaluate, initial, residual_scales, ...)` expects a residual vector
and analytic Jacobian from `evaluate`. It uses damped Newton steps, solved by the
existing row-scaled linear solver. Trial step lengths are repeatedly halved until
the fixed-scale residual norm decreases sufficiently or meets tolerance.

The scaled norm is `max(abs(Ri)/scale_i)`. Network defaults are 1 A for KCL equations,
1 V for voltage constraints, and a scaled tolerance of 1e-10. Configurable options:

- `nonlinear_tolerance` (positive, less than one).
- `max_iterations` (1 to 1000; default 100).
- `current_residual_scale_a`, `voltage_residual_scale_v` (positive).
- `pivot_tolerance` for Newton linear solves (default 1e-12).

The initial unknown vector is all zero. At most 40 step halvings are allowed per
iteration. Trial exponential overflow triggers backtracking; the diode law is not
clipped to a fictitious finite current. A singular Jacobian, failed line search,
non-finite initial evaluation or iteration exhaustion raises a convergence failure.
A failure does not prove that the physical circuit has no solution.

Convergence is local, not a proof of uniqueness or global existence. The solver has
no continuation, source stepping, sparse factorization or automatic initial-guess
strategy yet. Its scope remains small reference networks, not general circuit design.
Linear-only networks continue using their original direct solve. The linear-only
`residual_tolerance` option is rejected for nonlinear networks to avoid ambiguity.

## Accounting and outputs

Branch power is still voltage drop times absorbed current. The cell's negative
absorbed electrical power is its delivered DC power. Resistive loads and leads
consume that power, so their independently calculated values must balance.

Near open circuit, a purely relative power test is undefined or misleading because
all powers approach zero. Acceptance therefore requires

`abs(sum(Pbranch)) <= 1e-9 W + 1e-9 * sum(abs(Pbranch))`.

Both absolute and relative residuals, plus the actual acceptance threshold, are
reported. No current/power value is clipped to make this check pass.

The report distinguishes:

- Solved cell DC delivery into this specific network.
- Available cell maximum DC power under the same radiation assumptions.
- Above-gap absorbed radiation.
- Unresolved non-electrical remainder (radiation minus delivered DC).

That last quantity is subtraction-based accounting, not a solved thermal balance.
It must not be interpreted as a calibrated cooling requirement.

## Verification and deferred work

The test suite checks generic nonlinear equations, equation scaling, backtracking,
explicit failures, the assembled analytic Jacobian against finite differences,
TPV load-line agreement with an independent scalar root solve, MPP load matching,
mismatched loads, open/short circuits, dark conditions, reverse-domain rejection,
and lead-loss accounting. Prior linear, generation and study tests remain in place.

Next: dynamic states and time integration with consistent initialization, then
network-specific batch studies and terminal laws for converters and storage.
Hydropower still has no electrical terminal adapter. Cross-technology comparisons,
measured device verification, and coupled thermal balance remain separate tasks.
