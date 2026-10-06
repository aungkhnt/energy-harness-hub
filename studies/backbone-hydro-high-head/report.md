# hydropower-high-head-reference

**Reference simulation, not an empirically validated plant prediction.**

Technology: `hydropower`

| Metric | Value | Unit | Scope |
|---|---:|---|---|
| hydraulic_power | 39226.6 | W | prescribed hydraulic inlet to net electrical bus |
| shaft_power | 33342.61 | W | prescribed hydraulic inlet to net electrical bus |
| gross_electric_power | 31008.627 | W | prescribed hydraulic inlet to net electrical bus |
| auxiliary_power | 200 | W | prescribed hydraulic inlet to net electrical bus |
| net_electric_power | 30808.627 | W | prescribed hydraulic inlet to net electrical bus |
| conversion_losses | 8217.9727 | W | prescribed hydraulic inlet to net electrical bus |

## Illustrative economics

| Metric | Value | Unit |
|---|---:|---|
| initial_capital_cost | 50000 | USD |
| annual_delivered_energy | 123234.51 | kWh/year |
| discounted_lifecycle_cost | 70577.763 | USD |
| lcoe | 0.045955815 | USD/kWh |

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
  "energy_balance_residual_w": 7.275957614183426e-12
}
```

Input SHA-256: `5eafbd137a37c4087a84f8fddfbd8ffb788200c89886d6c32b730c9d80f75b7b`

Implementation SHA-256: `6741a8e1fcadee6ed6cba9597bde4d544f3a19d901e9a01e23144fba2390f9de`

The companion JSON includes the complete input snapshot, units, I–V data where applicable, and cost assumptions.
