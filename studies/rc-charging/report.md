# rc-charging-reference

Fixed-step transient reference; see JSON for all samples and equations.

Steps: 100; duration: 0.5 s.

| Quantity | Energy (J) |
|---|---:|
| initial_stored_energy_j | 0 |
| final_stored_energy_j | 0.492424424 |
| net_input_to_storage_j | 0.504618841 |
| numerical_damping_j | 0.0121944167 |
| discrete_balance_residual_j | 6.00387795e-15 |

## Final node voltages

| Node | V |
|---|---:|
| ground | 0 |
| supply | 10 |
| storage | 9.9239551 |

## Assumptions and limits

- Illustrative 10 V source, 10 ohm resistor and 10 mF capacitor initially at zero volts.
- Source and resistance remain constant; no switching impulse, temperature or device calibration is modeled.
- Fixed sources and fixed-temperature TPV only; no switching events, inductors, controllers or thermal dynamics.
- Backward Euler is first order and numerically dissipative. Numerical damping is not physical heat or a device loss.
- A converged algebraic solve and a closed discrete energy budget do not certify time-integration accuracy; refine the time step.
- Initial capacitor constraints must admit a unique supported initialization; ideal voltage-source/capacitor loops may be rejected even when their voltages are consistent.
- The t=0 sample is a solved right-hand initial state, not a pre-switch state. No instantaneous impulses are modeled.

Input hash: `ff41ff90920a17bbd9ee056560c096d60f8f0f313751654a56e47ef14481b398`

Implementation hash: `324a3f25884cd9e1645d7daf0eec1974b52f3f684acff8159cf7f112f6f8bbbf`
