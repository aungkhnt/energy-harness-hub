# Network and equation backbone — v0.3

Update: [v0.5 capacitor transients](transient-networks.md) now supports a restricted
RC/TPV time-integration mode. Earlier roadmap statements below describe the prior
version; general dynamics and thermal coupling remain deferred.


Extension: [v0.4 nonlinear DC solving and TPV terminal integration](nonlinear-networks.md)
adds a real generator-terminal adapter and damped Newton solving. The remainder of
this document records the v0.3 linear-network contract.

Updated 2026-09-20. This layer makes a first physical connection network executable:
small, linear, steady DC circuits. Device calibration and coupled heat balance remain
deferred. Dynamic, nonlinear, thermal, fluid and mechanical networks are not yet implemented.

## What works

A network names its electrical nodes, a reference node, and connected two-terminal
modules. Supported modules are resistors and ideal independent voltage/current
sources. Their positive/negative terminals identify existing nodes. The domain is
explicitly `electrical_dc`; other physical domains are rejected.

The engine validates the structure, assembles equations, solves voltages and currents,
then calculates branch powers and conservation residuals. Node connectivity alone
is not sufficient: a connected network can still lack a unique voltage/current
solution. The linear solver rejects singular or numerically unresolved systems.

Run the supplied example:

```bash
python3 -m engine network scenarios/dc_distribution.json --output studies/local-dc-network
```

The command saves `network.json` and `report.md` into a new output directory. Its
result type is distinct from standalone generation results; existing operating-point
comparison and sweep commands do not implicitly accept networks.

## Equations and signs

For each resistor, current from its positive to negative terminal is

`I = (Vpositive - Vnegative) / R`.

A current source prescribes that signed current. A voltage source prescribes
`Vpositive - Vnegative` and introduces an unknown branch current. At every
non-reference node, the sum of signed outgoing currents is zero. The reference
node fixes the otherwise arbitrary voltage datum to zero.

Modified nodal analysis assembles a square system `A x = b`, where x contains
non-reference node voltages followed by voltage-source currents. The result stores:

- Variable identities and units (V or A).
- Equation identities and residual units (KCL in A, voltage laws in V).
- The original matrix and right-hand side.
- Normalized module parameters and original input snapshot.
- Solver tolerances, residuals, and input/implementation hashes.

The matrix mixes physical coefficient units as required by each equation and
variable. It is not a dimensionless coefficient matrix or a symbolic unit-algebra
implementation. The assembler is responsible for dimensionally consistent stamps.

For every branch, `Pabsorbed = (Vpositive - Vnegative) * I`.
Positive values mean absorption; negative values mean delivery. Summing independently
computed branch powers provides a network energy-conservation check. It is not a
thermal model: resistor dissipation is reported as electrical power absorbed without
predicting temperature or a cooling requirement.

## Numerical method and limits

`solve_linear(matrix, rhs)` uses row scaling and partial-pivot Gaussian elimination
for at most 256 unknowns. Network input limits are 64 nodes and 128 modules. This
small dependency-free solver is appropriate to the current reference circuits,
not a substitute for a sparse circuit solver at plant scale.

Rows are normalized by their largest absolute coefficient before elimination.
The scaled pivot threshold defaults to 1e-12. The original-system relative residual
per row is `abs(Ax-b) / (sum(abs(Aij*xj)) + abs(bi))`; the maximum must be at most
1e-10. A zero row with zero denominator has zero residual after a successful solve.

Small residuals are not condition numbers or guarantees of small forward error.
A future solver adapter can use established sparse linear/nonlinear implementations
without changing network inputs or the saved equation representation.

Each run reports KCL residuals at all nodes, including the reference, and a signed
power-balance residual. The relative power residual must be at most 1e-9.

## Source limits and generation integration

Sources currently impose electrical values. A voltage source is not automatically
a reactor, PV array, battery, or TPV model. The source can absorb or deliver power
as determined by the solved network.

An optional `max_delivery_power_w` parameter rejects a result requiring more power
than that source is assumed able to supply. It does not clamp output or change the
voltage/current law. Absorption limits, voltage droop, converter efficiency, controls,
and nonlinear device operating points are not modeled.

Connecting a real generator requires a declared terminal law or converter model,
not just inserting a previously calculated maximum-power number as an ideal source.
That is the next electrical integration seam. No inferred device rating is added.

## Input validation

- Unique node/module identifiers and an existing reference node.
- Two distinct, existing terminals per module; all nodes connected to the reference.
- Known module kinds and exact parameter names.
- Positive resistance; finite voltage/current; nonnegative optional delivery limit.
- Compatible explicit input units (including V, mV, A, mA, ohm, and kohm).
- Explicit assumptions; bounded problem size; known solver options.

Short circuits can be represented by a zero-volt voltage source if the resulting
system is well posed. Zero-ohm resistors, duplicate parallel ideal voltage constraints,
floating nodes, and unsupported domains are rejected rather than silently regularized.

## Example and next seams

The example connects a 48 V source, a 0.5 ohm distribution line, and 12/24 ohm loads
in parallel. Independent series/parallel reduction gives 8 ohm equivalent load,
48/8.5 A source delivery, and a load-bus voltage below 48 V. Tests compare against
that solution and check source polarity, branch power, singular networks, and limits.

Next architecture work:

1. Define generator/converter terminal laws and connect a generation result only
   when voltage/current behavior and power limits are explicit.
2. Generalize equation assembly to nonlinear residuals with scaling and convergence
   criteria; retain the linear assembler as a concrete implementation.
3. Introduce dynamic states and consistent initialization with a justified ODE/DAE
   solver, rather than assuming a connection graph specifies the dynamics.
4. Extend network study sweeps and comparisons using network-specific result contracts.

The independent TPV/hydropower models and prior saved studies remain available.
