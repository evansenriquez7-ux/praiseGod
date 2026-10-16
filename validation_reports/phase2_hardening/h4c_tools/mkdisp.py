# usage: python3 mkdisp.py ITEM  -- prints the dispatch message: plain read for <=2000 lines, explicit chunked reads otherwise
import sys
item = sys.argv[1]
p = f"/Users/enrichmentcap/Documents/antigravity/ccmed/local_only/scratch/h4c/prompts/{item}.prompt.txt"
n = len(open(p, encoding="utf-8").read().splitlines())
tail = "Do not open any other file, list any directory, run any command, or search. Then reply with exactly what that file asks for, and nothing else."
if n <= 2000:
    print(f"Read the file {p} completely. It may be longer than one Read returns: if a read stops before the end of the file, keep reading with offset until you have read every line. {tail}")
else:
    k = (n + 1099) // 1100
    words = {2: "two", 3: "three", 4: "four"}[k]
    calls = "\n".join(f"{i+1}. Read file_path={p} with offset={1+1100*i} and limit=1100" for i in range(k))
    print(f"Your first {words} tool calls must be exactly these {words} Read calls, in this order:\n{calls}\nTogether these cover all {n} lines of the file. {tail}")
