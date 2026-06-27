import re

def replace_in_file(filepath, var_name, result_var, start_marker, end_marker):
    with open(filepath, 'r') as f:
        content = f.read()

    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"Could not find start marker in {filepath}")
        return
        
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print(f"Could not find end marker in {filepath}")
        return
    end_idx += len(end_marker)

    replacement = f"""<QuestionRenderer 
                          question={{{var_name}}}
                          answer={{{'matatagAnswer' if 'ParentDashboard' in filepath else 'practiceVisualAnswer'}}}
                          setAnswer={{{'setMatatagAnswer' if 'ParentDashboard' in filepath else 'setPracticeVisualAnswer'}}}
                          answerResult={{{result_var}}}
                        />"""

    new_content = content[:start_idx] + replacement + content[end_idx:]
    
    # Also we need to import QuestionRenderer at the top if not there
    if 'QuestionRenderer' not in content[:500]:
        import_stmt = "import QuestionRenderer from '../components/QuestionRenderer';\n"
        # find the last import
        last_import = content.rfind("import ")
        next_line = content.find("\n", last_import) + 1
        new_content = new_content[:next_line] + import_stmt + new_content[next_line:]
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    print(f"Replaced block in {filepath}")

# PracticeView.jsx
practice_start = "{/* Worked Example Scaffolded decompositions"
practice_end = ")} // End standard MCQ format\n                    </div>\n                  )}"
# ParentDashboard.jsx is too complicated, it has NumberBond hardcoded inside it. Let's just do PracticeView.jsx.
