"""Run with python3 -m engine; standard library only."""
import argparse
import json
import sys
from pathlib import Path
from .runner import catalog, run, markdown
from .registry import get_model
from .network import run_network, network_markdown
from .studies import run_sweep, sweep_markdown, compare, comparison_markdown


def main():
    parser = argparse.ArgumentParser(description='Energy Systems Lab reference engine')
    commands = parser.add_subparsers(dest='command',required=True)
    listing = commands.add_parser('catalog',help='List technologies and actual model availability')
    listing.add_argument('--json',action='store_true')
    execution = commands.add_parser('run',help='Run a study JSON and write JSON + Markdown')
    execution.add_argument('scenario',type=Path)
    execution.add_argument('--output',type=Path,required=True,help='New output directory (existing reports are not overwritten)')
    description = commands.add_parser('describe', help='Describe a runnable model and its input units')
    description.add_argument('technology')
    sweep = commands.add_parser('sweep', help='Run a deterministic Cartesian parameter sweep')
    sweep.add_argument('scenario', type=Path)
    sweep.add_argument('--output', type=Path, required=True)
    comparison = commands.add_parser('compare', help='Compare compatible saved operating-point results')
    comparison.add_argument('results', nargs='+', type=Path)
    comparison.add_argument('--metrics', nargs='+', default=['net_electric_power'])
    comparison.add_argument('--output', type=Path, required=True)
    network = commands.add_parser('network', help='Assemble and solve a steady DC network')
    network.add_argument('scenario', type=Path)
    network.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'catalog':
            data = catalog()
            if args.json:
                print(json.dumps(data,indent=2))
            else:
                for t in data['technologies']:
                    print(f'{t["id"]:24} {"reference" if t["engine_runnable"] else "planned":10} {t["name"]}')
        elif args.command == 'describe':
            print(json.dumps(get_model(args.technology).describe(), indent=2))
        elif args.command in ('sweep', 'compare', 'network'):
            if args.output.exists():
                raise ValueError('Output directory already exists; choose a new directory')
            if args.command == 'network':
                result = run_network(json.loads(args.scenario.read_text()))
                report = network_markdown(result)
                filename = 'network.json'
            elif args.command == 'sweep':
                result = run_sweep(json.loads(args.scenario.read_text()))
                report = sweep_markdown(result)
                filename = 'batch.json'
            else:
                result = compare([json.loads(p.read_text()) for p in args.results], args.metrics)
                report = comparison_markdown(result)
                filename = 'comparison.json'
            payload = json.dumps(result, indent=2, allow_nan=False) + '\n'
            args.output.mkdir(parents=True)
            (args.output/filename).write_text(payload)
            (args.output/'report.md').write_text(report)
            print(f'Report: {args.output / "report.md"}')
            if args.command == 'sweep' and result['failed_count']:
                print(f'{result["failed_count"]} cases failed; inspect batch.json', file=sys.stderr)
                return 1
        else:
            if args.output.exists():
                raise ValueError('Output directory already exists; choose a new directory')
            study = json.loads(args.scenario.read_text())
            result = run(study)
            payload = json.dumps(result,indent=2,allow_nan=False)+'\n'
            report = markdown(result)
            args.output.mkdir(parents=True)
            (args.output/'result.json').write_text(payload)
            (args.output/'report.md').write_text(report)
            print(f'Reference result: {args.output / "report.md"}')
            print(f'Net electrical power: {result["metrics"]["net_electric_power"]["value"]:.6g} W')
    except (ValueError, OSError, OverflowError, ZeroDivisionError) as error:
        print(f'Error: {error}',file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
