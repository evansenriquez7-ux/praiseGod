from backend.app.routes.matatag_router import _generate_lab_v2_student_problem
from backend.app.routes.practice_router import _generate_portal_student_problem


def test_lab_v2_and_portal_generation_are_field_identical():
    kwargs = {
        "node_id": "mat_g1_na_q1_0",
        "formatter": "cloze",
        "difficulty_profile": {"context": "pure", "direction": "forward"},
        "seed": 731,
        "interest_theme": "bible",
        "forced_dna": "counting",
    }

    lab = _generate_lab_v2_student_problem(**kwargs)
    portal = _generate_portal_student_problem(**kwargs)

    assert lab == portal
