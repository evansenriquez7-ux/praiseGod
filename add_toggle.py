import sys

def add_toggle(filepath, state_var, start_marker, end_marker, component_call):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the start of the rendering block
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print(f"Start marker not found in {filepath}")
        return
        
    end_idx = content.find(end_marker, start_idx)
    if end_idx == -1:
        print(f"End marker not found in {filepath}")
        return
    end_idx += len(end_marker)
    
    # Check if toggle is already there
    if f"{{ {state_var} ?" in content[start_idx-200:start_idx+200]:
        print(f"Toggle already exists in {filepath}")
        return

    # Create the wrapped block
    original_block = content[start_idx:end_idx]
    
    # We must indent the original block by 2 spaces if we are strict, but JS doesn't care.
    wrapped = f"""{{ {state_var} ? (
{component_call}
                  ) : (
{original_block}
                  )}}"""

    new_content = content[:start_idx] + wrapped + content[end_idx:]
    
    # Inject state variable
    state_decl = f"  const [{state_var}, set{state_var[0].upper() + state_var[1:]}] = useState(true); // Feature toggle\n"
    # Find start of component
    if "export default function PracticeView" in new_content:
        comp_idx = new_content.find("export default function PracticeView")
        brace_idx = new_content.find("{", comp_idx) + 1
        new_content = new_content[:brace_idx] + "\n" + state_decl + new_content[brace_idx:]
    elif "export default function ParentDashboard" in new_content:
        comp_idx = new_content.find("export default function ParentDashboard")
        brace_idx = new_content.find("{", comp_idx) + 1
        new_content = new_content[:brace_idx] + "\n" + state_decl + new_content[brace_idx:]

    # Inject import
    if "import QuestionRenderer" not in new_content:
        import_idx = new_content.find("import ")
        new_content = "import QuestionRenderer from '../components/QuestionRenderer';\n" + new_content
        
    with open(filepath, 'w') as f:
        f.write(new_content)
    print(f"Toggle added to {filepath}")

# PracticeView
pv_start = "{/* Worked Example Scaffolded decompositions"
pv_end = ")} // End standard MCQ format\n                    </div>\n                  )}"
if pv_end not in open('/workspaces/praiseGod/frontend/src/views/PracticeView.jsx').read():
    pv_end = "                    </div>\n                  )}"

pv_call = """                    <QuestionRenderer 
                      question={activeQuestion}
                      answer={practiceVisualAnswer}
                      setAnswer={setPracticeVisualAnswer}
                      answerResult={answerResult}
                    />"""

add_toggle('/workspaces/praiseGod/frontend/src/views/PracticeView.jsx', 'useV2Renderer', pv_start, pv_end, pv_call)

# ParentDashboard
pd_start = "{/* Worked Example Scaffolded decompositions"
pd_end = ")} // End error detect format\n                        </div>\n                      )}"
if pd_end not in open('/workspaces/praiseGod/frontend/src/views/ParentDashboard.jsx').read():
    # just find the end of the block
    pd_end = "                    </div>\n                  )}"

pd_call = """                    <QuestionRenderer 
                      question={matatagQuestion}
                      answer={matatagAnswer}
                      setAnswer={setMatatagAnswer}
                      answerResult={matatagResult}
                    />"""

# add_toggle('/workspaces/praiseGod/frontend/src/views/ParentDashboard.jsx', 'useV2Renderer', pd_start, pd_end, pd_call)
