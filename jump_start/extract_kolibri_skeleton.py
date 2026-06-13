import sqlite3
import json
import argparse
import os

def extract_kolibri_data(db_path, output_dir):
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        print("Please download the Kolibri channel database (e.g., Khan Academy English) and place it here.")
        return

    print(f"Connecting to Kolibri database at {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Try to extract nodes (titles, descriptions, parent_id to build the tree)
    nodes = {}
    print("Extracting nodes from content_contentnode...")
    try:
        cursor.execute("SELECT id, title, description, kind, parent_id FROM content_contentnode")
        for row in cursor.fetchall():
            node_id = row["id"]
            nodes[node_id] = {
                "id": node_id,
                "title": row["title"],
                "description": row["description"],
                "kind": row["kind"],
                "parent_id": row["parent_id"],
                "prerequisites": [] # Will populate later
            }
    except sqlite3.OperationalError as e:
        print(f"Warning: Could not query content_contentnode. Is this a valid Kolibri DB? ({e})")
        return

    # Try to extract prerequisite edges
    edges = []
    print("Extracting prerequisites from content_prerequisitecontentrelationship...")
    try:
        # Newer Kolibri versions use content_contentnode_has_prerequisite
        # with columns from_contentnode_id (prerequisite) and to_contentnode_id (target)
        cursor.execute("SELECT from_contentnode_id, to_contentnode_id FROM content_contentnode_has_prerequisite")
        for row in cursor.fetchall():
            prereq_id = row["from_contentnode_id"]
            target_id = row["to_contentnode_id"]
            edges.append({
                "target": target_id,
                "prerequisite": prereq_id
            })
            if target_id in nodes:
                nodes[target_id]["prerequisites"].append(prereq_id)
    except sqlite3.OperationalError as e:
        print(f"Warning: Could not query prerequisites. Table might not exist or schema differs. ({e})")
    
    conn.close()

    # Save to output
    os.makedirs(output_dir, exist_ok=True)
    nodes_path = os.path.join(output_dir, "nodes.json")
    edges_path = os.path.join(output_dir, "edges.json")

    with open(nodes_path, "w", encoding="utf-8") as f:
        json.dump(nodes, f, indent=2)
    with open(edges_path, "w", encoding="utf-8") as f:
        json.dump(edges, f, indent=2)

    print(f"Extraction complete! Extracted {len(nodes)} nodes and {len(edges)} prerequisite edges.")
    print(f"Saved to {nodes_path} and {edges_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Skeleton from Kolibri SQLite Database")
    parser.add_argument("--db", type=str, default="data/khan_academy.sqlite3", help="Path to Kolibri channel SQLite file")
    parser.add_argument("--output", type=str, default="output", help="Directory to save the JSON output")
    args = parser.parse_args()

    extract_kolibri_data(args.db, args.output)
