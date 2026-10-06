"""Fixed-temperature TPV reference model."""
import math
from engine.validation import exact_fields, metric
from engine.physics import (H, C, Q, SIGMA, positive, fraction, integer, radiance,
                            integrate_log, rectangle_coupling, diode_mpp)


def tpv(p, options):
    required = ['emitter_temperature_k', 'cell_temperature_k', 'emissivity',
                'emitter_width_m', 'emitter_height_m', 'cell_width_m', 'cell_height_m',
                'gap_m', 'emitter_offset_x_m', 'emitter_offset_y_m', 'bandgap_ev',
                'external_quantum_efficiency', 'dark_saturation_current_density_a_m2',
                'conditioning_efficiency', 'auxiliary_power_w']
    exact_fields(p, required)
    exact_fields(options, [], ['geometry_cells', 'spectral_intervals', 'wavelength_min_m', 'wavelength_max_m', 'geometry_relative_tolerance'])
    for key in required:
        if key in ('emitter_offset_x_m', 'emitter_offset_y_m'):
            if isinstance(p[key], bool) or not isinstance(p[key], (int, float)) or not math.isfinite(p[key]):
                raise ValueError(f'{key} must be finite')
        elif key in ('emissivity', 'external_quantum_efficiency', 'conditioning_efficiency'):
            fraction(key, p[key])
        else:
            positive(key, p[key], allow_zero=(key=='auxiliary_power_w'))
    if not 1 <= p['cell_temperature_k'] < p['emitter_temperature_k'] <= 10000:
        raise ValueError('Reference model requires 1 <= cell temperature < emitter temperature <= 10000 K')
    if not .05 <= p['bandgap_ev'] <= 5:
        raise ValueError('Reference model supports bandgaps in [0.05, 5] eV')
    cells = integer('geometry_cells', options.get('geometry_cells', 8), 2, 16)
    intervals = integer('spectral_intervals', options.get('spectral_intervals', 512), 32, 8192)
    if intervals % 2:
        raise ValueError('spectral_intervals must be even')
    lower, upper = options.get('wavelength_min_m', 1e-8), options.get('wavelength_max_m', 1e-3)
    positive('wavelength_min_m', lower); positive('wavelength_max_m', upper)
    if not 1e-9 <= lower < upper <= 1:
        raise ValueError('Require 1e-9 <= wavelength_min_m < wavelength_max_m <= 1 m')
    cutoff = H * C / (p['bandgap_ev'] * Q)
    if not lower < cutoff < upper:
        raise ValueError('Spectral window must bracket the cell bandgap wavelength')
    if p['gap_m'] < 10 * upper:
        raise ValueError('Far-field reference model requires gap >= 10 times wavelength_max_m')
    args = [p[k] for k in ('emitter_width_m','emitter_height_m','cell_width_m','cell_height_m',
                          'gap_m','emitter_offset_x_m','emitter_offset_y_m')]
    coarse = rectangle_coupling(*args, cells=cells)
    coupling = rectangle_coupling(*args, cells=2*cells)
    error = abs(coupling-coarse)/coupling
    tolerance = options.get('geometry_relative_tolerance', .01)
    positive('geometry_relative_tolerance', tolerance)
    if tolerance > .05:
        raise ValueError('geometry_relative_tolerance cannot exceed 0.05')
    if error > tolerance:
        raise ValueError(f'Geometry refinement difference {error:.3g} exceeds tolerance {tolerance}; refine grid or change geometry')
    ae, ac = p['emitter_width_m']*p['emitter_height_m'], p['cell_width_m']*p['cell_height_m']
    if coupling > math.pi * min(ae, ac):
        raise ValueError('Geometry violates view-factor bounds; quadrature is unresolved')
    spectrum = lambda wavelength: radiance(wavelength, p['emitter_temperature_k'])
    total_l = integrate_log(spectrum, lower, upper, intervals)
    theoretical_l = SIGMA*p['emitter_temperature_k']**4/math.pi
    spectral_deficit = abs(total_l/theoretical_l - 1)
    if spectral_deficit > .005:
        raise ValueError('Spectral window/quadrature misses more than 0.5% of blackbody energy')
    scale = coupling*p['emissivity']
    incident = scale*total_l
    absorbed = scale*integrate_log(spectrum, lower, cutoff, intervals)
    photons = scale*integrate_log(lambda w: spectrum(w)*w/(H*C), lower, cutoff, intervals)
    iph = Q*p['external_quantum_efficiency']*photons
    cell = diode_mpp(iph, p['dark_saturation_current_density_a_m2']*ac, p['cell_temperature_k'])
    # Necessary checks, not a proof that a user-supplied diode parameter is physically calibrated.
    if cell['voc_v'] > p['bandgap_ev'] or cell['dc_power_w'] > absorbed:
        raise ValueError('Diode assumptions violate bandgap-voltage or incident-energy bounds')
    gross = cell['dc_power_w']*p['conditioning_efficiency']
    net = gross-p['auxiliary_power_w']
    non_electric = absorbed-cell['dc_power_w']
    reflected = incident-absorbed
    losses = cell['dc_power_w']-gross
    values = dict(incident_radiation_power=incident, absorbed_above_gap_power=absorbed,
                  reflected_subgap_power=reflected, cell_dc_power=cell['dc_power_w'],
                  gross_electric_power=gross, auxiliary_power=p['auxiliary_power_w'],
                  net_electric_power=net, conditioning_losses=losses,
                  unresolved_nonelectrical_power=non_electric)
    metrics = {key: metric(value,'W','cell incident radiation to net electrical bus') for key,value in values.items()}
    for key in ('voc_v','vmpp_v','isc_a','impp_a'):
        metrics[key] = metric(cell[key], 'V' if key.endswith('_v') else 'A', 'single idealized cell')
    efficiency_scope = 'net electricity / radiation incident on cell; excludes source heating'
    metrics['radiation_to_net_efficiency'] = (metric(net/incident, '1', efficiency_scope)
        if incident else {'value': None, 'unit': '1', 'scope': efficiency_scope,
                          'status': 'undefined_zero_incident_power'})
    diagnostics = dict(geometry_relative_refinement_difference=error,
                       geometry_cells_per_axis=2*cells,
                       spectral_relative_blackbody_deficit=spectral_deficit,
                       emitter_to_cell_view_factor=coupling/(math.pi*ae),
                       energy_balance_residual_w=incident-(reflected+non_electric+losses+p['auxiliary_power_w']+net))
    return metrics, diagnostics, {'iv_curve': cell['iv_curve']}, [
        'Illustrative graybody emitter and one ideal single-diode cell; not a calibrated material/device prediction.',
        'Parallel facing rectangles, far-field diffuse vacuum radiation, fixed temperatures, no reabsorption or photon recycling.',
        'Above-bandgap absorptivity is one, below-bandgap reflectivity is one; external quantum efficiency is constant above the gap.',
        'Dark saturation current is a user assumption at the specified cell temperature; ideality is one, series resistance zero, shunt resistance infinite.',
        'Non-electrical remainder includes unresolved heat and radiative emission; energy closure is bookkeeping, not independent thermal validation.',
        'Efficiency excludes emitter heating and source losses. This is a converter operating point, not whole-plant efficiency.',
        'Spatial irradiance is averaged for the cell I-V model; no temperature dynamics or electrical mismatch model.']
