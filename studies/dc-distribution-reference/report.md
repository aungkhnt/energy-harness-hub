# dc-distribution-reference

Steady DC network reference; ideal source/load assumptions.

| Node | Voltage (V) |
|---|---:|
| ground | 0 |
| source_bus | 48 |
| load_bus | 45.176471 |

| Module | Voltage drop (V) | Current p→n (A) | Absorbed power (W) |
|---|---:|---:|---:|
| supply | 48 | -5.6470588 | -271.05882 |
| line | 2.8235294 | 5.6470588 | 15.944637 |
| load_one | 45.176471 | 3.7647059 | 170.07612 |
| load_two | 45.176471 | 1.8823529 | 85.038062 |

## Diagnostics

```json
{
  "linear_relative_residual": 7.401486830834377e-17,
  "minimum_scaled_pivot": 0.5,
  "node_kcl_residuals_a": {
    "ground": 1.9984014443252818e-15,
    "source_bus": 7.105427357601002e-15,
    "load_bus": -9.103828801926284e-15
  },
  "power_balance_residual_w": -6.927791673660977e-14,
  "relative_power_balance_residual": 1.277912960636248e-16,
  "unknown_count": 3,
  "equation_count": 3
}
```

## Assumptions and limits

- An ideal 48 V source supplies a distribution line and two resistive loads.
- All values are illustrative electrical assumptions; no generation-device calibration is implied.
- The source delivery cap is an assumed 500 W rating, not a measured capability.
- Ideal steady DC network; no dynamics, AC, semiconductor device law, or thermal coupling.
- Positive branch current flows from positive to negative terminal; positive power is absorbed, negative power is delivered.
- Sources are prescribed electrical assumptions, not automatically connected to TPV or hydropower results.
- Optional source delivery limits reject infeasible results; no voltage droop, saturation or control law is modeled.
- A small residual is not a condition-number estimate or empirical validation.

The companion JSON preserves all equations, inputs, normalized modules, and source hashes.
