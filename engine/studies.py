"""Deterministic Cartesian sweeps and conservative within-model comparisons."""
import copy
import itertools
import math
from .validation import exact_fields
from .runner import run, digest, prepare_study
from .contracts import validate_metrics
from .numerics import ConvergenceError

MAX_CASES = 256


def run_sweep(spec):
    """Sweep explicit parameter values; expected case failures do not hide other cases.

    Structural errors fail before execution. Programming errors propagate. Results
    retain input settings and errors; failed runs never become zero-valued metrics.
    """
    exact_fields(spec, ['schema_version','study_id','base_study','axes'])
    if spec['schema_version'] != '0.1.0':
        raise ValueError('Unsupported sweep schema_version')
    if not isinstance(spec['study_id'],str) or not spec['study_id'].strip():
        raise ValueError('Sweep study_id must be nonempty')
    base = spec['base_study']
    exact_fields(base,['schema_version','study_id','technology','parameters','assumptions'],['solver','economics'])
    definition, _, _ = prepare_study(base)
    axes = spec['axes']
    if not isinstance(axes,dict) or not axes:
        raise ValueError('axes must be a nonempty object of parameter names and value lists')
    for key, values in axes.items():
        if key not in definition.parameter_units:
            raise ValueError(f'Unknown sweep parameter: {key}')
        if not isinstance(values,list) or not values:
            raise ValueError(f'Axis {key} must contain a nonempty list')
    count = math.prod(len(values) for values in axes.values())
    if count > MAX_CASES:
        raise ValueError(f'Sweep has {count} cases; limit is {MAX_CASES}')
    snapshot = copy.deepcopy(spec)
    spec_hash = digest(snapshot)  # rejects non-JSON values, NaN and infinity
    keys = sorted(axes)
    cases = []
    for index, values in enumerate(itertools.product(*(axes[key] for key in keys)),1):
        study = copy.deepcopy(base)
        settings = dict(zip(keys,copy.deepcopy(values)))
        study['parameters'].update(settings)
        case_id = f'{spec["study_id"]}:{index:04d}'
        study['study_id'] = case_id
        case = {'case_id':case_id,'settings':settings}
        try:
            case.update(status='completed',result=run(study))
        except ConvergenceError as error:
            case.update(status='failed',error={'kind':'numerical_convergence','message':str(error)})
        except (OverflowError, ZeroDivisionError) as error:
            case.update(status='failed',error={'kind':'numerical_domain','message':str(error)})
        except ValueError as error:
            case.update(status='failed',error={'kind':'invalid_input_or_model_domain','message':str(error)})
        cases.append(case)
    completed = sum(case['status']=='completed' for case in cases)
    status = 'completed' if completed==count else ('partial_failure' if completed else 'failed')
    return {'schema_version':'0.1.0','study_id':spec['study_id'],'status':status,
            'input_sha256':spec_hash,'input_snapshot':snapshot,
            'case_count':count,'completed_count':completed,'failed_count':count-completed,
            'execution_order':'Cartesian product of lexically sorted parameter names; value list order preserved',
            'cases':cases}


def compare(results, metric_names):
    """Descriptive within-model operating-point comparison, not equal-service ranking.

    Require same model/version, implementation digest, selected metric units and
    scope. Distinct technologies and economic comparisons await service contracts.
    """
    if not isinstance(results,list) or len(results)<2:
        raise ValueError('Comparison requires at least two successful results')
    if not isinstance(metric_names,list) or not metric_names or any(not isinstance(n,str) or not n for n in metric_names):
        raise ValueError('metric_names must be a nonempty list of strings')
    if len(set(metric_names)) != len(metric_names):
        raise ValueError('Duplicate comparison metrics')
    baseline = results[0]
    columns = []
    for result in results:
        if not isinstance(result,dict) or result.get('status')!='completed_reference_model':
            raise ValueError('Comparison accepts successful reference results only')
        validate_metrics(result.get('metrics'))
        for field in ('model_id','implementation_sha256'):
            if not isinstance(result.get(field),str) or result[field]!=baseline.get(field):
                raise ValueError(f'Comparison requires matching {field}')
        if not isinstance(result.get('study_id'),str):
            raise ValueError('Comparison result requires study_id')
        for name in metric_names:
            item = result['metrics'].get(name)
            reference = baseline['metrics'].get(name)
            if item is None or reference is None:
                raise ValueError(f'Missing comparison metric: {name}')
            if (item['unit'],item['scope']) != (reference['unit'],reference['scope']):
                raise ValueError(f'Incompatible unit or scope for {name}')
    for name in metric_names:
        item=baseline['metrics'][name]
        columns.append({'metric':name,'unit':item['unit'],'scope':item['scope']})
    return {'schema_version':'0.1.0','comparison_kind':'within_model_operating_points',
            'columns':columns,
            'rows':[{'study_id':r['study_id'],'input_sha256':r.get('input_sha256'),
                     'values':{name:r['metrics'][name]['value'] for name in metric_names}}
                    for r in results],
            'warnings':['Descriptive parameter comparison only; equal energy, reliability, and system service are not established.',
                        'No winner or weighted ranking is inferred. Null values remain undefined.',
                        'Consult each source result for its complete input assumptions and model limitations.']}


def comparison_markdown(table):
    def clean(value):
        return str(value).replace('|','\\|').replace('\n',' ')
    names=[c['metric'] for c in table['columns']]
    lines=['# Operating-point comparison','',
           '| Study | '+' | '.join(clean(c['metric']+' ('+c['unit']+')') for c in table['columns'])+' |',
           '|---|'+'---:|'*len(names)]
    for row in table['rows']:
        values=['undefined' if row['values'][n] is None else f'{row["values"][n]:.8g}' for n in names]
        lines.append('| '+clean(row['study_id'])+' | '+' | '.join(values)+' |')
    lines+=['','## Metric scopes','']+[f'- {clean(c["metric"])}: {clean(c["scope"])}' for c in table['columns']]
    lines+=['','## Interpretation','']+['- '+w for w in table['warnings']]
    return '\n'.join(lines)+'\n'


def sweep_markdown(batch):
    lines=['# '+batch['study_id'],'',
           f'Status: {batch["status"]}. Completed: {batch["completed_count"]}/{batch["case_count"]}.','',
           '| Case | Status | Details |','|---|---|---|']
    for case in batch['cases']:
        detail = 'See complete result in batch.json' if case['status']=='completed' else case['error']['message']
        lines.append('| '+case['case_id'].replace('|','\\|').replace('\n',' ')+' | '+case['status']+' | '+detail.replace('|','\\|').replace('\n',' ')+' |')
    results=[case['result'] for case in batch['cases'] if case['status']=='completed']
    if len(results)>=2:
        lines+=['',comparison_markdown(compare(results,['net_electric_power']))]
    return '\n'.join(lines)+'\n'
