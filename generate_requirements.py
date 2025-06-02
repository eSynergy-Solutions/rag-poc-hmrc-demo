#!/usr/bin/env python3
# generate_requirements.py

import ast
import pathlib
import sys
from importlib.metadata import packages_distributions, version, PackageNotFoundError

# ——— CONFIG ———
PROJECT_ROOT = pathlib.Path(__file__).parent
REQ_DIR      = PROJECT_ROOT / "requirements"
APP_DIR      = PROJECT_ROOT / "app"
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"
# Packages to drop as “local” (not real PyPI dists)
LOCAL_MODULES = {"app"}
# Manually override certain module → distribution mappings
MODULE_DIST_OVERRIDES = {
    # you import from “opentelemetry”, but only need the API & SDK packages
    "opentelemetry": ["opentelemetry-api", "opentelemetry-sdk"],
}
# =============

def find_imports(paths, ignore_dirs=None):
    """Collect top-level module names imported under each path, skipping ignore_dirs."""
    mods = set()
    ignore_dirs = set(ignore_dirs or ())
    for base in paths:
        for py in pathlib.Path(base).rglob("*.py"):
            if ignore_dirs & set(py.parts):
                continue
            try:
                tree = ast.parse(py.read_text(), filename=str(py))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mods.add(alias.name.split(".",1)[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods.add(node.module.split(".",1)[0])
    return mods

def filter_third_party(mods):
    """Drop stdlib, private (underscore), and your LOCAL_MODULES."""
    std = sys.stdlib_module_names  # Py3.10+
    return {
        m for m in mods
        if m not in std
        and not m.startswith("_")
        and m not in LOCAL_MODULES
    }

def map_to_distributions(mods):
    """
    Map each module to one or more PyPI dists.
    Honors MODULE_DIST_OVERRIDES; otherwise uses packages_distributions().
    """
    pkg_map = packages_distributions()
    dists = set()
    for m in mods:
        if m in MODULE_DIST_OVERRIDES:
            dists.update(MODULE_DIST_OVERRIDES[m])
        elif m in pkg_map:
            dists.update(pkg_map[m])
        else:
            # fallback: assume module==dist
            dists.add(m)
    return dists

def collect_with_versions(dists):
    """Pin each dist to the installed version, skipping any not installed."""
    lines = []
    for dist in sorted(dists, key=str.lower):
        try:
            ver = version(dist)
            lines.append(f"{dist}=={ver}")
        except PackageNotFoundError:
            print(f"⚠️  Warning: distribution {dist!r} not installed; skipping.",
                  file=sys.stderr)
    return lines

def write_req(name, imports_set):
    """Filter, map, pin, and write out requirements/<name>.txt."""
    third = filter_third_party(imports_set)
    dists = map_to_distributions(third)
    lines = collect_with_versions(dists)

    out = REQ_DIR / f"{name}.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} entries to {out.relative_to(PROJECT_ROOT)}")

if __name__ == "__main__":
    # 1) Base = only app/ code (skip app/tests, scripts/)
    base_imports = find_imports([APP_DIR], ignore_dirs={"tests","scripts"})
    write_req("base", base_imports)

    # 2) Dev = app/ (including its tests) + scripts/
    dev_imports = find_imports([APP_DIR, SCRIPTS_DIR], ignore_dirs=None)
    write_req("dev", dev_imports)

    # 3) Prod = same as base (runtime-only)
    write_req("prod", base_imports)
