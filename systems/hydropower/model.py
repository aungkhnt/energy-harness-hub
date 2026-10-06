"""Prescribed-head hydropower reference model."""
from engine.validation import exact_fields, metric
from engine.physics import positive, fraction


def hydro(p, options):
    exact_fields(p, ['head_m', 'flow_m3_s', 'water_density_kg_m3',
                     'turbine_efficiency', 'generator_efficiency', 'auxiliary_power_w'])
    exact_fields(options, [])
    for key in ('head_m', 'water_density_kg_m3'):
        positive(key, p[key])
    for key in ('flow_m3_s', 'auxiliary_power_w'):
        positive(key, p[key], allow_zero=True)
    for key in ('turbine_efficiency', 'generator_efficiency'):
        fraction(key, p[key])
    available = p['water_density_kg_m3'] * 9.80665 * p['flow_m3_s'] * p['head_m']
    shaft = available * p['turbine_efficiency']
    gross = shaft * p['generator_efficiency']
    net = gross - p['auxiliary_power_w']
    metrics = {key: metric(value, 'W', 'prescribed hydraulic inlet to net electrical bus')
               for key, value in dict(hydraulic_power=available, shaft_power=shaft,
                   gross_electric_power=gross, auxiliary_power=p['auxiliary_power_w'],
                   net_electric_power=net, conversion_losses=available-gross).items()}
    return metrics, {'energy_balance_residual_w': available - (net + p['auxiliary_power_w'] + available - gross)}, {}, [
        'Head is net available head after upstream hydraulic losses.',
        'Constant head, flow, density and efficiencies; no reservoir, resource-duration, cavitation or dispatch model.',
        'Negative net power is preserved as an importing operating point.']
