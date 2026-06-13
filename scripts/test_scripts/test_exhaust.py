from backend.app import sympy_skeletons
import random
import traceback

def exhaust_test():
    skills_to_test = [
        "1.OA.A.1", "2.OA.A.1", "3.OA.D.8", "4.NF.A.1", "5.NF.A.1", 
        "6.EE.A.2", "7.EE.B.3", "8.EE.C.7", "N-RN.A.1", "G-CO.1"
    ]
    
    for skill_id in skills_to_test:
        for _ in range(50):
            try:
                seed = random.randint(1000, 99999)
                skel = sympy_skeletons.get_question_skeleton(skill_id, seed=seed, grade_level=5)
                
                # Test the correct key!
                correct_key = skel["correct_key"]
                correct_val = skel["correct_answer"]
                opt_val = skel["options"][correct_key]["value"]
                
                is_correct = sympy_skeletons.validate_answer(correct_val, opt_val)
                if not is_correct:
                    print(f"FAILED for {skill_id} (Seed {seed})!")
                    print(f"  correct_val: '{correct_val}'")
                    print(f"  opt_val: '{opt_val}'")
                    return
            except Exception as e:
                print(f"CRASH for {skill_id}: {e}")
                traceback.print_exc()
                return
                
    print("All tests passed!")

if __name__ == "__main__":
    exhaust_test()
