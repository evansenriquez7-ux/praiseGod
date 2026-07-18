"""
rebuild_knowledge_graph.py

Regenerates data/knowledge_graph_g1_3.json from
data/skeletons/vocab_annotation.json.

cumulative_vocab at each node is computed from student_vocab (not
introduces_vocab), plus the cross-branch baseline terms that are always
available to every node.

cumulative_concepts is computed by accumulating introduces_concepts and
the DNA concepts mapped to each node via NODE_TO_DNA.

Run:
    python scripts/rebuild_knowledge_graph.py
"""

import json
import os
import sys

# Add project root to sys.path so we can import backend packages
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.app.practice_gen.registry import NODE_TO_DNA

# Read from vocab_annotation.json at runtime — single source of truth
CROSS_BRANCH_TERMS = None

# Branch ordering for cumulative accumulation:
# Within each branch: G1 Q1 → Q2 → Q3 → Q4 → G2 Q1 → ... → G3 Q4
# Within each quarter: by index (0, 1, 2, ...)
BRANCH_ORDER = ["na", "mg", "dp"]
GRADE_ORDER = [1, 2, 3]
QUARTER_ORDER = [1, 2, 3, 4]


def chronological_sort_key(node_id: str) -> tuple:
    """Return a sort key that respects grade → quarter → branch → index ordering."""
    # Format: mat_g{grade}_{branch}_q{quarter}_{index}
    parts = node_id.split("_")
    grade = int(parts[1][1:])
    branch = parts[2]
    quarter = int(parts[3][1:])
    index = int(parts[4])
    branch_rank = BRANCH_ORDER.index(branch) if branch in BRANCH_ORDER else 99
    return (grade, quarter, branch_rank, index)


def rebuild(vocab_path: str, kg_path: str) -> None:
    with open(vocab_path) as f:
        vocab_data = json.load(f)

    # Read cross-branch terms from vocab_annotation.json — single source of truth
    cross_branch_terms = vocab_data.get("_cross_branch_terms", [
        "number", "equal", "more", "less", "how many", "total", "left", "count", "group"
    ])

    nodes_raw = vocab_data["nodes"]

    # Sort nodes into global chronological order
    sorted_ids = sorted(nodes_raw.keys(), key=chronological_sort_key)

    # Track global cumulative vocab and concepts
    global_cumulative_vocab: list[str] = []
    global_cumulative_concepts: list[str] = []

    result_nodes = {}

    for node_id in sorted_ids:
        node = nodes_raw[node_id]
        branch = node["branch"]
        grade = node["grade"]
        quarter = node["quarter"]
        index = node["index"]

        # cumulative_vocab = cross-branch terms + everything accumulated globally so far
        cum_vocab_set = set(cross_branch_terms) | set(global_cumulative_vocab)
        cumulative_vocab = sorted(cum_vocab_set)

        # cumulative_concepts = everything accumulated globally so far
        cum_concept_set = set(global_cumulative_concepts)
        cumulative_concepts = sorted(cum_concept_set)

        # prior_node_ids: all nodes in this branch that come before this one
        prior_ids = [
            nid for nid in sorted_ids
            if nodes_raw[nid]["branch"] == branch
            and chronological_sort_key(nid) < chronological_sort_key(node_id)
        ]

        # next_node_id
        later_in_branch = [
            nid for nid in sorted_ids
            if nodes_raw[nid]["branch"] == branch
            and chronological_sort_key(nid) > chronological_sort_key(node_id)
        ]
        next_node_id = later_in_branch[0] if later_in_branch else None

        # Grade-level metadata
        sentence_max = {1: 15, 2: 18, 3: 22}.get(grade, 15)
        number_format = {
            1: "no commas, no thousands separator",
            2: "no commas for numbers up to 1000",
            3: "space separator for thousands (e.g. 1 000)",
        }.get(grade, "no commas")

        result_nodes[node_id] = {
            "grade": grade,
            "branch": branch,
            "quarter": quarter,
            "index": index,
            "competency": node["competency"],
            "student_vocab": node.get("student_vocab", []),
            "curriculum_vocab": node.get("curriculum_vocab", []),
            "introduces_vocab": node.get("introduces_vocab", []),
            "introduces_concepts": node.get("introduces_concepts", []),
            "cumulative_vocab": cumulative_vocab,
            "cumulative_concepts": cumulative_concepts,
            "prior_node_ids": prior_ids,
            "next_node_id": next_node_id,
            "sentence_max_words": sentence_max,
            "number_format": number_format,
            "NOT_YET_KNOWN": [],
        }

        # Accumulate this node's student_vocab into global cumulative vocab
        for term in node.get("student_vocab", []):
            if term not in global_cumulative_vocab:
                global_cumulative_vocab.append(term)

        # Accumulate this node's introduces_concepts AND its DNA concepts into global cumulative concepts
        node_dnas = NODE_TO_DNA.get(node_id, [])
        for concept in node.get("introduces_concepts", []):
            if concept not in global_cumulative_concepts:
                global_cumulative_concepts.append(concept)
        for dna_concept in node_dnas:
            if dna_concept not in global_cumulative_concepts:
                global_cumulative_concepts.append(dna_concept)

    # After sequential accumulation, populate NOT_YET_KNOWN for each node.
    # NOT_YET_KNOWN = (all introduced vocab across the entire graph) - (cumulative_vocab + introduces_vocab of this node)
    all_introduced_vocab = set()
    for node in nodes_raw.values():
        all_introduced_vocab.update(node.get("student_vocab", []))

    for node_id, node in result_nodes.items():
        known_vocab = set(node["cumulative_vocab"]) | set(node["student_vocab"])
        not_yet_known = sorted(list(all_introduced_vocab - known_vocab))
        node["NOT_YET_KNOWN"] = not_yet_known

    output = {
        "_description": (
            "Knowledge graph for MATATAG G1-3. cumulative_vocab is computed "
            "from student_vocab only (not introduces_vocab). Cross-branch "
            "baseline terms are always included."
        ),
        "_generated_from": [
            "data/skeletons/vocab_annotation.json",
        ],
        "_generated_by": "scripts/rebuild_knowledge_graph.py",
        "_branch_ordering": (
            "Within each branch (na, mg, dp): "
            "Grade 1 Q1 → Q2 → Q3 → Q4 → Grade 2 Q1 → ... → Grade 3 Q4, "
            "then by index within each quarter."
        ),
        "_cross_branch_terms_included_in_all_cumulative_vocab": cross_branch_terms,
        "nodes": result_nodes,
    }

    with open(kg_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Rebuilt knowledge graph: {len(result_nodes)} nodes → {kg_path}")


if __name__ == "__main__":
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    vocab_path = os.path.abspath(os.path.join(base, "data", "skeletons", "vocab_annotation.json"))
    kg_path = os.path.abspath(os.path.join(base, "data", "knowledge_graph_g1_3.json"))
    rebuild(vocab_path, kg_path)
