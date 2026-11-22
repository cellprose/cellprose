# Freeze manifest

`benchmark.json` lists the SHA-256 of every file the benchmark run depends on (docs/PROTOCOL.md section 9), plus one
digest over them: the SHA-256 of the lines `<path> <sha256>\n` sorted by path. The digest is posted publicly with a
date before the run. It depends only on paths and contents, so it can be checked from any copy of the repository plus
the two datasets. This README is not part of the manifest.

Check: `python3 benchmarks/freeze.py` rewrites `benchmark.json`; the printed digest must match the posted one. Any edit
to a listed file changes the digest, so after the posting such an edit is a deviation and goes in the write-up.

`pilot2.json` belongs to development data (`external/realworld3/`) and is not part of the benchmark.
