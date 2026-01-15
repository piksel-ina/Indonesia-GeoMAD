from __future__ import annotations

from pathlib import Path
import inspect
import re

import odc.stats.io as odc_stats_io

def patch_odc_stats_dump_json() -> Path:
    io_path = Path(inspect.getsourcefile(odc_stats_io))
    src = io_path.read_text(encoding="utf-8")

    if "from affine import Affine" in src:
        print(f"[OK] odc.stats.io already patched: {io_path}")
        return io_path

    pattern = (
        r"def dump_json\(meta: dict(\[str, Any\]|\[str, Any\])\) -> str:\n"
        r"\s+return json\.dumps\(meta, separators=\(\",\", \":\"\)\)\n"
    )

    replacement = """def dump_json(meta: dict[str, Any]) -> str:
    \"\"\"Dump metadata to JSON string, handling Affine objects\"\"\"
    from affine import Affine

    def convert_obj(obj):
        if isinstance(obj, Affine):
            return list(obj)[:6]
        elif isinstance(obj, dict):
            return {k: convert_obj(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_obj(item) for item in obj]
        return obj

    meta = convert_obj(meta)
    return json.dumps(meta, separators=(",", ":"))
"""

    new_src, n = re.subn(pattern, replacement, src)
    if n != 1:
        raise RuntimeError(f"Patch failed: expected dump_json() not found in {io_path}")

    # backup once
    bak = io_path.with_suffix(io_path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")

    io_path.write_text(new_src, encoding="utf-8")
    print(f"[PATCHED] Updated dump_json in: {io_path} (backup: {bak})")
    return io_path

def patch_odc_stats_xarray_dims() -> Path:
    """Patch xarray dims compatibility issue in load_with_native_transform"""
    io_path = Path(inspect.getsourcefile(odc_stats_io))
    src = io_path.read_text(encoding="utf-8")

    # Check if already patched
    if "list(_xx[0].dims)[0]" in src:
        print(f"[OK] odc.stats.io xarray dims already patched: {io_path}")
        return io_path

    # Pattern to find the problematic line (line 841)
    pattern = r"(\s+)xx = xr\.concat\(_xx, _xx\[0\]\.dims\[0\]\)(\s+# type: ignore)?"
    
    # Replacement with xarray compatibility fix
    replacement = r"\1xx = xr.concat(_xx, list(_xx[0].dims)[0])\2"

    new_src, n = re.subn(pattern, replacement, src)
    
    if n != 1:
        raise RuntimeError(f"Patch failed: expected xr.concat line not found in {io_path}. Found {n} matches.")

    # backup once (reuse existing backup system)
    bak = io_path.with_suffix(io_path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(src, encoding="utf-8")

    io_path.write_text(new_src, encoding="utf-8")
    print(f"[PATCHED] Fixed xarray dims compatibility in: {io_path}")
    return io_path

patched_file1 = patch_odc_stats_dump_json()
patched_file2 = patch_odc_stats_xarray_dims()