"""Search the research ELF with pyelftools and Capstone; retain address evidence."""

import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_PPC, CS_MODE_64, CS_MODE_BIG_ENDIAN
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / "analysis/EBOOT.elf"
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        segments = [(segment.header.p_vaddr, segment.header.p_offset, segment.data()) for segment in elf.iter_segments() if segment.header.p_type == "PT_LOAD"]
        code_sections = [(section.header.sh_addr, section.data()) for section in elf.iter_sections() if section.header.sh_flags & 4 and section.header.sh_size > 100000]
        entry = elf.header.e_entry
        metadata = {"elf_class": elf.elfclass, "little_endian": elf.little_endian, "machine": elf.header.e_machine, "entry_descriptor": hex(entry)}
    def read(address, size):
        for virtual, _, data in segments:
            if virtual <= address and address + size <= virtual + len(data):
                return data[address - virtual:address - virtual + size]
        raise ValueError(f"Unmapped ELF address: {address:#x}")
    # This ELF64 PS3 executable uses 32-bit pointers and eight-byte PPU OPDs.
    entry_code, toc = struct.unpack(">II", read(entry, 8))
    metadata.update({"entry_code": hex(entry_code), "toc": hex(toc), "pointer_width": 4})
    strings = []
    for virtual, offset, data in segments:
        for match in re.finditer(rb"[ -~]{4,}", data):
            value = match.group().decode("ascii")
            if re.search(r"(?i)(^e(?:nao|na2|nze|nza|nte|all|kyr|ter|tes|ms\d+|ko\d+|sc\d+)$|Unit/|Char|Chara|Select|UnitResource|UNIT_|CSVB|CAO[12]|Player|Nirvash|Secret|Mons)", value):
                strings.append({"address": hex(virtual + match.start()), "file_offset": offset + match.start(), "text": value})
    targets = {}
    for item in strings:
        address = int(item["address"], 16)
        if not 0x547000 <= address < 0x54F000:
            continue
        needle = struct.pack(">I", address)
        for virtual, _, data in segments:
            for match in re.finditer(re.escape(needle), data):
                slot = virtual + match.start()
                if slot % 4 == 0 and -32768 <= slot - toc <= 32767:
                    targets[slot] = {"toc_slot": hex(slot), "target": item}
    decoder = Cs(CS_ARCH_PPC, CS_MODE_64 | CS_MODE_BIG_ENDIAN)
    decoder.skipdata = True
    references = []
    for virtual, code in code_sections:
        for address, _, mnemonic, operands in decoder.disasm_lite(code, virtual):
            if "(r2)" not in operands:
                continue
            match = re.search(r"(-?(?:0x[0-9a-f]+|\d+))\(r2\)", operands)
            if match:
                slot = toc + int(match.group(1), 0)
                if slot in targets:
                    references.append({"instruction": hex(address), "mnemonic": mnemonic, "operands": operands, **targets[slot]})
    metadata.update({"elf_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "capstone": importlib.metadata.version("capstone"), "pyelftools": importlib.metadata.version("pyelftools")})
    (ROOT / "analysis/elf-metadata.json").write_text(json.dumps(metadata, indent=2))
    (ROOT / "analysis/elf-roster-strings.json").write_text(json.dumps(strings, indent=2))
    (ROOT / "analysis/elf-toc-roster-xrefs.json").write_text(json.dumps({"toc": hex(toc), "pointer_slots": len(targets), "references": references}, indent=2))
    print("ELF_MINING", json.dumps(metadata), "strings", len(strings), "resolved_toc_references", len(references))


if __name__ == "__main__":
    main()
