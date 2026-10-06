"""Reproducible execution records; unsupported models fail explicitly."""
import hashlib
import json
from pathlib import Path
from . import __version__
from .validation import exact_fields
from .registry import REGISTRY, get_model
from .contracts import validate_metrics
from .economics import assess

ROOT = Path(__file__).resolve().parent.parent


def catalog():
    data = json.loads((ROOT/'catalog/plants.json').read_text())
    for entry in data['technologies']:
        entry['engine_runnable'] = entry['id'] in REGISTRY
        if entry['engine_runnable']:
            entry['model_id'] = REGISTRY[entry['id']].model_id
    return data


def digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def implementation_digest():
    # Hash executable first-party engine and system code; archive scripts are separate.
    files = list((ROOT/'engine').rglob('*.py'))
    files += [p for p in (ROOT/'systems').rglob('*.py') if 'legacy' not in p.relative_to(ROOT/'systems').parts]
    return digest({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(files)})


def prepare_study(study):
    exact_fields(study,['schema_version','study_id','technology','parameters','assumptions'],['solver','economics'])
    if study['schema_version'] != '0.1.0':
        raise ValueError('Unsupported study schema_version')
    if not isinstance(study['study_id'],str) or not study['study_id'].strip():
        raise ValueError('study_id must be a nonempty string')
    definition = get_model(study['technology'])
    if not isinstance(study['assumptions'],list) or not study['assumptions'] or any(not isinstance(a,str) or not a.strip() for a in study['assumptions']):
        raise ValueError('assumptions must be a nonempty list of explanatory strings')
    # Make a detached, JSON-safe snapshot before running.
    snapshot = json.loads(json.dumps(study,allow_nan=False))
    normalized = definition.prepare(snapshot['parameters'])
    return definition, snapshot, normalized


def run(study):
    definition, snapshot, normalized = prepare_study(study)
    metrics, diagnostics, series, warnings = definition.evaluate(normalized,snapshot.get('solver',{}))
    validate_metrics(metrics)
    result = {
        'schema_version':'0.1.0','status':'completed_reference_model',
        'study_id':study['study_id'], 'technology':study['technology'],
        'model_id':definition.model_id, 'engine_version':__version__,
        'input_sha256':digest(snapshot),'implementation_sha256':implementation_digest(),
        'input_snapshot':snapshot,'normalized_parameters':normalized,
        'model_definition':definition.describe(),'metrics':metrics,'diagnostics':diagnostics,
        'series':series,'warnings':warnings,
        'validation_status':'computational_reference_checks_only_not_empirically_validated',
        'evidence_manifest':'evidence/references.md',
        'economics':None,
        'unsupported_outputs':['deployment_feasibility','supply_chain','propulsion','transient_dynamics']}
    if 'economics' in snapshot:
        result['economics'] = assess(metrics['net_electric_power']['value'],snapshot['economics'])
    json.dumps(result, allow_nan=False)
    return result


def markdown(result):
    rows = ['# '+result['study_id'],'',
            '**Reference simulation, not an empirically validated plant prediction.**','',
            'Technology: `'+result['technology']+'`','',
            '| Metric | Value | Unit | Scope |','|---|---:|---|---|']
    def safe(text):
        return str(text).replace('|','\\|').replace('\n',' ')
    for name,m in result['metrics'].items():
        value = 'undefined' if m['value'] is None else f'{m["value"]:.8g}'
        rows.append(f'| {safe(name)} | {value} | {safe(m["unit"])} | {safe(m["scope"])} |')
    if result['economics']:
        rows += ['','## Illustrative economics','', '| Metric | Value | Unit |','|---|---:|---|']
        for name,m in result['economics']['metrics'].items():
            rows.append(f'| {safe(name)} | {m["value"]:.8g} | {safe(m["unit"])} |')
    rows += ['','## Assumptions and limits','']
    warnings = result['input_snapshot']['assumptions'] + result['warnings']
    if result['economics']:
        warnings += result['economics']['warnings']
    rows += ['- '+safe(w) for w in warnings]
    rows += ['','## Numerical diagnostics','', '```json',json.dumps(result['diagnostics'],indent=2),'```',
             '', 'Input SHA-256: `'+result['input_sha256']+'`',
             '', 'Implementation SHA-256: `'+result['implementation_sha256']+'`','',
             'The companion JSON includes the complete input snapshot, units, I–V data where applicable, and cost assumptions.','']
    return '\n'.join(rows)
