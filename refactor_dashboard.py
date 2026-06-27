import re

def replace_dashboard_legacy():
    filepath = '/workspaces/praiseGod/frontend/src/views/ParentDashboard.jsx'
    with open(filepath, 'r') as f:
        content = f.read()

    start_str = "{/* Worked Example Scaffolded decompositions"
    end_str = ")} // End error detect format\n                        </div>\n                      )}"
    
    start_idx = content.find(start_str)
    
    # Actually, let's just find the end of the block properly.
    # The block ends after the fallback MCQ format or after error detect.
    # Let's search for "Enter the missing number..." to ensure NumberBond is inside.
    if "Enter the missing number..." not in content:
        print("NumberBond not found in ParentDashboard.jsx. Has it already been refactored?")
        return
        
    end_idx = content.find(end_str)
    if end_idx == -1:
        # Fallback end search
        end_idx = content.find("                    </div>\n                  )}")
        
    if start_idx == -1 or end_idx == -1:
        print(f"Could not find bounds in ParentDashboard.jsx: start={start_idx}, end={end_idx}")
        return
        
    # We add length of end_str if we used end_str
    if end_idx != -1 and content[end_idx:end_idx+len(end_str)] == end_str:
        end_idx += len(end_str)
        
    # Construct the renderer component call
    replacement = """                  <QuestionRenderer 
                    question={matatagQuestion}
                    answer={matatagAnswer}
                    setAnswer={setMatatagAnswer}
                    answerResult={matatagResult}
                  />"""
                  
    new_content = content[:start_idx] + replacement + content[end_idx:]
    
    # Import QuestionRenderer if needed
    if "import QuestionRenderer" not in new_content:
        import_stmt = "import QuestionRenderer from '../components/QuestionRenderer';\n"
        last_import = new_content.rfind("import ")
        next_line = new_content.find("\n", last_import) + 1
        new_content = new_content[:next_line] + import_stmt + new_content[next_line:]
        
    with open(filepath, 'w') as f:
        f.write(new_content)
    print("Replaced legacy code in ParentDashboard.jsx with QuestionRenderer!")

if __name__ == '__main__':
    replace_dashboard_legacy()
