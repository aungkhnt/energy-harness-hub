# tpv-connected-load

Steady DC network reference; ideal source/load assumptions.

| Node | Voltage (V) |
|---|---:|
| ground | 0 |
| cell_bus | 0.33551086 |
| load_bus | 0.30500987 |

| Module | Voltage drop (V) | Current p→n (A) | Absorbed power (W) |
|---|---:|---:|---:|
| cell | 0.33551086 | -6.1001975 | -2.0466825 |
| lead | 0.030500987 | 6.1001975 | 0.18606205 |
| load | 0.30500987 | 6.1001975 | 1.8606205 |

## TPV operating points

| Cell | Delivered DC (W) | Available MPP (W) | Absorbed radiation (W) |
|---|---:|---:|---:|
| cell | 2.0466825 | 2.2281644 | 9.2985339 |

## Diagnostics

```json
{
  "linear_relative_residual": null,
  "minimum_scaled_pivot": null,
  "node_kcl_residuals_a": {
    "ground": -6.217248937900877e-15,
    "cell_bus": 0.0,
    "load_bus": 6.217248937900877e-15
  },
  "power_balance_residual_w": 1.6930901125533637e-15,
  "relative_power_balance_residual": 4.1361816392346587e-16,
  "power_balance_acceptance_threshold_w": 5.093364992710151e-09,
  "unknown_count": 2,
  "equation_count": 2,
  "nonlinear_scaled_residual": 1.4210854715202004e-14,
  "nonlinear_iterations": 7,
  "line_search_backtracks": 2
}
```

## Assumptions and limits

- Illustrative fixed-temperature TPV cell connected directly to a resistive load through a resistive lead.
- No MPPT, conditioning, auxiliary demand or heat-balance solution is included. Device calibration is deferred.
- Steady DC network with ideal sources, resistors and optional ideal-diode TPV cells; no dynamics, AC or thermal coupling.
- Positive branch current flows from positive to negative terminal; positive power is absorbed, negative power is delivered.
- Ideal sources remain prescribed assumptions. tpv_cell modules derive a terminal law from the existing fixed-temperature TPV reference model; hydropower has no terminal adapter yet.
- Optional source delivery limits reject infeasible results; no voltage droop, saturation or control law is modeled.
- A small residual is not a condition-number estimate or empirical validation.
- Illustrative graybody emitter and one ideal single-diode cell; not a calibrated material/device prediction.
- Parallel facing rectangles, far-field diffuse vacuum radiation, fixed temperatures, no reabsorption or photon recycling.
- Above-bandgap absorptivity is one, below-bandgap reflectivity is one; external quantum efficiency is constant above the gap.
- Dark saturation current is a user assumption at the specified cell temperature; ideality is one, series resistance zero, shunt resistance infinite.
- Non-electrical remainder includes unresolved heat and radiative emission; energy closure is bookkeeping, not independent thermal validation.
- Efficiency excludes emitter heating and source losses. This is a converter operating point, not whole-plant efficiency.
- Spatial irradiance is averaged for the cell I-V model; no temperature dynamics or electrical mismatch model.
- TPV output is raw cell DC at the load-selected operating point. No MPPT, power conditioner or auxiliary load is silently applied.

The companion JSON preserves all equations, inputs, normalized modules, and source hashes.
