# tpv-fixed-temperature-reference

**Reference simulation, not an empirically validated plant prediction.**

Technology: `tpv`

| Metric | Value | Unit | Scope |
|---|---:|---|---|
| incident_radiation_power | 23.736217 | W | cell incident radiation to net electrical bus |
| absorbed_above_gap_power | 9.2985339 | W | cell incident radiation to net electrical bus |
| reflected_subgap_power | 14.437683 | W | cell incident radiation to net electrical bus |
| cell_dc_power | 2.2281644 | W | cell incident radiation to net electrical bus |
| gross_electric_power | 2.1167561 | W | cell incident radiation to net electrical bus |
| auxiliary_power | 0.1 | W | cell incident radiation to net electrical bus |
| net_electric_power | 2.0167561 | W | cell incident radiation to net electrical bus |
| conditioning_losses | 0.11140822 | W | cell incident radiation to net electrical bus |
| unresolved_nonelectrical_power | 7.0703696 | W | cell incident radiation to net electrical bus |
| voc_v | 0.37452777 | V | single idealized cell |
| vmpp_v | 0.30836231 | V | single idealized cell |
| isc_a | 7.8315813 | A | single idealized cell |
| impp_a | 7.2258 | A | single idealized cell |
| radiation_to_net_efficiency | 0.084965355 | 1 | net electricity / radiation incident on cell; excludes source heating |

## Assumptions and limits

- All device parameters are illustrative assumptions, not measured properties of a named material.
- An external source holds the emitter at 2000 K and cooling holds the cell at 300 K; their energy costs are not modeled.
- Illustrative graybody emitter and one ideal single-diode cell; not a calibrated material/device prediction.
- Parallel facing rectangles, far-field diffuse vacuum radiation, fixed temperatures, no reabsorption or photon recycling.
- Above-bandgap absorptivity is one, below-bandgap reflectivity is one; external quantum efficiency is constant above the gap.
- Dark saturation current is a user assumption at the specified cell temperature; ideality is one, series resistance zero, shunt resistance infinite.
- Non-electrical remainder includes unresolved heat and radiative emission; energy closure is bookkeeping, not independent thermal validation.
- Efficiency excludes emitter heating and source losses. This is a converter operating point, not whole-plant efficiency.
- Spatial irradiance is averaged for the cell I-V model; no temperature dynamics or electrical mismatch model.

## Numerical diagnostics

```json
{
  "geometry_relative_refinement_difference": 0.0009497970886113656,
  "geometry_cells_per_axis": 16,
  "spectral_relative_blackbody_deficit": 1.9058506661728813e-08,
  "emitter_to_cell_view_factor": 0.011627792720767902,
  "energy_balance_residual_w": 0.0
}
```

Input SHA-256: `1caec91d69a876097a578f09632527b79ddcaa32b02ceea19e0330867487fdf0`

Implementation SHA-256: `3e05b7d91b4423e625951219d123bd4b6e4f0dca41cab7cd7febcafaf840398e`

The companion JSON includes the complete input snapshot, units, I–V data where applicable, and cost assumptions.
