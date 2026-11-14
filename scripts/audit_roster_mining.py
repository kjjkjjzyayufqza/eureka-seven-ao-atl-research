"""Cross-check every observed unit against parameter, stage and executable evidence."""

from collections import Counter, defaultdict
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

from vendor_integrity import verify_dependencies

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-eboot", type=Path, required=True, help="Original read-only EBOOT.BIN input")
    args = parser.parse_args()
    inventory = load("analysis/data-mining-inventory.json")
    assert inventory["csvb_files"] == 106 and not inventory["csvb_failures"]
    base = "analysis/tables/extracted/nested/root/LevelDesign/ActCommon.cpk.unpacked/"
    units = load(base + "UnitResource.prm.json")["tables"][0]["rows"]
    codes = [row["strings"]["64"] for row in units]
    expected = ["enao", "ena2", "eall", "ekyr", "enze", "ente", "eter", "enza", "etes", "ems2", "ems1", "eko1", "eko2", "eko3", "eko4", "esc1", "esc2", "esc3"]
    assert codes == expected
    secondary_tables = {}
    for name in ("BulletParam", "ForceParam", "FrameEvent", "NodeParam", "ThinkParam"):
        tables = load(base + name + ".prm.json")["tables"]
        assert len(tables) == len(codes), name
        secondary_tables[name] = [{"unit_id": index, "code": codes[index], "table_name": table["name"], "rows": table["row_count"]} for index, table in enumerate(tables)]
    assert set(inventory["unit_code_reference_counts"]) == set(expected)
    stage_rows = load(base + "StageResource.prm.json")["tables"][0]["rows"]
    assert len(stage_rows) == 44
    stage_uses = defaultdict(list)
    stages = []
    for row in stage_rows:
        slots = []
        for column in range(2, 16, 2):
            unit_id = row["raw"][column]
            if unit_id == 0xFFFF:
                continue
            assert 0 <= unit_id < len(codes)
            slot = {"column": column, "unit_id": unit_id, "code": codes[unit_id], "companion_flag": row["raw"][column + 1]}
            slots.append(slot)
            stage_uses[unit_id].append({"stage": row["index"], "script": row["strings"]["16"], "column": column})
        stages.append({"index": row["index"], "script": row["strings"]["16"], "slots": slots})
    assert set(stage_uses) == set(range(18)) - {1}
    assert stage_rows[23]["raw"][8] == 5  # Single Mission 6: theEND
    assert stage_rows[25]["raw"][8] == 8  # Single Mission 8: Devilfish S
    assert all(stage_rows[index]["raw"][8] == 17 for index in (2, 5, 8, 28))
    assets = load("manifests/playable-assets.json")
    unit_assets = {Path(item["glb"]).parts[3]: item for item in assets if item["kind"] == "model" and "/Unit/" in item["glb"]}
    assert len(unit_assets) == 32
    main_archives = {row["strings"]["65"] for row in units}
    assert len(main_archives) == 16
    main_codes = {Path(name).stem for name in main_archives}
    assert main_codes <= set(unit_assets)
    references = set()
    for file in inventory["files"]:
        data = load(file["output"])
        for table in data["tables"]:
            for row in table["rows"]:
                references.update(value for value in row.get("strings", {}).values() if value.startswith("Unit/"))
    strings = load("analysis/elf-roster-strings.json")
    references.update(item["text"] for item in strings if item["text"].startswith("Unit/"))
    unreferenced_models = [name for name in unit_assets if "Unit/" + name + ".cpk" not in references]
    assert unreferenced_models == ["ems1_gun", "enze_knife"]
    nav = load("analysis/ida/function-0x202538.json")["result"]["structuredContent"]["code"]
    toggle = (ROOT / "analysis/decompiled/sub_1F4058.c").read_text()
    commit = load("analysis/ida/function-0x202dd0.json")["result"]["structuredContent"]["code"]
    assert "(unsigned int)v17 <= 7" in nav and "case 6:" in nav and "case 4:" in nav
    assert "*(_DWORD *)(a1 + 280) = 1" in toggle and "*(_DWORD *)(a1 + 280) = v5" in toggle
    assert "sub_1D4BA8" in toggle and "a1[68] = a1[70]" in commit
    elf_metadata = load("analysis/elf-metadata.json")
    source = args.source_eboot.resolve()
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert original_hash == hashlib.sha256((ROOT / "analysis/EBOOT.BIN").read_bytes()).hexdigest()
    revision = verify_dependencies()["csvb"]
    assert revision == "d1e54c7b41b1165970f841c3de3fd7d86cc93bdc"
    missing = sorted(path for path in references if not (ROOT / "extracted/root" / path).is_file())
    result = {
        "status": "passed", "source_eboot_sha256": original_hash, "source_eboot_unchanged": True,
        "elf": elf_metadata, "csvb_parser_commit": revision,
        "extracted_entries_examined": inventory["extracted_paths_examined"], "csvb_files_parsed": 106,
        "unit_definitions": 18, "player_configurations": 8, "named_player_types_after_ao_variant_merge": 7,
        "non_player_definitions": 10, "unique_unit_body_archives": 16, "unit_model_resources_including_weapons": 32,
        "stage_rows": 44, "stage_unit_ids": sorted(stage_uses), "not_preset_in_stage_rows": [1],
        "non_player_definitions_without_stage_use": [index for index in range(8, 18) if index not in stage_uses],
        "unreferenced_by_typed_tables_or_named_elf_paths": unreferenced_models, "missing_referenced_paths": missing,
        "secondary_tables": secondary_tables, "stages": stages,
        "units": [{"id": index, "code": code, "main_archive": units[index]["strings"]["65"], "player_configuration": index < 8, "stage_uses": stage_uses[index]} for index, code in enumerate(codes)],
        "important_code": {"selector_navigation": "0x202538", "ao_variant_toggle": "0x1F4058", "primary_selection_commit": "0x202DD0", "ally_selection_commit": "0x202A30", "unlock_flag_reader": "0x1D4BA8"},
        "scope_limit": "Static delivered-build coverage; no runtime unlock or procedural-spawn trace, and no proof about absent DLC/builds.",
    }
    (ROOT / "analysis/roster-mining-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("ROSTER_MINING_AUDIT_PASSED", json.dumps({key: value for key, value in result.items() if key not in ("secondary_tables", "stages", "units")}, indent=2))


if __name__ == "__main__":
    main()
