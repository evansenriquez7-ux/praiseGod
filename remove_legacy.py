import re

def remove_legacy(filepath, state_var):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the feature toggle declaration and remove it
    toggle_pattern = re.compile(r"^\s*const\s+\[" + state_var + r",\s*set[a-zA-Z0-9_]+\]\s*=\s*useState\(.*?\);\s*// Feature toggle\n", re.MULTILINE)
    content = toggle_pattern.sub("", content)

    # In PracticeView, the toggle structure is:
    # { useV2Renderer ? (
    #   <QuestionRenderer ... />
    # ) : (
    #   ... old code ...
    # )}
    
    # Let's find "{ useV2Renderer ? ("
    start_str = "{ useV2Renderer ? ("
    start_idx = content.find(start_str)
    
    if start_idx == -1:
        print(f"Toggle block not found in {filepath}")
        return
        
    # We want to keep the QuestionRenderer call.
    mid_str = ") : ("
    mid_idx = content.find(mid_str, start_idx)
    
    if mid_idx == -1:
        print("Mid block not found")
        return
        
    # The end of the block is ")}" but it matches the last brace of the component.
    # The string we replaced ended with ")} // End standard MCQ format\n                    </div>\n                  )}" or similar.
    # Let's use the Python script to just do a smart bracket matching.
    
    # Or just replace the whole file using string manipulation since we generated the block exactly.
    # Let's extract what was inside the True branch.
    true_branch = content[start_idx + len(start_str):mid_idx]
    
    # Now find the matching ")}" for the `start_idx`.
    # Count braces
    count = 0
    end_idx = -1
    for i in range(start_idx, len(content)):
        if content[i] == '{':
            count += 1
        elif content[i] == '}':
            count -= 1
            if count == 0:
                end_idx = i + 1
                break
                
    if end_idx == -1:
        print("Failed to find matching brace")
        return
        
    # Replace the whole block with just the true branch!
    # Note: true branch might have leading/trailing newlines.
    new_content = content[:start_idx] + true_branch.strip() + content[end_idx:]
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    print(f"Legacy code removed from {filepath}")

remove_legacy('/workspaces/praiseGod/frontend/src/views/PracticeView.jsx', 'useV2Renderer')
