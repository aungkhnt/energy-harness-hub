# hydropower-prescribed-resource-reference

**Reference simulation, not an empirically validated plant prediction.**

Technology: `hydropower`

| Metric | Value | Unit | Scope |
|---|---:|---|---|
| hydraulic_power | 19613.3 | W | prescribed hydraulic inlet to net electrical bus |
| shaft_power | 16671.305 | W | prescribed hydraulic inlet to net electrical bus |
| gross_electric_power | 15504.314 | W | prescribed hydraulic inlet to net electrical bus |
| auxiliary_power | 200 | W | prescribed hydraulic inlet to net electrical bus |
| net_electric_power | 15304.314 | W | prescribed hydraulic inlet to net electrical bus |
| conversion_losses | 4108.9863 | W | prescribed hydraulic inlet to net electrical bus |

## Illustrative economics

| Metric | Value | Unit |
|---|---:|---|
| initial_capital_cost | 50000 | USD |
| annual_delivered_energy | 61217.255 | kWh/year |
| discounted_lifecycle_cost | 70577.763 | USD |
| lcoe | 0.09251219 | USD/kWh |

## Assumptions and limits

- A hypothetical hydraulic operating point with prescribed net head and flow, not a site resource forecast.
- The economic inputs are invented demonstration values, not supplier quotes or market estimates.
- Annual operation is assumed at this fixed operating point for 4000 hours; no seasonal analysis is performed.
- Head is net available head after upstream hydraulic losses.
- Constant head, flow, density and efficiencies; no reservoir, resource-duration, cavitation or dispatch model.
- Negative net power is preserved as an importing operating point.
- Illustrative user-entered prices; no market-price or supply-chain evidence.
- Constant net output during assumed operating hours; availability is not predicted.
- Constant real costs; no escalation, degradation, financing schedule, taxes, subsidies, or replacement schedule.
- Omitted costs are not proven zero. Include fuel and heat-source costs in annual_opex when relevant.
- Not suitable for a cross-technology ranking without matching scope and completeness.

## Numerical diagnostics

```json
{
  "energy_balance_residual_w": 3.637978807091713e-12
}
```

Input SHA-256: `e4d7ac23221b1d0c6388e3e55a28242f06e1a5db2a5c62b81faa3f65d2093ce5`

Implementation SHA-256: `6741a8e1fcadee6ed6cba9597bde4d544f3a19d901e9a01e23144fba2390f9de`

The companion JSON includes the complete input snapshot, units, I–V data where applicable, and cost assumptions.
