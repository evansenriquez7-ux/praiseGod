
import json

def dummy_get_available_formats(nid):
    return ["mcq"]

def test_nodes_logic():
    # Simulate node_ids like in registry
    node_ids = ["mat_g1_na_q1_0", "mat_g2_mg_q3_5", "mat_g3_dp_q4_10"]
    nodes = []
    for nid in node_ids:
        parts = nid.split("_")
        try:
            n_grade  = int(parts[1][1:])
            n_branch = parts[2].upper()
            n_quarter = int(parts[3][1:])
            n_index   = int(parts[4])
            print(f"Processed {nid}: G{n_grade} {n_branch} Q{n_quarter} I{n_index}")
        except Exception as e:
            print(f"Failed {nid}: {e}")

if __name__ == "__main__":
    test_nodes_logic()
