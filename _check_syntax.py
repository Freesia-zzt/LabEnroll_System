import ast

with open("api/api.py", encoding="utf-8") as f:
    source = f.read()

try:
    ast.parse(source)
    print("Syntax OK")
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}")
    lines = source.split("\n")
    start = max(0, e.lineno - 3)
    for i in range(start, min(len(lines), e.lineno + 3)):
        marker = ">>>" if i + 1 == e.lineno else "   "
        print(f"{marker} {i+1:4d}: {lines[i]}")