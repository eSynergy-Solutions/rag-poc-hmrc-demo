#!/usr/bin/env python3
# verify_requirements.py

import ast
import pathlib
import sys

def find_imports(path):
    """Recursively collect all top‐level module names imported in .py files under `path`."""
    mods = set()
    for py in pathlib.Path(path).rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(), filename=str(py))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.add(alias.name.split(".", 1)[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module.split(".", 1)[0])
    return mods

def read_requirements(req_path):
    """Read a requirements.txt, return the set of package names (before '==')."""
    reqs = set()
    for line in pathlib.Path(req_path).read_text().splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        pkg = line.split("==",1)[0]
        reqs.add(pkg)
    return reqs

if __name__ == "__main__":
    # Adjust these paths if your structure differs
    code_dirs = ["app", "scripts", "app/tests"]
    req_file  = pathlib.Path("requirements") / "dev.txt"

    if not req_file.exists():
        print(f"ERROR: can’t find {req_file}", file=sys.stderr)
        sys.exit(1)

    # 1) Gather real imports
    real_imports = set()
    for d in code_dirs:
        real_imports |= find_imports(d)

    # 2) Read declared requirements
    declared = read_requirements(req_file)

    # 3) Compare
    missing   = sorted(real_imports - declared)
    unused    = sorted(declared    - real_imports)

    if missing:
        print("\n🔴 Imports _used_ in code but _missing_ from requirements/dev.txt:")
        for m in missing:
            print(f"  • {m}")
    else:
        print("\n✅ No missing requirements—every imported module is declared.")

    if unused:
        print("\n🔴 Packages listed in requirements/dev.txt but _never_ imported:")
        for u in unused:
            print(f"  • {u}")
    else:
        print("\n✅ No unused requirements—every declared package is imported somewhere.")
