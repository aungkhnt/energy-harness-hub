"""Explicit input conversions. Not a symbolic dimensional-algebra package."""
import math

# dimension, scale to base, offset in base. Temperatures are absolute, not deltas.
UNITS = {
    's': ('time', 1.0, 0.0), 'ms': ('time', .001, 0.0),
    'F': ('capacitance', 1.0, 0.0), 'mF': ('capacitance', .001, 0.0), 'uF': ('capacitance', 1e-6, 0.0),
    'V': ('voltage', 1.0, 0.0), 'mV': ('voltage', .001, 0.0),
    'A': ('current', 1.0, 0.0), 'mA': ('current', .001, 0.0),
    'ohm': ('resistance', 1.0, 0.0), 'kohm': ('resistance', 1000.0, 0.0),
    '1': ('dimensionless', 1.0, 0.0), '%': ('dimensionless', .01, 0.0),
    'm': ('length', 1.0, 0.0), 'cm': ('length', .01, 0.0),
    'mm': ('length', .001, 0.0), 'um': ('length', 1e-6, 0.0),
    'K': ('temperature', 1.0, 0.0), 'degC': ('temperature', 1.0, 273.15),
    'W': ('power', 1.0, 0.0), 'kW': ('power', 1000.0, 0.0), 'MW': ('power', 1e6, 0.0),
    'm3/s': ('volume_flow', 1.0, 0.0), 'L/s': ('volume_flow', .001, 0.0),
    'kg/m3': ('density', 1.0, 0.0),
    'eV': ('energy', 1.602176634e-19, 0.0), 'J': ('energy', 1.0, 0.0),
    'A/m2': ('current_density', 1.0, 0.0), 'A/cm2': ('current_density', 1e4, 0.0),
}


def normalize(value, target_unit):
    """Bare numbers use the declared unit; objects must specify value and unit."""
    source_unit = target_unit
    if isinstance(value, dict):
        if set(value) != {'value', 'unit'}:
            raise ValueError('A quantity requires exactly value and unit')
        source_unit, value = value['unit'], value['value']
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Quantity value must be a finite number')
    if not isinstance(source_unit, str) or source_unit not in UNITS or target_unit not in UNITS:
        raise ValueError(f'Unsupported unit: {source_unit!r} or {target_unit!r}')
    sd, ss, so = UNITS[source_unit]
    td, ts, to = UNITS[target_unit]
    if sd != td:
        raise ValueError(f'Incompatible units: {source_unit} and {target_unit}')
    result = value if source_unit == target_unit else (value * ss + so - to) / ts
    if not math.isfinite(result):
        raise ValueError('Unit conversion overflow')
    return result
