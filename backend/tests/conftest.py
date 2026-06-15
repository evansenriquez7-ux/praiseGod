"""
conftest.py — pytest fixtures and dynamic test data for MATATAG Lab comprehensive tests.

Fetches all nodes and axis options from the running backend at session start.
Requires the backend to be running on localhost:8000.
"""

import re
import pytest
import requests

BASE = "http://localhost:8000/api"


def pytest_configure(config):
    """Fetch all test data from API once at session start."""
    try:
        nodes_resp = requests.get(f"{BASE}/matatag/nodes", timeout=10)
        nodes_resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(
            f"Backend not responding at {BASE}. "
            f"Run `./scripts/manage.sh start` before running tests.\n{e}"
        )

    pytest.all_nodes = nodes_resp.json()["nodes"]

    # Build all (node_id, axis_name, axis_value) triples
    pytest.all_axis_options = []
    for node in pytest.all_nodes:
        axes_resp = requests.get(
            f"{BASE}/matatag/difficulty-axes/{node['node_id']}", timeout=10
        )
        if axes_resp.ok:
            for axis in axes_resp.json()["axes"]:
                for opt in axis["options"]:
                    pytest.all_axis_options.append({
                        "node_id":     node["node_id"],
                        "competency":  node["competency"],
                        "grade":       node["grade"],
                        "concept":     node["primary_concept"],
                        "axis_name":   axis["name"],
                        "axis_label":  axis["label"],
                        "axis_value":  opt["value"],
                        "axis_label_val": opt["label"],
                    })

    # Nodes that support both MCQ and visual
    from backend.app.matatag_skeletons import VISUAL_COMPETENCY_ROUTES

    pytest.dual_support_nodes = []
    for node in pytest.all_nodes:
        fmts = node.get("available_formats", ["mcq"])
        if "mcq" in fmts and "visual" in fmts:
            pytest.dual_support_nodes.append(node)

    print(
        f"\n[conftest] Loaded {len(pytest.all_nodes)} nodes, "
        f"{len(pytest.all_axis_options)} axis options, "
        f"{len(pytest.dual_support_nodes)} dual-format nodes"
    )
