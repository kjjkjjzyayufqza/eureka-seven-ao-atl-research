"""Read-only CSVB/resource mining using kimjh-eclipse's existing table parser."""

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "third_party/srw-og-infinite-battle-korean/tools/csvb.py"
spec = importlib.util.spec_from_file_location("existing_csvb", UPSTREAM)
csvb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csvb)


def parse_table(path):
    data, count, column_start, string_start, string_end, extra, tables = csvb.parse(str(path))
    output = []
    for table in tables:
        rows = []
        for row_index in range(table.nrows):
            cursor = table.rowsoff + row_index * table.rowsize
            raw = []
            texts = {}
            floats = {}
            for column, kind in enumerate(table.types):
                size = csvb.col_size(kind)
                value = int.from_bytes(data[cursor:cursor + size], "big")
                raw.append(value)
                if kind == 3:
                    floats[str(column)] = struct.unpack_from(">f", data, cursor)[0]
                # This game's resource references use 7/9 in addition to the
                # translation tool's 0x1B text type. Preserve the raw values too.
                if kind in (7, 9, 0x1B) and value < string_end - string_start:
                    try:
                        texts[str(column)] = csvb.read_str(data, string_start, value)
                    except (UnicodeDecodeError, ValueError):
                        pass
                cursor += size
            row = {"index": row_index, "offset": table.rowsoff + row_index * table.rowsize, "raw": raw}
            if texts:
                row["strings"] = texts
            if floats:
                row["floats"] = floats
            if table.rowsize == 8 and table.types == (2, 2):
                argument_offset, opcode = raw
                next_offset = struct.unpack_from(">I", data, table.rowsoff + (row_index + 1) * 8)[0] if row_index + 1 < table.nrows else len(data) - extra
                if 0 <= argument_offset <= next_offset <= len(data) - extra and (next_offset - argument_offset) % 4 == 0:
                    row["argument_words"] = list(struct.unpack_from(">" + "I" * ((next_offset - argument_offset) // 4), data, extra + argument_offset))
                row["opcode"] = opcode
                row["argument_offset"] = argument_offset
            rows.append(row)
        output.append({"name": table.name, "row_count": table.nrows, "row_size": table.rowsize, "row_start": table.rowsoff, "column_types": list(table.types), "rows": rows})
    return {"source": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(data).hexdigest(), "table_count": count, "string_pool": [string_start, string_end], "extra_start": extra, "extra_size": len(data) - extra, "tables": output}


def main():
    archives = json.loads((ROOT / "manifests/archives.json").read_text())
    entries = [entry for archive in archives for entry in archive["entries"]]
    paths = sorted({ROOT / entry["output"] for entry in entries})
    summaries = []
    failures = []
    body_names = set()
    name_hits = defaultdict(list)
    for path in paths:
        with path.open("rb") as stream:
            magic = stream.read(8)
        if magic == b"CSVBv4.3":
            try:
                parsed = parse_table(path)
                target = ROOT / "analysis/tables" / (path.relative_to(ROOT).as_posix() + ".json")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(parsed, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
                summaries.append({"source": parsed["source"], "output": target.relative_to(ROOT).as_posix(), "tables": [{"name": table["name"], "rows": table["row_count"]} for table in parsed["tables"]], "extra_size": parsed["extra_size"]})
                for table in parsed["tables"]:
                    for row in table["rows"]:
                        for value in row.get("strings", {}).values():
                            for match in re.finditer(r"(?<![A-Za-z0-9])(e(?:nao|na\d+|nz[a-z\d]+|nte|all|kyr|te[a-z\d]+|ms\d+|ko\d+|sc\d+))(?![A-Za-z0-9])", value):
                                name_hits[match.group(1)].append({"source": parsed["source"], "table": table["name"], "row": row["index"], "value": value})
            except Exception as error:
                failures.append({"source": path.relative_to(ROOT).as_posix(), "error": repr(error)})
        if path.name.lower().endswith("_model.dae.gcm"):
            body_names.add(path.name)
    report = {"extracted_paths_examined": len(paths), "csvb_files": len(summaries), "csvb_failures": failures, "files": summaries, "unit_code_reference_counts": {key: len(value) for key, value in sorted(name_hits.items())}, "unit_code_references": dict(name_hits), "all_model_cluster_basenames": sorted(body_names)}
    (ROOT / "analysis/data-mining-inventory.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in ("files", "unit_code_references", "all_model_cluster_basenames")}, indent=2))


if __name__ == "__main__":
    main()
