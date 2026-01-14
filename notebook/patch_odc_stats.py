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


patched_file = patch_odc_stats_dump_json()
