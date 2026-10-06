"""Shared model input and metric construction helpers."""
import math


def exact_fields(data, required, optional=()):
    if not isinstance(data, dict):
        raise ValueError('Expected an object')
    missing, unknown = set(required) - data.keys(), data.keys() - set(required) - set(optional)
    if missing or unknown:
        raise ValueError(f'Missing fields: {sorted(missing)}; unknown fields: {sorted(unknown)}')


def metric(value, unit, scope):
    if not math.isfinite(value):
        raise ValueError('Non-finite computed metric')
    return {'value': value, 'unit': unit, 'scope': scope}
