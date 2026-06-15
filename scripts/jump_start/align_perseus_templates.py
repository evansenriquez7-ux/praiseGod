import json
import os

def align_templates(graph_path, templates_dir, output_path):
    print(f"Loading graph from {graph_path}...")
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)
        
    aligned_count = 0
    for node_id, node_data in graph.items():
        template_file = os.path.join(templates_dir, f"{node_id}.json")
        if os.path.exists(template_file):
            # To keep the graph lightweight, we just store a reference to the template file
            node_data['perseus_template_file'] = f"templates/{node_id}.json"
            aligned_count += 1
            
    print(f"Aligned {aligned_count} nodes with Perseus templates.")
    
    print(f"Saving updated graph to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)
    print("Done.")

if __name__ == '__main__':
    graph_file = 'output/ged_knowledge_graph.json'
    templates_directory = 'output/templates'
    # For test run, we'll output to a test file to avoid overwriting the massive graph immediately
    # if it goes wrong, but it's safe to overwrite if we want.
    output_file = 'output/ged_knowledge_graph.json'
    
    align_templates(graph_file, templates_directory, output_file)
