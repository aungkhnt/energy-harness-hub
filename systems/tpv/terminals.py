"""Terminal laws derived from existing generation models, without recalibration."""
import math
from engine.validation import exact_fields
from engine.registry import get_model
from engine.physics import K, Q


def prepare_tpv_terminal(parameters):
    exact_fields(parameters,['tpv_parameters'],['radiation_solver'])
    definition=get_model('tpv')
    p=definition.prepare(parameters['tpv_parameters'])
    if p['conditioning_efficiency']!=1 or p['auxiliary_power_w']!=0:
        raise ValueError('tpv_cell is a bare cell: conditioning_efficiency must be 1 and auxiliary_power_w must be 0; converters/auxiliaries need separate laws')
    metrics,diagnostics,_,warnings=definition.evaluate(p,parameters.get('radiation_solver',{}))
    return {
        'photocurrent_a':metrics['isc_a']['value'],
        'saturation_current_a':p['dark_saturation_current_density_a_m2']*p['cell_width_m']*p['cell_height_m'],
        'thermal_voltage_v':K*p['cell_temperature_k']/Q,
        'open_circuit_voltage_v':metrics['voc_v']['value'],
        'maximum_dc_power_w':metrics['cell_dc_power']['value'],
        'absorbed_radiation_power_w':metrics['absorbed_above_gap_power']['value'],
        'normalized_tpv_parameters':p,
        'radiation_solver':parameters.get('radiation_solver',{}),
        'radiation_diagnostics':diagnostics,
        'model_id':definition.model_id,
        'model_warnings':warnings,
    }


def tpv_current(voltage, parameters):
    """Return absorbed terminal current and dI/dV, not delivered current.

    Trials may leave the generating quadrant. Only final operating points in
    0 <= V <= Voc are accepted by the network; reverse breakdown is not modeled.
    """
    x=voltage/parameters['thermal_voltage_v']
    current=parameters['saturation_current_a']*math.expm1(x)-parameters['photocurrent_a']
    slope=parameters['saturation_current_a']*math.exp(x)/parameters['thermal_voltage_v']
    return current,slope
