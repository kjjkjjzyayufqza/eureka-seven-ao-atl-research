# Pinned Source Snapshots

Only the source modules used by this research and their original license files are included. These directories are not nested Git repositories. Exact commits, source URLs, authors, licenses and SHA-256 values are recorded in `dependencies.lock.json` at the repository root.

| Dependency | Author | Included source | License |
| --- | --- | --- | --- |
| ed8pkg2glb | Julian Uy (`uyjulian`) | `ed8pkg2glb/src/ed8pkg2glb.py` | MIT |
| CSVB parser | June; `kimjh-eclipse` repository | `srw-og-infinite-battle-korean/tools/csvb.py` | Apache-2.0 |

The snapshots retain their original bytes. Title-specific behavior belongs in local adapters under `scripts/`. The complete upstream checkouts used during research were moved to a separate local cache; they are not part of this repository.

Other tools, including PyCriCodecs, Blender, IDA and scetool, are installed separately. No dependency binaries, game resources or decryption keys are vendored. See [tools and attribution](../docs/tools-and-attribution.md).
