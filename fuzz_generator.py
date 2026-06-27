import json
import traceback
import itertools
from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.routes.matatag_router import get_matatag_lab_config
from backend.app.practice_gen.pipeline import run

def generate_test_cases(config):
    node_id = config['node_id']
    base_dp = {dim['name']: (dim['options'][0]['scalar'] if dim['dim_type'] == 'continuous' else dim['options'][0]['level']) for dim in config.get('difficulty_dimensions', [])}
    base_variants = {v['name']: v['default'] for v in config.get('contextual_variants', [])}
    base_formatter = config['formatters'][0]['name'] if config.get('formatters') else "mcq"

    cases = []
    
    # 1. Test every formatter
    for fmt in config.get('formatters', []):
        cases.append({
            'dp': base_dp,
            'variants': base_variants,
            'formatter': fmt['name'],
            'reason': f"Testing formatter {fmt['name']}"
        })

    # 2. Test every difficulty dimension option
    for dim in config.get('difficulty_dimensions', []):
        for opt in dim.get('options', []):
            dp = dict(base_dp)
            dp[dim['name']] = opt['scalar'] if dim['dim_type'] == 'continuous' else opt.get('level', opt.get('value'))
            cases.append({
                'dp': dp,
                'variants': base_variants,
                'formatter': base_formatter,
                'reason': f"Testing dimension {dim['name']} = {dp[dim['name']]}"
            })

    # 3. Test every contextual variant option
    for variant in config.get('contextual_variants', []):
        for opt in variant.get('options', []):
            variants = dict(base_variants)
            variants[variant['name']] = opt
            cases.append({
                'dp': base_dp,
                'variants': variants,
                'formatter': base_formatter,
                'reason': f"Testing variant {variant['name']} = {opt}"
            })

    return cases

def run_fuzzer():
    node_ids = get_all_node_ids()
    total_tests = 0
    failures = []

    print(f"Starting fuzzer on {len(node_ids)} competencies...")

    # For speed, let's limit to 5 nodes in this test run, or run all if requested.
    for node_id in node_ids:
        config = get_matatag_lab_config(node_id)
        if not config:
            continue
            
        grade = config.get('grade', 1)
        cases = generate_test_cases(config)
        
        for case in cases:
            total_tests += 1
            try:
                # build combined profile as the UI does
                combined_profile = {**case['dp'], **case['variants']}
                
                # Check variant restrictions for formatter
                fmt_config = next((f for f in config.get('formatters', []) if f['name'] == case['formatter']), None)
                if fmt_config and not fmt_config.get('supports_all_variants', True):
                    restrictions = fmt_config.get('variant_restrictions', {})
                    if restrictions:
                        skip = False
                        for r_k, r_v in restrictions.items():
                            if combined_profile.get(r_k) not in r_v:
                                skip = True
                                break
                        if skip:
                            continue # skip incompatible variant combination
                            
                result = run(
                    node_id=node_id,
                    student_grade=grade,
                    formatter=case['formatter'],
                    difficulty_profile=combined_profile
                )
                
                if not result or not result.get('problem_id'):
                    failures.append(f"{node_id} [{case['reason']}]: Empty result")
                    
            except Exception as e:
                failures.append(f"{node_id} [{case['reason']}]: {str(e)}")

    print(f"\nCompleted {total_tests} tests.")
    if failures:
        print(f"Found {len(failures)} failures:")
        for f in failures[:50]:
            print(f" - {f}")
        if len(failures) > 50:
            print("... and more.")
        
        with open("fuzzer_failures.json", "w") as f:
            json.dump(failures, f, indent=2)
            
    else:
        print("All tests passed perfectly! Zero crashes.")

if __name__ == "__main__":
    run_fuzzer()
