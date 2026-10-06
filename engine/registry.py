"""One model registry for dispatch, discoverability, and parameter units."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping
from .validation import exact_fields
from systems.hydropower.model import hydro
from systems.hydropower.parameters import PARAMETER_UNITS as HYDRO_UNITS
from systems.tpv.model import tpv
from systems.tpv.parameters import PARAMETER_UNITS as TPV_UNITS
from .units import normalize


@dataclass(frozen=True)
class ModelDefinition:
    technology: str
    model_id: str
    evaluate: Callable
    parameter_units: Mapping[str, str]
    description: str
    output_scope: str

    def prepare(self, parameters):
        exact_fields(parameters, self.parameter_units)
        return {key: normalize(parameters[key], unit) for key, unit in self.parameter_units.items()}

    def describe(self):
        return {'technology': self.technology, 'model_id': self.model_id,
                'execution_mode': 'steady_operating_point',
                'parameter_units': dict(self.parameter_units),
                'required_parameters': list(self.parameter_units),
                'description': self.description, 'output_scope': self.output_scope,
                'domain_reference': 'docs/reference-models.md',
                'empirical_validation': 'deferred'}


REGISTRY = MappingProxyType({
    'hydropower': ModelDefinition('hydropower', 'hydropower_reference_v1', hydro,
        MappingProxyType(HYDRO_UNITS), 'Prescribed head/flow with constant efficiencies.',
        'prescribed hydraulic inlet to net electrical bus'),
    'tpv': ModelDefinition('tpv', 'tpv_reference_v1', tpv, MappingProxyType(TPV_UNITS),
        'Fixed-temperature gray emitter and idealized cell.',
        'cell incident radiation to net electrical bus'),
})


def get_model(technology):
    if not isinstance(technology, str) or technology not in REGISTRY:
        raise ValueError(f'Unsupported runnable technology: {technology!r}. Available: {sorted(REGISTRY)}')
    return REGISTRY[technology]
