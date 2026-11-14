"""Analyze the research ELF in an isolated IDA process; export targeted evidence."""

import json
from pathlib import Path
import traceback

import ida_auto
import ida_funcs
import ida_kernwin
import ida_loader
import ida_nalt
import ida_pro
import ida_xref
import idautils
import idc

ROOT = Path(__file__).resolve().parents[1]


try:
    ida_auto.auto_wait()
    requested = json.loads((ROOT / "analysis/elf-roster-strings.json").read_text())
    output = []
    for item in requested:
        address = int(item["address"], 16)
        if not (0x547000 <= address < 0x550000):
            continue
        refs = []
        for ref in idautils.XrefsTo(address, 0):
            function = ida_funcs.get_func(ref.frm)
            refs.append({"from": hex(ref.frm), "type": ref.type, "function": hex(function.start_ea) if function else None, "function_name": idc.get_func_name(ref.frm) if function else None})
        output.append({**item, "xrefs": refs})
    report = {"input": ida_nalt.get_input_file_path(), "ida_version": ida_kernwin.get_kernel_version(), "functions": len(list(idautils.Functions())), "strings": output}
    (ROOT / "analysis/ida-roster-triage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    ida_loader.save_database(str(ROOT / "analysis/EBOOT.i64"), 0)
except Exception:
    (ROOT / "analysis/ida-roster-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
finally:
    ida_pro.qexit(0)
