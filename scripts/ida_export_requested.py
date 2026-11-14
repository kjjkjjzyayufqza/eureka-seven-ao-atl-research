"""Export only requested functions from the research IDB, without MCP truncation."""

import json
from pathlib import Path
import traceback

import ida_auto
import ida_funcs
import ida_hexrays
import ida_kernwin
import ida_nalt
import ida_pro
import idautils
import idc

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "analysis/decompiled"
OUTPUT.mkdir(exist_ok=True)

try:
    ida_auto.auto_wait()
    if not ida_hexrays.init_hexrays_plugin():
        raise RuntimeError("No Hex-Rays decompiler for the selected processor")
    request = json.loads((ROOT / "analysis/ida-export-request.json").read_text())
    results = []
    seen = set()
    for address in request["addresses"]:
        address = int(address, 0)
        function = ida_funcs.get_func(address)
        if function is None:
            results.append({"address": hex(address), "error": "No defined function"})
            continue
        address = function.start_ea
        if address in seen:
            continue
        seen.add(address)
        try:
            code = str(ida_hexrays.decompile(address))
            path = OUTPUT / (f"sub_{address:X}.c")
            path.write_text(code, encoding="utf-8")
            results.append({"address": hex(address), "end": hex(function.end_ea), "name": idc.get_func_name(address), "output": path.relative_to(ROOT).as_posix(), "characters": len(code), "callers": [{"address": hex(ref.frm), "function": idc.get_func_name(ref.frm)} for ref in idautils.XrefsTo(address, 0)]})
        except Exception as error:
            results.append({"address": hex(address), "error": str(error)})
    (ROOT / "analysis/ida-export-result.json").write_text(json.dumps({"input": ida_nalt.get_input_file_path(), "ida_version": ida_kernwin.get_kernel_version(), "results": results}, indent=2), encoding="utf-8")
except Exception:
    (ROOT / "analysis/ida-export-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
finally:
    ida_pro.qexit(0)
