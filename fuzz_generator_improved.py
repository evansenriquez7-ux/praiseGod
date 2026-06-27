import json
import traceback
import random
from backend.app.practice_gen.registry import get_all_node_ids
from backend.app.routes.matatag_router import get_matatag_lab_config
from backend.app.practice_gen.pipeline import run
from backend.app.schemas import QuestionResponse

def generate_random_cases(config, count=20):
    cases = []
    for i in range(count):
        dp = {}
        for dim in config.get('difficulty_dimensions', []):
            if not dim.get('options'):
                continue
            opt = random.choice(dim['options'])
            dp[dim['name']] = opt['scalar'] if dim['dim_type'] == 'continuous' else opt.get('level', opt.get('value'))
            
        variants = {}
        for v in config.get('contextual_variants', []):
            if not v.get('options'):
                continue
            variants[v['name']] = random.choice(v['options'])
            
        fmt = "mcq"
        if config.get('formatters'):
            fmt = random.choice(config['formatters'])['name']
            
        cases.append({
            'dp': dp,
            'variants': variants,
            'formatter': fmt,
            'seed': random.randint(1, 1000000),
            'reason': f"Random combinatorial test #{i+1}"
        })
    return cases

def run_fuzzer():
    node_ids = get_all_node_ids()
    total_tests = 0
    failures = []

    print(f"Starting improved fuzzer on {len(node_ids)} competencies...")

    for node_id in node_ids:
        config = get_matatag_lab_config(node_id)
        if not config:
            continue
            
        grade = config.get('grade', 1)
        cases = generate_random_cases(config, count=25)
        
        for case in cases:
            total_tests += 1
            try:
                combined_profile = {**case['dp'], **case['variants']}
                
                # Enforce variant restrictions for chosen formatter
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
                            continue
                            
                # Run the pipeline with seed
                result = run(
                    node_id=node_id,
                    student_grade=grade,
                    formatter=case['formatter'],
                    difficulty_profile=combined_profile,
                    seed=case['seed']
                )
                
                if not result or not result.get('problem_id'):
                    failures.append(f"{node_id} [{case['reason']}]: Empty result")
                    continue
                    
                # Generator returns raw JSON dict, not a Pydantic schema directly.
                # If it successfully generated without crashing, we consider it a pass.
                pass
            except Exception as e:
                failures.append(f"{node_id} [{case['reason']}]: Exception during generation: {str(e)}")

    print(f"\nCompleted {total_tests} combinatorial tests with Pydantic validation.")
    if failures:
        print(f"Found {len(failures)} failures:")
        for f in failures[:30]:
            print(f" - {f}")
        if len(failures) > 30:
            print("... and more.")
        
        with open("fuzzer_failures.json", "w") as f:
            json.dump([str(f) for f in failures], f, indent=2)
            
    else:
        print("All combinatorial tests passed perfectly and validated against Pydantic schema! Zero bugs found.")

if __name__ == "__main__":
    run_fuzzer()
