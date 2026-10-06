"""Result-interface checks shared by execution and comparison."""
import math


def validate_metrics(metrics):
    if not isinstance(metrics, dict) or not metrics:
        raise ValueError('Model must return a nonempty metrics object')
    for name, metric in metrics.items():
        if not isinstance(name, str) or not name or not isinstance(metric, dict):
            raise ValueError('Metrics require names and objects')
        if not {'value', 'unit', 'scope'} <= metric.keys():
            raise ValueError(f'Metric {name} lacks value, unit or scope')
        if any(not isinstance(metric[k], str) or not metric[k].strip() for k in ('unit','scope')):
            raise ValueError(f'Metric {name} requires nonempty unit and scope')
        value = metric['value']
        if value is None:
            if not isinstance(metric.get('status'),str) or not metric['status'].startswith('undefined_'):
                raise ValueError(f'Metric {name} must explain its undefined value')
        elif isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
            raise ValueError(f'Metric {name} must be finite or explicitly undefined')
