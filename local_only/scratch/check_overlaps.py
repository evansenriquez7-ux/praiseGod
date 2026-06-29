import math
from backend.app.practice_gen.axes_catalog import CONCEPT_AXES_CATALOG
from backend.app.practice_gen.registry import get_all_node_ids, get_node_competency_bounds, get_node_dnas

def check_overlaps():
    node_ids = get_all_node_ids()
    for node_id in node_ids:
        dnas = get_node_dnas(node_id)
        if not dnas: continue
        primary_concept = dnas[0]
        axes = CONCEPT_AXES_CATALOG.get(primary_concept, [])
        bounds_dict = get_node_competency_bounds(node_id)
        
        for axis in axes:
            if axis.get("dim_type") == "continuous":
                axis_name = axis["name"]
                
                # Dynamic axis filtering
                if axis_name in bounds_dict and isinstance(bounds_dict[axis_name], bool):
                    continue
                    
                bounds = bounds_dict.get(axis_name)
                if bounds:
                    min_val, max_val = bounds
                else:
                    min_val = axis.get("default_min", 1)
                    max_val = axis.get("default_max", 100)
                    
                divisions = axis.get("divisions", 5)
                scale_type = axis.get("scale", "linear")
                
                values = []
                for i in range(divisions):
                    scalar = i / (divisions - 1) if divisions > 1 else 0.0
                    if scale_type == "logarithmic":
                        shift = 1 if min_val == 0 else 0
                        log_min = math.log10(min_val + shift)
                        log_max = math.log10(max_val + shift)
                        log_val = log_min + scalar * (log_max - log_min)
                        value = int(math.pow(10, log_val)) - shift
                    else:
                        if isinstance(min_val, float) or isinstance(max_val, float) or (max_val - min_val <= 2):
                            value = round(min_val + scalar * (max_val - min_val), 2)
                        else:
                            value = int(min_val + scalar * (max_val - min_val))
                    values.append(value)
                
                if len(values) != len(set(values)):
                    print(f"Overlap in {node_id} ({primary_concept}.{axis_name}) bounds=({min_val},{max_val}) divs={divisions}: {values}")

if __name__ == "__main__":
    check_overlaps()
