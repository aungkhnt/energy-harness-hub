# tpv-capacitor-startup

Fixed-step transient reference; see JSON for all samples and equations.

Steps: 60; duration: 0.03 s.

| Quantity | Energy (J) |
|---|---:|
| initial_stored_energy_j | 0 |
| final_stored_energy_j | 0.00465155021 |
| net_input_to_storage_j | 0.00498487605 |
| numerical_damping_j | 0.000333325843 |
| discrete_balance_residual_j | -4.31602996e-14 |

## Final node voltages

| Node | V |
|---|---:|
| ground | 0 |
| cell_bus | 0.335510838 |
| load_bus | 0.305009843 |

## Assumptions and limits

- Illustrative fixed-temperature TPV cell connected directly to a resistive load through a resistive lead.
- No MPPT, conditioning, auxiliary demand or heat-balance solution is included. Device calibration is deferred.
- An illustrative 0.1 F capacitor starts at zero volts across the load; its state evolves while TPV temperatures remain fixed.
- Fixed sources and fixed-temperature TPV only; no switching events, inductors, controllers or thermal dynamics.
- Backward Euler is first order and numerically dissipative. Numerical damping is not physical heat or a device loss.
- A converged algebraic solve and a closed discrete energy budget do not certify time-integration accuracy; refine the time step.
- Initial capacitor constraints must admit a unique supported initialization; ideal voltage-source/capacitor loops may be rejected even when their voltages are consistent.
- The t=0 sample is a solved right-hand initial state, not a pre-switch state. No instantaneous impulses are modeled.
- TPV parameters are uncalibrated reference assumptions; generating-domain checks apply to every sample, with no implicit MPPT or conditioning.

Input hash: `b75a154f9dfe6067f8966835543f63a79ff25b7dec5b9a863fe3aba8764c58e4`

Implementation hash: `324a3f25884cd9e1645d7daf0eec1974b52f3f684acff8159cf7f112f6f8bbbf`
